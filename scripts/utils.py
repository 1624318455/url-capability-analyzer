import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import re
import sys

def fetch_webpage_info(url: str, use_headless_browser: bool = False) -> Dict[str, Any]:
    """Fetch and parse a webpage, extract MCP/Skill metadata."""
    
    # Try headless browser first for dynamic content if requested
    if use_headless_browser:
        content = _fetch_with_browser(url)
        if content:
            return _parse_html_content(content, url)
    
    # Fall back to requests
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        html_content = resp.text
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {url}. Error: {str(e)}")
    
    return _parse_html_content(html_content, url)

def _parse_html_content(html_content: str, url: str) -> Dict[str, Any]:
    """Parse HTML content and extract metadata."""
    
    # Handle encoding issues
    html_content = _fix_encoding(html_content)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    # Get text content
    text = soup.get_text(separator=' ', strip=True)
    
    # Try to get title
    title = None
    if soup.title:
        title_raw = soup.title.string
        if title_raw:
            title_raw = title_raw.strip()
            # Try to fix encoding
            title = _fix_encoding(title_raw)
    
    if not title:
        # Try to extract from h1, h2, or meta tags
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            if tag.string and len(tag.string.strip()) > 3:
                title = _fix_encoding(tag.string.strip())
                break
    
    if not title:
        title = url.split('/')[-1] if url.split('/')[-1] else "Unknown"
    
    # Detect type
    type_ = _detect_type(url, text, soup)
    
    # Try to extract more meaningful description
    description = _extract_description(soup, text)
    
    # Extract GitHub URL if present
    github_url = _extract_github_url(soup, html_content)
    
    # Extract MCP-specific metadata
    mcp_metadata = _extract_mcp_metadata(soup, text, html_content, url)
    
    return {
        "name": title,
        "type": type_,
        "url": url,
        "description": description,
        "full_text": text[:5000],  # limit length
        "github_url": github_url,
        "tools": mcp_metadata['tools'],
        "install_methods": mcp_metadata['install_methods'],
        "author": mcp_metadata['author'],
        "language": mcp_metadata['language'],
        "tags": mcp_metadata['tags']
    }

def _fix_encoding(text: str) -> str:
    """Fix common encoding issues in text."""
    if not text:
        return text
    
    # Check if the text looks like it has encoding issues (contains replacement characters or mojibake)
    # If text contains Chinese characters that look corrupted, try to fix
    try:
        # Try to detect if text is actually valid UTF-8 that got double-encoded
        # by checking if it contains the UTF-8 BOM or has valid UTF-8 sequences
        text_bytes = text.encode('utf-8', errors='replace')
        # Try to decode as different encodings and re-encode as UTF-8
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
            try:
                # If this encoding works and produces valid UTF-8, use it
                decoded = text_bytes.decode(encoding, errors='replace')
                if _is_valid_text(decoded):
                    return decoded
            except:
                continue
    except:
        pass
    
    return text

def _is_valid_text(text: str) -> bool:
    """Check if text appears to be valid (not garbled)."""
    if not text:
        return False
    
    # Count valid-looking characters
    valid_chars = 0
    for char in text:
        if char.isprintable() or char.isspace():
            valid_chars += 1
    
    return valid_chars > len(text) * 0.9

def _detect_type(url: str, text: str, soup: BeautifulSoup) -> str:
    """Detect if the target is an MCP or Skill."""
    text_lower = text.lower()
    url_lower = url.lower()
    
    # Strong indicators for MCP
    mcp_indicators = [
        'model context protocol',
        'mcp server',
        'mcp-server-',
        'mcp_',
        '@modelcontextprotocol',
        'mcp protocol',
        'stdin/stdout',
        'json-rpc'
    ]
    
    # Check URL
    if 'mcp' in url_lower:
        return "mcp"
    
    # Check text content
    for indicator in mcp_indicators:
        if indicator in text_lower:
            return "mcp"
    
    # Check for npm package pattern (common for MCP servers)
    if re.search(r'npm\s+(install|install|-g)', text_lower):
        return "mcp"
    
    # Check for common MCP installation patterns
    if re.search(r'(uvx|pip install|npx\s+@)', text_lower):
        return "mcp"
    
    return "skill"

def _extract_description(soup: BeautifulSoup, text: str) -> str:
    """Extract a meaningful description from the page."""
    
    # Try meta description first
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return _fix_encoding(meta_desc['content'])[:2000]
    
    # Try Open Graph description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        return _fix_encoding(og_desc['content'])[:2000]
    
    # Try to find substantial paragraphs
    paragraphs = []
    for p in soup.find_all('p'):
        if p.string and len(p.string.strip()) > 50:
            paragraphs.append(_fix_encoding(p.string.strip()))
    
    if paragraphs:
        # Return all substantial paragraphs, concatenated
        return '\n\n'.join(paragraphs[:5])[:2000]  # First 5 substantial paragraphs
    
    # Try article or main content
    for tag_name in ['article', 'main', 'div']:
        for tag in soup.find_all(tag_name):
            content = tag.get_text(separator=' ', strip=True)
            if len(content) > 100 and not _is_navigation_content(content):
                # Return substantial content
                return _fix_encoding(content)[:2000]
    
    # Fallback: use cleaned text
    cleaned_text = ' '.join(text.split())[:2000]
    return _fix_encoding(cleaned_text)

def _is_navigation_content(text: str) -> bool:
    """Check if text looks like navigation or boilerplate content."""
    nav_keywords = [
        'menu', 'navigation', 'home', 'login', 'sign up', 'register',
        'copyright', 'privacy policy', 'terms of', 'contact',
        'about us', 'follow us', 'social media'
    ]
    text_lower = text.lower()
    for keyword in nav_keywords:
        if keyword in text_lower:
            return True
    return False

def _extract_github_url(soup: BeautifulSoup, html_content: str) -> Optional[str]:
    """Extract GitHub URL from the page."""
    
    # Look for GitHub links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'github.com' in href and not href.endswith('.git'):
            return href
    
    # Look for GitHub in text
    github_match = re.search(r'https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+', html_content)
    if github_match:
        return github_match.group(0)
    
    return None

def _extract_mcp_metadata(soup: BeautifulSoup, text: str, html_content: str, url: str = "") -> Dict[str, Any]:
    """Extract MCP-specific metadata like tools, installation methods, etc."""
    metadata = {
        'tools': [],
        'install_methods': [],
        'author': None,
        'language': None,
        'tags': [],
        'package_name': None
    }
    
    text_lower = text.lower()
    html_lower = html_content.lower()
    url_lower = url.lower()
    
    # Define false positives for tool filtering
    false_positives = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
        'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        'just', 'also', 'now', 'url', 'https', 'http', 'html', 'json', 'xml',
        'api', 'com', 'org', 'git', 'src', 'raw', 'text', 'content', 'page',
        'none', 'any', 'all', 'max', 'min', 'default', 'type', 'name', 'id',
        'value', 'data', 'key', 'link', 'img', 'div', 'span', 'p', 'ul', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'button', 'input', 'form', 'table',
        'row', 'col', 'cell', 'header', 'footer', 'body', 'head', 'title', 'meta',
        'style', 'script', 'class', 'function', 'return', 'string', 'number',
        'boolean', 'null', 'undefined', 'object', 'array', 'true', 'false',
        'world', 'home', 'mcp', 'server', 'servers', 'fetching', 'about',
        'login', 'sign', 'register', 'menu', 'nav', 'navigation', 'bot', 'tree',
        'list', 'item', 'label', 'tag', 'tags', 'icon', 'image', 'avatar',
        # Common markdown/Section headers that are not tools
        'main', 'overview', 'introduction', 'installation', 'configuration', 
        'usage', 'example', 'examples', 'available', 'tools', 'prompt', 'prompts',
        'optionally', 'alternatively', 'recommended', 'requirements', 'license',
        'contributing', 'security', 'warning', 'caution', 'note', 'tip',
        'introduction', 'features', 'quickstart', 'getting', 'started'
    }
    
    # Extract MCP name from URL path (for directory sites like mcpworld.com)
    if url:
        url_mcp_match = re.search(r'/servers/([a-z][a-z0-9_-]+)(?:/|$)', url_lower)
        if url_mcp_match:
            mcp_name = url_mcp_match.group(1)
            if mcp_name not in false_positives and len(mcp_name) > 2:
                metadata['tools'].append(mcp_name)
    
    # Extract package name from URL (e.g., mcp-server-fetch from github.com/modelcontextprotocol/servers/tree/main/src/fetch)
    package_patterns = [
        r'mcp[_-]server[_-]([a-z][a-z0-9_-]+)',  # mcp-server-fetch
        r'@([a-z0-9_-]+/[a-z][a-z0-9_-]+)',       # @scope/package
        r'pip install ([a-z0-9_-]+)',              # pip install mcp-server-fetch
        r'npm install ([a-z0-9_-@]+)',              # npm install @scope/package
    ]
    for pattern in package_patterns:
        match = re.search(pattern, url_lower + html_lower)
        if match:
            pkg = match.group(1)
            if not any(fp in pkg.lower() for fp in false_positives):
                metadata['package_name'] = pkg
                break
    
    # Extract tools from markdown code block patterns: `tool_name` or "tool_name"
    code_tool_pattern = r'`([a-z][a-z0-9_-]{2,30})`'
    code_tools = re.findall(code_tool_pattern, text)
    for tool in code_tools:
        if tool.lower() not in false_positives:
            metadata['tools'].append(tool)
    
    # Extract tools from **bold** patterns (MCP README style: **fetch** - description)
    bold_tool_pattern = r'\*\*([a-z][a-z0-9_-]{2,30})\*\*\s*[-–—]'
    bold_tools = re.findall(bold_tool_pattern, text)
    for tool in bold_tools:
        if tool.lower() not in false_positives:
            metadata['tools'].append(tool)
    
    # Extract tools from inline code in JSON/config (tool: "name")
    json_tool_pattern = r'tool["\s:]+["]([a-z][a-z0-9_-]{2,30})["]'
    json_tools = re.findall(json_tool_pattern, html_content, re.IGNORECASE)
    for tool in json_tools:
        if tool.lower() not in false_positives:
            metadata['tools'].append(tool)
    
    # Filter and deduplicate tools
    common_mcp_tools = {'fetch', 'search', 'scrape', 'transform', 'convert', 'analyze', 'query', 'get', 'post', 'list', 'create', 'update', 'delete', 'edit', 'read', 'write'}
    
    def is_valid_tool(tool):
        tool_lower = tool.lower()
        if tool_lower in common_mcp_tools:
            return True
        if tool_lower in false_positives:
            return False
        if len(tool) <= 2 or tool.isdigit():
            return False
        if all(c.isupper() for c in tool) and len(tool) > 3:
            return False
        if any(fp in tool_lower for fp in ['using', 'install', 'option', 'config', 'setting']):
            return False
        return True
    
    metadata['tools'] = [tool for tool in metadata['tools'] if is_valid_tool(tool)]
    # Remove duplicates while preserving order
    seen = set()
    filtered_tools = []
    for tool in metadata['tools']:
        tool_lower = tool.lower()
        if tool_lower not in seen:
            seen.add(tool_lower)
            filtered_tools.append(tool)
    metadata['tools'] = filtered_tools[:10]
    
    # Extract installation methods
    install_methods = []
    if 'uvx' in html_lower or ' uv run' in html_lower:
        install_methods.append('uvx')
    if 'pip install' in html_lower:
        install_methods.append('pip')
    if 'npm install' in html_lower or 'npx' in html_lower:
        install_methods.append('npm')
    if 'docker' in html_lower:
        install_methods.append('docker')
    if '手动' in text or 'manual' in html_lower:
        install_methods.append('manual')
    
    metadata['install_methods'] = list(set(install_methods))
    
    # Extract author - try multiple patterns
    author_patterns = [
        r'github\.com/([a-zA-Z0-9_-]+)/',  # From GitHub URL
        r'By\s+[\*\*]?([A-Za-z0-9_-]+)[\*\*]?',  # By username or **username**
        r'作者[:\s]+([^\n]+)',
        r'作者：\s*([^\n]+)',
        r'maintainer[s]?[:\s]+([^\n]+)',
    ]
    for pattern in author_patterns:
        match = re.search(pattern, text + ' ' + url, re.IGNORECASE)
        if match:
            author = match.group(1).strip()
            # Clean up author name
            author = re.sub(r'[\*`]', '', author)
            if author and len(author) < 50 and author.lower() not in false_positives:
                metadata['author'] = author
                break
    
    # Extract language
    language_patterns = [
        r'\b(JavaScript|TypeScript|Python|Rust|Go|Java|C\+\+|Ruby)\b',
        r'语言[:\s]+([^\n]+)',
    ]
    for pattern in language_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['language'] = match.group(1).strip()
            break
    
    # Extract tags (from the website's tag section)
    tag_keywords = ['网页抓取', 'HTML转换', '模型上下文协议', '内容处理', '本地部署', 'A-优质']
    found_tags = []
    for tag in tag_keywords:
        if tag in text:
            found_tags.append(tag)
    
    metadata['tags'] = list(set(found_tags))[:10]
    
    return metadata

def _fetch_with_browser(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch page content using a headless browser (Playwright)."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
            
            # Wait a bit more for dynamic content
            page.wait_for_timeout(2000)
            
            content = page.content()
            browser.close()
            return content
    except ImportError:
        print("Warning: Playwright not installed. Run: pip install playwright && playwright install chromium", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Warning: Browser fetch failed: {e}", file=sys.stderr)
        return None
