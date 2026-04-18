import os
import json
from typing import Optional, Dict, Any

from ..image_service import get_image_service

class WebMixin:

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
