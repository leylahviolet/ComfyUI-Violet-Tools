import os
import json
import datetime
import hashlib
from typing import Any, Dict, Optional, Tuple

from PIL import Image, PngImagePlugin
import numpy as np

def _now_str() -> str:
    """Local time string for filename"""
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

def _shape_wh(image: Optional[np.ndarray]) -> Tuple[Optional[int], Optional[int]]:
    """Extract width/height from ComfyUI IMAGE tensor"""
    if image is None:
        return None, None
    arr = image
    if isinstance(arr, list):  # Some nodes pass lists
        arr = arr[0]
    if arr.ndim == 4:  # B,H,W,C -> take first
        _, h, w, _ = arr.shape
    elif arr.ndim == 3:  # H,W,C
        h, w, _ = arr.shape
    else:
        return None, None
    return w, h

def _to_pil(image: Optional[np.ndarray]) -> Image.Image:
    """Convert ComfyUI IMAGE to PIL Image. Creates 1x1 placeholder if no image."""
    if image is None:
        return Image.new("RGB", (1, 1), (0, 0, 0))
    arr = image
    if isinstance(arr, list):
        arr = arr[0]
    if arr.ndim == 4:
        arr = arr[0]
    # Convert from 0..1 float to 0..255 uint8
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def _extract_model_info(model_obj: Any) -> Dict[str, Optional[str]]:
    """
    Extract model name and hash from ComfyUI MODEL object.
    Based on patterns from save_image_extended.py and utils_info.py.
    """
    if model_obj is None:
        return {"name": None, "hash": None}
    
    name = None
    model_hash = None
    
    try:
        # Try to get model config/path info (ComfyUI model objects usually have these)
        if hasattr(model_obj, 'model') and hasattr(model_obj.model, 'model_config'):
            config = model_obj.model.model_config
            if hasattr(config, 'unet_config') and hasattr(config.unet_config, 'model_path'):
                model_path = config.unet_config.model_path
                if model_path:
                    # Extract name from path
                    name = os.path.splitext(os.path.basename(model_path))[0]
                    # Remove common model extensions  
                    for ext in ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']:
                        name = name.removesuffix(ext)
                    
                    # Calculate hash if file exists
                    if os.path.exists(model_path):
                        model_hash = _get_file_hash(model_path)
        
        # Alternative: try to get from model patcher (another ComfyUI pattern)
        elif hasattr(model_obj, 'model_patcher'):
            patcher = model_obj.model_patcher
            if hasattr(patcher, 'model_options') and 'model_path' in patcher.model_options:
                model_path = patcher.model_options['model_path']
                if model_path:
                    name = os.path.splitext(os.path.basename(model_path))[0]
                    for ext in ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']:
                        name = name.removesuffix(ext)
                    if os.path.exists(model_path):
                        model_hash = _get_file_hash(model_path)
        
        # Try model.model.diffusion_model.checkpoint_path (yet another pattern)
        elif hasattr(model_obj, 'model') and hasattr(model_obj.model, 'diffusion_model'):
            diff_model = model_obj.model.diffusion_model  
            if hasattr(diff_model, 'checkpoint_path'):
                model_path = diff_model.checkpoint_path
                if model_path:
                    name = os.path.splitext(os.path.basename(model_path))[0]
                    for ext in ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']:
                        name = name.removesuffix(ext)
                    if os.path.exists(model_path):
                        model_hash = _get_file_hash(model_path)
                        
    except Exception:
        # Silent fallback - don't break the node if model introspection fails
        pass
    
    return {"name": name, "hash": model_hash}

def _get_file_hash(file_path: str, truncate_length: int = 12) -> Optional[str]:
    """Calculate SHA256 hash of file, truncated for compact metadata"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        BUF_SIZE = 1024 * 128  # 128KB chunks
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(BUF_SIZE), b""):
                sha256_hash.update(chunk)
        # Return first N characters for compact metadata
        return sha256_hash.hexdigest()[:truncate_length]
    except Exception:
        return None

class SaveSiren:
    """
    🧜‍♀️ Save Siren — Save PNG with compact Violet Tools metadata
    
    Saves images with a minimal JSON metadata block containing only the essential 
    generation parameters. Designed to avoid ComfyUI's massive workflow bloat 
    for uploading to sites with strict file size limits.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Auto-populate sampler choices if available
        sampler_input = ("STRING", {"default": "euler_ancestral"})
        try:
            # Try to get KSampler choices - this is the most common pattern
            import nodes
            if hasattr(nodes, 'KSampler') and hasattr(nodes.KSampler, 'INPUT_TYPES'):
                ksampler_inputs = nodes.KSampler.INPUT_TYPES()
                if 'required' in ksampler_inputs and 'sampler_name' in ksampler_inputs['required']:
                    sampler_choices = ksampler_inputs['required']['sampler_name']
                    if isinstance(sampler_choices, (list, tuple)) and len(sampler_choices) > 0:
                        sampler_input = (sampler_choices[0], {"default": sampler_choices[0][0] if sampler_choices[0] else "euler_ancestral"})
        except Exception:
            # Fallback to common samplers
            common_samplers = ["euler_ancestral", "euler", "dpmpp_2m", "dpmpp_sde", "heun", "dpm_2", "lms"]
            sampler_input = (common_samplers, {"default": "euler_ancestral"})

        return {
            "required": {
                "steps": ("INT", {"default": 25, "min": 1, "max": 1000}),
                "cfg": ("FLOAT", {"default": 7.5, "min": 0.0, "max": 100.0, "step": 0.1}),
                "sampler": sampler_input,
                "used_detailer": ("BOOLEAN", {"default": False}),
                "filename_prefix": ("STRING", {"default": "vt", "tooltip": "Prefix for saved filename"})
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Image to save (creates 1x1 placeholder if missing)"}),
                "model": ("MODEL", {"tooltip": "Model object to extract name/hash from"}),  
                "positive": ("STRING", {"forceInput": True, "tooltip": "Positive prompt"}),
                "negative": ("STRING", {"forceInput": True, "tooltip": "Negative prompt"}),
                "seed": ("INT", {"forceInput": True, "tooltip": "Generation seed"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("metadata",)
    FUNCTION = "save"
    CATEGORY = "Violet Tools 💅/Utility"
    OUTPUT_NODE = True

    def save(
        self,
        steps: int,
        cfg: float,
        sampler: str,
        used_detailer: bool,
        filename_prefix: str,
        image: Optional[np.ndarray] = None,
        model: Any = None,
        positive: Optional[str] = None,
        negative: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Tuple[str]:
        
        # Extract image dimensions
        w, h = _shape_wh(image)
        size_str = f"{w}x{h}" if (w and h) else None
        
        # Extract model info  
        model_info = _extract_model_info(model)
        
        # Build compact metadata payload
        payload = {}
        
        # Only include non-null values to keep JSON compact
        if size_str:
            payload["size"] = size_str
        if positive and positive.strip():
            payload["prompt"] = positive.strip()
        if negative and negative.strip():
            payload["negative_prompt"] = negative.strip()
        if isinstance(seed, int) and seed >= 0:
            payload["seed"] = seed
            
        # Always include these core generation params
        payload["steps"] = steps
        payload["cfg_scale"] = round(cfg, 2)  # Round to 2 decimal places
        payload["sampler"] = sampler
        payload["is_adetailer"] = bool(used_detailer)
        payload["model"] = model_info
        payload["saved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create compact JSON (no spaces, sorted keys for consistency)
        meta_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)

        # Build filename 
        timestamp = _now_str()
        safe_prefix = (filename_prefix or "vt").strip()
        # Sanitize prefix for filesystem safety
        safe_prefix = "".join(c for c in safe_prefix if c.isalnum() or c in "._-")
        if not safe_prefix:
            safe_prefix = "vt"
        filename = f"{safe_prefix}-{timestamp}.png"

        # Determine output directory
        output_dir = os.path.join(os.getcwd(), "output")
        try:
            import folder_paths
            output_dir = folder_paths.get_output_directory()
        except Exception:
            pass
        
        # Ensure directory exists
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, filename)

        # Convert to PIL and embed metadata
        pil_image = _to_pil(image)
        pnginfo = PngImagePlugin.PngInfo()
        
        # Embed our compact JSON under custom key
        pnginfo.add_text("vt_json", meta_json)
        
        # Optional: add a minimal 'parameters' field for basic compatibility
        # Some tools look for this standard key
        if positive or steps or cfg:
            basic_params = []
            if positive and positive.strip():
                basic_params.append(f"prompt: {positive.strip()[:100]}")  # Truncate long prompts
            basic_params.append(f"steps: {steps}")
            basic_params.append(f"cfg: {cfg}")
            basic_params.append(f"sampler: {sampler}")
            pnginfo.add_text("parameters", ", ".join(basic_params))

        # Save PNG with metadata
        pil_image.save(file_path, format="PNG", pnginfo=pnginfo, optimize=True)

        print(f"🧜‍♀️ Save Siren: Saved {filename} ({os.path.getsize(file_path)} bytes)")
        
        return (meta_json,)

# Node registration
NODE_CLASS_MAPPINGS = {"SaveSiren": SaveSiren}
NODE_DISPLAY_NAME_MAPPINGS = {"SaveSiren": "🧜‍♀️ Save Siren"}
