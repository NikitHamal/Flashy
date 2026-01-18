"""
Image Generation Service Module

This module provides image generation capabilities for the Flashy Coding Agent
using Gemini's built-in image generation features (Nano Banana model).

Features:
- Generate images from natural language prompts
- Save images to workspace for use in projects
- Handle both WebImage and GeneratedImage types
- Proxy images for display in chat
"""

import os
import asyncio
import uuid
import aiohttp
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ImageType(Enum):
    """Type of image returned by Gemini."""
    GENERATED = "generated"  # AI-generated image
    WEB = "web"              # Image fetched from web


@dataclass
class ImageResult:
    """Represents an image result."""
    url: str
    local_path: Optional[str] = None
    image_type: ImageType = ImageType.WEB
    title: Optional[str] = None
    alt: Optional[str] = None
    saved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "local_path": self.local_path,
            "type": self.image_type.value,
            "title": self.title,
            "alt": self.alt,
            "saved": self.saved
        }


class ImageService:
    """
    Service for generating and managing images.
    
    Uses Gemini's internal image generation when available,
    and provides tools for saving images to the workspace.
    """

    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.generated_images: List[ImageResult] = []
        self._image_cache: Dict[str, str] = {}  # URL -> local path

    def set_workspace(self, path: str):
        """Set the workspace path for saving images."""
        if os.path.isdir(path):
            self.workspace_path = os.path.abspath(path)

    def _get_images_dir(self) -> str:
        """Get or create the images directory in workspace."""
        images_dir = os.path.join(self.workspace_path, "assets", "images")
        os.makedirs(images_dir, exist_ok=True)
        return images_dir

    def _generate_filename(self, prefix: str = "image", ext: str = "png") -> str:
        """Generate a unique filename for an image."""
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{unique_id}.{ext}"

    async def save_image_from_url(
        self, 
        url: str, 
        filename: Optional[str] = None,
        subdir: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Download and save an image from URL to workspace.
        
        Args:
            url: Image URL to download
            filename: Optional custom filename
            subdir: Optional subdirectory within assets/images
            
        Returns:
            Tuple of (success, path_or_error)
        """
        try:
            # Create target directory
            images_dir = self._get_images_dir()
            if subdir:
                images_dir = os.path.join(images_dir, subdir)
                os.makedirs(images_dir, exist_ok=True)

            # Generate filename if not provided
            if not filename:
                # Try to extract extension from URL
                ext = "png"
                if "." in url.split("/")[-1]:
                    potential_ext = url.split(".")[-1].split("?")[0].lower()
                    if potential_ext in ["png", "jpg", "jpeg", "gif", "webp", "svg"]:
                        ext = potential_ext
                filename = self._generate_filename("image", ext)

            full_path = os.path.join(images_dir, filename)
            
            # Prepare headers and cookies for authenticated download
            from .config import load_config
            config = load_config()
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Referer": "https://gemini.google.com/",
            }
            
            cookies = {}
            if config.get("Secure_1PSID"):
                cookies["__Secure-1PSID"] = config.get("Secure_1PSID")
            if config.get("Secure_1PSIDTS"):
                cookies["__Secure-1PSIDTS"] = config.get("Secure_1PSIDTS")
            if config.get("Secure_1PSIDCC"):
                cookies["__Secure-1PSIDCC"] = config.get("Secure_1PSIDCC")

            # Download image
            async with aiohttp.ClientSession(cookies=cookies) as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        return False, f"Failed to download: HTTP {response.status}"
                    
                    content = await response.read()
                    
                    with open(full_path, "wb") as f:
                        f.write(content)

            # Return relative path from workspace
            # Use forward slashes for web consistency
            relative_path = os.path.relpath(full_path, self.workspace_path).replace("\\", "/")
            self._image_cache[url] = relative_path
            
            return True, relative_path

        except asyncio.TimeoutError:
            return False, "Download timed out"
        except Exception as e:
            return False, f"Error saving image: {str(e)}"

    async def save_generated_image(
        self,
        image_obj: Any,
        filename: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Save a GeneratedImage object from Gemini response.
        
        Args:
            image_obj: Gemini Image object (WebImage or GeneratedImage)
            filename: Optional custom filename
            
        Returns:
            Tuple of (success, path_or_error)
        """
        try:
            images_dir = self._get_images_dir()
            
            if not filename:
                filename = self._generate_filename("generated", "png")
            
            full_path = os.path.join(images_dir, filename)
            
            # Use the image object's save method if available
            if hasattr(image_obj, 'save'):
                await image_obj.save(path=images_dir, filename=filename, verbose=False)
            elif hasattr(image_obj, 'url'):
                # Fallback to URL download
                return await self.save_image_from_url(image_obj.url, filename)
            else:
                return False, "Unknown image object type"

            relative_path = os.path.relpath(full_path, self.workspace_path)
            return True, relative_path

        except Exception as e:
            return False, f"Error saving generated image: {str(e)}"

    def process_response_images(self, response: Any) -> List[ImageResult]:
        """
        Process images from a Gemini response.
        
        Args:
            response: Gemini ModelOutput object
            
        Returns:
            List of ImageResult objects
        """
        results = []
        
        if not hasattr(response, 'images') or not response.images:
            return results

        for img in response.images:
            # Determine image type
            # GeneratedImage vs WebImage - check class name
            class_name = type(img).__name__.lower()
            
            if "generated" in class_name:
                img_type = ImageType.GENERATED
            else:
                img_type = ImageType.WEB

            result = ImageResult(
                url=getattr(img, 'url', ''),
                image_type=img_type,
                title=getattr(img, 'title', None),
                alt=getattr(img, 'alt', None)
            )
            results.append(result)

        self.generated_images.extend(results)
        return results

    def get_image_info(self, index: int = -1) -> Optional[Dict[str, Any]]:
        """Get info about a generated image by index."""
        if not self.generated_images:
            return None
        
        try:
            img = self.generated_images[index]
            return img.to_dict()
        except IndexError:
            return None

    def clear_cache(self):
        """Clear the image cache."""
        self.generated_images = []
        self._image_cache = {}


class ImageGenerationTool:
    """
    Tool interface for AI agent to generate and manage images.
    
    This works by constructing prompts that trigger Gemini's
    internal image generation capabilities.
    """

    def __init__(self, image_service: ImageService):
        self.service = image_service

    def get_tool_description(self) -> Dict[str, Any]:
        """Get tool schema for the agent."""
        return {
            "name": "generate_image",
            "description": "Generate an AI image from a text prompt. The image will be created by Gemini's image model and can optionally be saved to the project.",
            "parameters": {
                "prompt": {
                    "type": "string",
                    "required": True,
                    "description": "Detailed description of the image to generate"
                },
                "save_to_project": {
                    "type": "boolean",
                    "required": False,
                    "default": False,
                    "description": "Whether to save the image to the project's assets folder"
                },
                "filename": {
                    "type": "string",
                    "required": False,
                    "description": "Custom filename for the saved image (without path)"
                }
            },
            "returns": "Image generation request. The image will appear in the response.",
            "example": '{"action": "generate_image", "args": {"prompt": "A modern logo for a coffee shop with minimalist design", "save_to_project": true, "filename": "logo.png"}}'
        }

    def format_generation_prompt(self, prompt: str) -> str:
        """
        Format a prompt to trigger Gemini's image generation.
        
        The key is to explicitly ask Gemini to GENERATE the image,
        not just search for one.
        """
        return f"""Please generate an image with the following description:

{prompt}

Important: Use your image generation capabilities to CREATE a new, original image based on this description. Do not search for existing images - generate a new one."""

    async def save_last_generated(
        self,
        filename: Optional[str] = None
    ) -> str:
        """Save the most recently generated image to the project."""
        if not self.service.generated_images:
            return "Error: No generated images available to save."

        last_image = self.service.generated_images[-1]
        
        if last_image.saved and last_image.local_path:
            return f"Image already saved at: {last_image.local_path}"

        success, result = await self.service.save_image_from_url(
            last_image.url,
            filename
        )

        if success:
            last_image.local_path = result
            last_image.saved = True
            return f"Image saved to: {result}"
        else:
            return f"Error: {result}"


# Tool function for agent integration
async def generate_image_tool(
    prompt: str,
    save_to_project: bool = False,
    filename: Optional[str] = None,
    workspace_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tool function that can be called by the agent.
    
    Returns a dict with:
    - generation_prompt: The formatted prompt for Gemini
    - save_requested: Whether to save after generation
    - filename: The requested filename
    """
    return {
        "action": "image_generation_request",
        "generation_prompt": f"Generate an image: {prompt}",
        "original_prompt": prompt,
        "save_to_project": save_to_project,
        "filename": filename,
        "workspace_path": workspace_path
    }


# Singleton service instance
_image_service: Optional[ImageService] = None


def get_image_service(workspace_path: str = None) -> ImageService:
    """Get or create the image service singleton."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService(workspace_path)
    elif workspace_path:
        _image_service.set_workspace(workspace_path)
    return _image_service
