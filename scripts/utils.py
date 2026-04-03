import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import re

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
    
    return {
        "name": title,
        "type": type_,
        "url": url,
        "description": description,
        "full_text": text[:5000],  # limit length
        "github_url": github_url
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
        return _fix_encoding(meta_desc['content'])[:500]
    
    # Try Open Graph description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        return _fix_encoding(og_desc['content'])[:500]
    
    # Try to find the first substantial paragraph
    for p in soup.find_all('p'):
        if p.string and len(p.string.strip()) > 50:
            return _fix_encoding(p.string.strip())[:500]
    
    # Try article or main content
    for tag_name in ['article', 'main', 'div']:
        for tag in soup.find_all(tag_name):
            # Skip if it's too short or contains mostly navigation
            content = tag.get_text(separator=' ', strip=True)
            if len(content) > 100 and not _is_navigation_content(content):
                # Return first substantial paragraph-like content
                lines = [l.strip() for l in content.split('.') if len(l.strip()) > 30]
                if lines:
                    return _fix_encoding('. '.join(lines[:2]))[:500]
    
    # Fallback: use cleaned text
    cleaned_text = ' '.join(text.split())[:500]
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
