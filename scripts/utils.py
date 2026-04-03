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
    mcp_metadata = _extract_mcp_metadata(soup, text, html_content)
    
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

def _extract_mcp_metadata(soup: BeautifulSoup, text: str, html_content: str) -> Dict[str, Any]:
    """Extract MCP-specific metadata like tools, installation methods, etc."""
    metadata = {
        'tools': [],
        'install_methods': [],
        'author': None,
        'language': None,
        'tags': []
    }
    
    text_lower = text.lower()
    html_lower = html_content.lower()
    
    # Extract tools (improved patterns for MCP documentation)
    # Pattern 1: **fetch** - description format (common in MCP READMEs)
    tool_pattern1 = r'\*\*([a-zA-Z_][a-zA-Z0-9_-]*)\*\*\s*[-–—]\s*([^\n]+)'
    matches1 = re.findall(tool_pattern1, text, re.IGNORECASE)
    for tool_name, tool_desc in matches1:
        if len(tool_name) < 50 and len(tool_desc) > 10:
            metadata['tools'].append(tool_name.strip())
    
    # Pattern 2: "tool-name - description" or "tool-name : description"
    tool_pattern2 = r'([a-zA-Z_][a-zA-Z0-9_-]*)\s*[:\-–—]\s*([^\n]+)'
    matches2 = re.findall(tool_pattern2, text)
    for tool_name, tool_desc in matches2:
        if len(tool_name) < 50 and len(tool_desc) > 10 and tool_name.lower() not in ['url', 'max_length', 'start_index', 'raw']:
            metadata['tools'].append(tool_name.strip())
    
    # Pattern 3: Look for "Available tools" or "可用工具" section
    if 'available tools' in text_lower or '可用工具' in text_lower:
        # Find lines that mention tool names followed by descriptions
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'available tools' in line.lower() or '可用工具' in line:
                # Check next few lines for tool definitions
                for j in range(i+1, min(i+10, len(lines))):
                    line_content = lines[j].strip()
                    # Look for patterns like "tool - description"
                    if ' - ' in line_content or ' — ' in line_content:
                        parts = line_content.split(' - ')[0].split(' — ')[0]
                        if len(parts) < 50:
                            metadata['tools'].append(parts.strip())
    
    # Pattern 4: Look for code blocks with tool definitions
    # Pattern like: ```typescript\n// tool: fetch\n```
    code_tool_pattern = r'[\'"`]([a-z_][a-z0-9_]*)[\'"`]\s*:|tool["\s]+(\w+)'
    code_matches = re.findall(code_tool_pattern, html_content, re.IGNORECASE)
    for match in code_matches:
        tool = match[0] or match[1]
        if len(tool) > 2 and len(tool) < 50:
            metadata['tools'].append(tool)
    
    # Pattern 5: If this is a directory listing (like mcpworld.com), extract the MCP name as primary tool
    # and extract from description
    page_title = soup.title.string if soup.title and soup.title.string else ""
    if 'mcpworld' in html_lower or 'mcp' in page_title.lower():
        # Try to extract MCP name from URL path
        mcp_name_match = re.search(r'/servers/([a-z0-9_-]+)', html_lower)
        if mcp_name_match:
            mcp_name = mcp_name_match.group(1)
            # Add the MCP name as a tool (it's the primary capability)
            if len(mcp_name) > 2:
                metadata['tools'].append(mcp_name)
        
        # Extract common MCP tool names that might appear in descriptions
        common_mcp_tool_patterns = [
            r'(?:tool|功能)[:\s]+([a-z][a-z0-9_]+)',
            r'([a-z]+)\s+(?:tool|功能)',
        ]
        for pattern in common_mcp_tool_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if len(match) > 2 and match not in false_positives:
                    metadata['tools'].append(match)
    
    # Remove duplicates, clean, and filter out false positives
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
        'list', 'item', 'label', 'tag', 'tags', 'icon', 'image', 'avatar'
    }
    # Filter out single letters, common words, and very short strings
    # But always keep common MCP tool names
    common_mcp_tools = {'fetch', 'search', 'scrape', 'transform', 'convert', 'analyze', 'query', 'get', 'post'}
    
    def is_valid_tool(tool):
        tool_lower = tool.lower()
        # Always keep if it's a common MCP tool
        if tool_lower in common_mcp_tools:
            return True
        # Filter out false positives
        if tool_lower in false_positives:
            return False
        if len(tool) <= 2:
            return False
        if tool.isdigit():
            return False
        if all(c.isupper() for c in tool) and len(tool) > 3:
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
    
    # Extract author
    author_patterns = [
        r'By\s+([A-Za-z0-9_-]+)',
        r'作者[:\s]+([^\n]+)',
        r'作者：\s*([^\n]+)',
    ]
    for pattern in author_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['author'] = match.group(1).strip()
            break
    
    # Extract language
    language_patterns = [
        r'\b(JavaScript|TypeScript|Python|Rust|Go|Java|C\+\+)\b',
        r'语言[:\s]+([^\n]+)',
    ]
    for pattern in language_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata['language'] = match.group(1).strip()
            break
    
    # Extract tags (from the website's tag section)
    tag_keywords = ['网页抓取', 'HTML转换', '模型上下文协议', '内容处理', '本地部署', '网页抓取', 'A-优质']
    found_tags = []
    for tag in tag_keywords:
        if tag in text:
            found_tags.append(tag)
    
    # Also look for English tags
    english_tag_pattern = r'([A-Za-z]+(?:[-][A-Za-z]+)*)\s*(?:\d+\s*)?(?:推荐|优质|必备)'
    matches = re.findall(english_tag_pattern, text)
    found_tags.extend(matches)
    
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
