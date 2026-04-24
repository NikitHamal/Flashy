import os
import json
from typing import Optional, Dict, Any

class WebMixin:

    async def web_browse(self, url: str, max_length: int = 50000) -> str:
        """
        Fetch and summarize a web page.
        
        Args:
            url: URL to fetch
            max_length: Maximum characters to return
        """
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Remove script/style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            text = soup.get_text(separator="\n", strip=True)
            lines = [line for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)
            
            if len(text) > max_length:
                text = text[:max_length] + f"\n\n[Content truncated at {max_length} chars]"
            
            return f"Fetched {url}:\n\n{text}"
        except Exception as e:
            return f"Error fetching {url}: {str(e)}"
