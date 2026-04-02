import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

def fetch_webpage_info(url: str) -> Dict[str, Any]:
    """Fetch and parse a webpage, extract MCP/Skill metadata."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=' ', strip=True)[:3000]  # limit length

    # Try to guess name from title
    title = soup.title.string.strip() if soup.title else url.split('/')[-1]
    # Simple type detection
    type_ = "mcp" if "mcp" in url.lower() or "model context protocol" in text.lower() else "skill"

    return {
        "name": title,
        "type": type_,
        "url": url,
        "description": text[:1000],
        "full_text": text
    }