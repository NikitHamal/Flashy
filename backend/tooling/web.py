import os
import subprocess
import glob
import tempfile
import shutil
import json
import asyncio
from typing import Optional, List, Dict, Any

from ..git_manager import GitManager
from ..websocket_manager import ws_manager
from ..image_service import get_image_service, ImageService

class WebMixin:
    def web_search(self, query: str) -> str:
        """Search the web using DuckDuckGo."""
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            # DuckDuckGo HTML version (simpler to parse)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            resp = session.get(url, timeout=20)
            results = []
            for item in resp.html.find('.result'):
                title_node = item.find('.result__a', first=True)
                snippet_node = item.find('.result__snippet', first=True)
                if title_node and snippet_node:
                    results.append(f"Title: {title_node.text}\nLink: {title_node.attrs['href']}\nSnippet: {snippet_node.text}\n")
            
            if results:
                return "\n".join(results[:8])
            return "No web results found."
        except Exception as e:
            return f"Error during web search: {str(e)}"
        finally:
            try:
                if 'session' in locals():
                    session.close()
            except Exception:
                pass

    def web_browse(self, url: str) -> str:
        """Browse a website and return its text content."""
        try:
            from requests_html import HTMLSession
            session = HTMLSession()
            resp = session.get(url, timeout=20)
            # Basic text extraction
            text = resp.html.text
            # Clean up excessive whitespace
            import re
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return f"Content of {url}:\n\n{text[:10000]}..." # Cap at 10k chars
        except Exception as e:
            return f"Error browsing {url}: {str(e)}"
        finally:
            try:
                if 'session' in locals():
                    session.close()
            except Exception:
                pass

    def generate_image(self, prompt: str, save_to_project: bool = False, filename: str = None) -> str:
        """
        Request image generation from AI.
        
        This tool signals to the agent loop that an image should be generated.
        The actual generation happens via Gemini's internal image generation.
        
        Args:
            prompt: Description of the image to generate
            save_to_project: Whether to save the image to assets/images
            filename: Optional custom filename
        """
        # Store pending save request if needed
        if save_to_project:
            self._pending_image_save = {
                "save": True,
                "filename": filename,
                "prompt": prompt
            }
        
        # Return a formatted prompt that will trigger Gemini's image generation
        return f"""IMAGE_GENERATION_REQUEST:
Prompt: {prompt}
Save to project: {save_to_project}
Filename: {filename or 'auto'}

Please generate an image matching this description. Use your image generation capabilities to CREATE a new, original image. After generation, the image will appear in the response."""

    async def save_image(self, url: str, filename: str = None, subdir: str = None) -> str:
        """
        Save an image from URL to the project's assets folder.
        
        Args:
            url: Image URL to download and save
            filename: Optional custom filename
            subdir: Optional subdirectory within assets/images
        """
        success, result = await self.image_service.save_image_from_url(
            url, 
            filename, 
            subdir
        )
        
        if success:
            return f"Image saved successfully to: {result}"
        else:
            return f"Error saving image: {result}"

    async def save_generated_images(self, subdir: str = None) -> str:
        """
        Save all recently generated images to the project.
        
        Args:
            subdir: Optional subdirectory within assets/images
        """
        if not self.image_service.generated_images:
            return "No generated images available to save."
        
        saved = []
        errors = []
        
        for i, img in enumerate(self.image_service.generated_images):
            if img.saved:
                saved.append(f"Already saved: {img.local_path}")
                continue
                
            success, result = await self.image_service.save_image_from_url(
                img.url,
                filename=None,
                subdir=subdir
            )
            
            if success:
                img.local_path = result
                img.saved = True
                saved.append(f"Saved: {result}")
            else:
                errors.append(f"Failed: {result}")
        
        output = []
        if saved:
            output.append("Saved images:\\n" + "\\n".join(saved))
        if errors:
            output.append("Errors:\\n" + "\\n".join(errors))
        
        return "\\n\\n".join(output) if output else "No images to save."

    def get_pending_image_save(self) -> Dict[str, Any]:
        """Get and clear pending image save request."""
        pending = self._pending_image_save.copy()
        self._pending_image_save = {}
        return pending
