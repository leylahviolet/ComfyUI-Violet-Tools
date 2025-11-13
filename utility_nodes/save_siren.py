from typing import Any, Dict, Optional, Tuple, List
import os
import hashlib
import datetime
import json
import numpy as np
from PIL import Image, PngImagePlugin


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
    # Convert tensor to numpy if needed
    if hasattr(arr, 'cpu'):  # PyTorch tensor
        arr = arr.cpu().numpy()
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
    # Convert tensor to numpy if needed (ComfyUI passes tensors)
    if hasattr(arr, 'cpu'):  # PyTorch tensor
        arr = arr.cpu().numpy()
    # Convert from 0..1 float to 0..255 uint8
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _clean_filename(filename: str) -> str:
    """Remove subfolder paths and clean up filename for display"""
    if not filename:
        return filename
    
    # Remove path separators (both Windows and Unix style)
    clean_name = filename.split('\\')[-1].split('/')[-1]
    
    # Remove common file extensions for cleaner display
    for ext in ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']:
        clean_name = clean_name.removesuffix(ext)
    
    return clean_name


def _get_civitai_name(file_hash: str, model_type: str = "unknown") -> Optional[str]:
    """Get the real model name from Civitai using file hash"""
    if not file_hash:
        return None
    
    try:
        import requests
        api_url = f'https://civitai.com/api/v1/model-versions/by-hash/{file_hash}'
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Get model name and version name
            model_name = data.get('model', {}).get('name', '')
            version_name = data.get('name', '')
            
            if model_name and version_name:
                return f"{model_name} - {version_name}"
            elif model_name:
                return model_name
            elif version_name:
                return version_name
                
    except Exception:
        pass  # Silently handle API failures
    
    return None


def _get_civitai_info(file_hash: str, model_type: str = "unknown") -> tuple[Optional[str], Optional[str]]:
    """Get both filename and correct hash from Civitai API
    
    Returns the actual filename (not display name) for maximum compatibility 
    with sites like socialdiff.net that require exact filename matches.
    """
    if not file_hash:
        return None, None
    
    try:
        import requests
        api_url = f'https://civitai.com/api/v1/model-versions/by-hash/{file_hash}'
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Get the actual filename from files array - this is key for socialdiff.net recognition!
            files = data.get('files', [])
            filename = None
            correct_hash = None
            
            for file_info in files:
                hashes = file_info.get('hashes', {})
                
                # Choose hash type based on model_type
                target_hash = None
                if model_type == "checkpoints":
                    # Models should use AUTOV2
                    if 'AutoV2' in hashes:
                        target_hash = hashes['AutoV2'].lower()  # Force lowercase!
                elif model_type == "loras":
                    # LoRAs should use AUTOV3
                    if 'AutoV3' in hashes:
                        target_hash = hashes['AutoV3'].lower()  # Force lowercase!
                
                # If we didn't find the preferred type, fall back to any available
                if not target_hash:
                    if 'AutoV3' in hashes:
                        target_hash = hashes['AutoV3'].lower()
                    elif 'AutoV2' in hashes:
                        target_hash = hashes['AutoV2'].lower()
                    elif 'SHA256' in hashes:
                        # Last resort: truncated SHA256
                        sha256 = hashes['SHA256']
                        target_hash = (sha256[:12] if len(sha256) > 12 else sha256).lower()
                
                if target_hash:
                    correct_hash = target_hash
                    # Extract actual filename - remove extension for cleaner name
                    raw_filename = file_info.get('name', '')
                    if raw_filename:
                        # Remove .safetensors, .ckpt, .pt extensions for metadata
                        import os
                        filename = os.path.splitext(raw_filename)[0]
                    break
            
            return filename, correct_hash
                
    except Exception:
        pass  # Silently handle API failures
    
    return None, None


# Workflow-based model and LoRA extraction helpers
def _sha256(path: str, short: int = 12) -> Optional[str]:
    """Calculate SHA256 hash of file, truncated for compact metadata"""
    if not path or not os.path.exists(path):
        return None
    try:
        BUF_SIZE = 1024 * 128  # 128KB chunks
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(BUF_SIZE), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()[:short]
    except Exception:
        return None


def _resolve_path(category: str, name: str) -> Optional[str]:
    """Resolve model/LoRA name to full path using folder_paths"""
    try:
        import folder_paths
        return folder_paths.get_full_path(category, name)
    except Exception:
        return None


def _resolve_any_lora_path(name: str) -> Optional[str]:
    """Try to resolve LoRA name in both loras and lycoris folders"""
    for cat in ("loras", "lycoris"):
        p = _resolve_path(cat, name)
        if p:
            return p
    return None


def _get_workflow(extra_pnginfo: Any, prompt: Any) -> Optional[Dict[str, Any]]:
    """Extract workflow graph from ComfyUI execution context"""
    wf = None
    if isinstance(extra_pnginfo, dict):
        wf = extra_pnginfo.get("workflow")
    if not wf and isinstance(prompt, dict):
        wf = prompt.get("workflow")  # rare fallback
    return wf if isinstance(wf, dict) else None


def _index_workflow(wf: Dict[str, Any]):
    """Build lookup structures for workflow graph navigation"""
    nodes = {n["id"]: n for n in wf.get("nodes", []) if isinstance(n, dict) and "id" in n}
    links = wf.get("links", [])
    # Build: link_id -> (src_node, src_slot, dst_node, dst_slot)
    linkmap = {}
    for l in links:
        # Format: [link_id, from_node, from_slot, to_node, to_slot, ...]
        if isinstance(l, list) and len(l) >= 5:
            linkmap[l[0]] = (l[1], l[2], l[3], l[4])
    return nodes, linkmap


def _find_this_node(nodes: Dict[int, Dict[str, Any]], class_types=("SaveSiren", "🧜‍♀️ Save Siren")) -> Optional[Dict[str, Any]]:
    """Find our Save Siren node in the workflow graph"""
    candidates = [n for n in nodes.values() if n.get("type") in class_types]
    if candidates:
        return candidates[-1]  # Most recent if multiple
    # Fallback: match by title
    candidates = [n for n in nodes.values() if n.get("title") in class_types]
    return candidates[-1] if candidates else None


def _link_src_for_input(nodes, linkmap, node, input_name: str) -> Optional[int]:
    """Find the source node feeding a specific input socket"""
    for inp in node.get("inputs", []):
        if inp.get("name") == input_name and inp.get("link") in linkmap:
            src_node_id = linkmap[inp["link"]][0]
            return src_node_id
    return None


def _walk_model_chain(nodes, linkmap, start_node_id: int):
    """Walk upstream from model input to collect checkpoint and LoRAs"""
    ckpt_name = None
    lora_nodes: List[Dict[str, Any]] = []

    seen = set()
    stack = [start_node_id]
    
    while stack:
        nid = stack.pop()
        if nid in seen:
            continue
        seen.add(nid)
        n = nodes.get(nid)
        if not n:
            continue
        ntype = n.get("type") or n.get("title") or ""

        # LoRA detection FIRST to avoid conflicts (more specific keywords)
        if any(keyword in ntype for keyword in ["LoraLoader", "LoRA", "Lora", "Power"]):
            lora_nodes.append(n)
            
        # Checkpoint loader detection (more restrictive to avoid LoRA conflicts)
        elif any(keyword in ntype for keyword in ["CheckpointLoader", "CheckpointLoaderSimple", "Checkpoint"]) or ntype in ["Load Checkpoint", "ModelLoader"]:
            inputs = n.get("inputs", [])
            for i in inputs:
                input_name = i.get("name", "")
                input_value = i.get("value", "")
                # Expanded input name detection for different loader types
                if input_name in ["ckpt_name", "model_name", "checkpoint_name", "name"] and input_value:
                    ckpt_name = input_value.strip()
            
            # If inputs are empty, check widgets (most common case)
            if not ckpt_name:
                widgets = n.get("widgets_values", [])
                if widgets and len(widgets) > 0 and widgets[0]:
                    ckpt_name = widgets[0].strip()

        # Continue upstream via "model" input
        src = _link_src_for_input(nodes, linkmap, n, "model")
        if src is not None:
            stack.append(src)

    # LoRAs in application order (closest to checkpoint first)
    lora_nodes.reverse()
    return ckpt_name, lora_nodes


def extract_model_and_loras(prompt, extra_pnginfo, want_hashes=True):
    """
    Extract model and LoRA info from workflow graph.
    Returns: (model_info, loras_list)
    """
    wf = _get_workflow(extra_pnginfo, prompt)
    model_info = {"name": None, "hash": None}
    loras_out: List[Dict[str, Any]] = []

    if wf:
        nodes, linkmap = _index_workflow(wf)
        me = _find_this_node(nodes)
        if me:
            upstream_model_node = _link_src_for_input(nodes, linkmap, me, "model")
            if upstream_model_node is not None:
                ckpt_name, lora_nodes = _walk_model_chain(nodes, linkmap, upstream_model_node)

                # Model name + hash
                if ckpt_name:
                    model_info["name"] = _clean_filename(ckpt_name)
                    if want_hashes:
                        p = _resolve_path("checkpoints", ckpt_name)
                        full_hash = _sha256(p, short=64) if p else None  # Get full hash for Civitai lookup
                        
                        # Try to get real name and correct hash from Civitai
                        if full_hash:
                            civitai_name, correct_hash = _get_civitai_info(full_hash, "checkpoints")
                            if civitai_name:
                                model_info["name"] = civitai_name
                            if correct_hash:
                                model_info["hash"] = correct_hash  # Use Civitai's AUTOV2 hash!
                            else:
                                # Fallback to truncated SHA256
                                model_info["hash"] = full_hash[:10].lower()  # Force lowercase!
                        else:
                            model_info["hash"] = None

                # Each LoRA
                for ln in lora_nodes:
                    lora_entries = []
                    ntype = ln.get("type") or ln.get("title") or ""
                    
                    # Handle rgthree Power Lora Loader (complex widget structure)
                    if "Power Lora Loader" in ntype:
                        widgets = ln.get("widgets_values", [])
                        for widget in widgets:
                            if isinstance(widget, dict) and widget.get("on") and widget.get("lora"):
                                name = widget.get("lora")
                                strength = widget.get("strength", 1.0)
                                # Power Lora Loader uses single strength for both model and clip
                                lora_entries.append((name, strength, strength))
                    else:
                        # Handle standard LoraLoader
                        name, sm, sc = None, None, None
                        
                        # First try inputs (for connected LoRAs)
                        for i in ln.get("inputs", []):
                            if i.get("name") == "lora_name":
                                name = (i.get("value") or "").strip() or name
                            elif i.get("name") == "strength_model":
                                sm = i.get("value")
                            elif i.get("name") == "strength_clip":
                                sc = i.get("value")
                        
                        # If no inputs, try widgets (most common for LoRA nodes)
                        if not name:
                            widgets = ln.get("widgets_values", [])
                            if len(widgets) >= 1:  # LoraLoader typically: [name, strength_model, strength_clip]
                                name = widgets[0] if widgets[0] else None
                            if len(widgets) >= 2:
                                try:
                                    sm = float(widgets[1]) if widgets[1] is not None else None
                                except (ValueError, TypeError):
                                    sm = None
                            if len(widgets) >= 3:
                                try:
                                    sc = float(widgets[2]) if widgets[2] is not None else None
                                except (ValueError, TypeError):
                                    sc = None
                        
                        if name and name.strip():
                            lora_entries.append((name, sm, sc))
                    
                    # Process all LoRA entries from this node
                    for name, sm, sc in lora_entries:
                        if name and name.strip():
                            clean_name = _clean_filename(name.strip())
                            lhash = None
                            civitai_name = None
                            
                            if want_hashes:
                                lp = _resolve_any_lora_path(name)
                                if lp:
                                    full_hash = _sha256(lp, short=64)  # Full hash for Civitai lookup
                                    
                                    # Try to get real name and correct hash from Civitai
                                    if full_hash:
                                        civitai_name, correct_hash = _get_civitai_info(full_hash, "loras")
                                        if correct_hash:
                                            lhash = correct_hash  # Use Civitai's AUTOV3 hash!
                                        else:
                                            # Fallback to truncated SHA256
                                            lhash = full_hash[:12].lower()  # Force lowercase!
                                    else:
                                        lhash = None
                            
                            loras_out.append({
                                "name": civitai_name if civitai_name else clean_name,
                                "filename": clean_name,  # Keep original filename for reference
                                "hash": lhash,
                                "strength_model": round(sm, 2) if sm is not None else None,
                            "strength_clip": round(sc, 2) if sc is not None else None
                        })

    return model_info, loras_out


def _build_a1111_parameters(payload: Dict[str, Any], loras: List[Dict[str, Any]]) -> str:
    """Build A1111 format parameters string matching exact reference format"""
    parts = []
    
    # Line 1: Positive prompt with LoRA tags appended
    prompt = payload.get("positiveprompt", "")
    
    # Add LoRA tags to positive prompt (essential for external site recognition)
    if loras:
        lora_tags = []
        for lora in loras:
            # Use civitai name for the tag
            name = lora.get("name", lora.get("filename", "unknown"))
            # Use model strength for the tag (standard A1111 practice)
            strength = lora.get("strength_model")
            if strength is not None:
                lora_tags.append(f"<lora:{name}:{strength}>")
            else:
                lora_tags.append(f"<lora:{name}:1.0>")  # Default strength
        
        if lora_tags:
            # Append LoRA tags to prompt with proper spacing
            if prompt.strip():
                prompt = f"{prompt.rstrip()}, {', '.join(lora_tags)},"
            else:
                prompt = f"{', '.join(lora_tags)},"
    
    parts.append(prompt)
    
    # Line 2: Negative prompt with exact label format
    negative = payload.get("negativeprompt", "")
    if negative:
        parts.append(f"Negative prompt: {negative}")
    
    # Line 3: All settings in exact reference order and format
    settings = []
    
    # Steps
    if "steps" in payload:
        settings.append(f"Steps: {payload['steps']}")
    
    # Sampler 
    if "sampler" in payload:
        settings.append(f"Sampler: {payload['sampler']}")
    
    # Schedule type (exact capitalization from reference)
    settings.append("Schedule type: Automatic")
    
    # CFG scale (exact format from reference)
    if "cfg" in payload:
        settings.append(f"CFG scale: {payload['cfg']}")
    
    # Seed
    if "seed" in payload:
        settings.append(f"Seed: {payload['seed']}")
    
    # Size
    if "size" in payload:
        settings.append(f"Size: {payload['size']}")
    
    # Model hash (10-digit AUTOV2, lowercase)
    if "hash" in payload:
        model_hash = payload['hash']
        short_model_hash = model_hash[:10] if len(model_hash) > 10 else model_hash
        settings.append(f"Model hash: {short_model_hash.lower()}")
    
    # Model name
    if "model" in payload:
        settings.append(f"Model: {payload['model']}")
    
    # Lora hashes (exact capitalization and format from reference)
    if loras:
        lora_hashes = []
        for lora in loras:
            # Use civitai name (stored in "name") for socialdiff.net compatibility
            # Fall back to filename only if civitai name unavailable
            name = lora.get("name", lora.get("filename", "unknown"))
            hash_val = lora.get("hash", "unknown")
            if hash_val and hash_val != "unknown":
                # 12-digit AUTOV3 hash, lowercase
                short_hash = hash_val[:12] if len(hash_val) > 12 else hash_val
                lora_hashes.append(f"{name}: {short_hash.lower()}")
        
        if lora_hashes:
            settings.append(f'Lora hashes: "{", ".join(lora_hashes)}"')
    
    # Version (exact format from reference)
    settings.append("Version: v1.10.0")
    
    # Add settings line
    if settings:
        parts.append(", ".join(settings))
    
    return "\n".join(parts)


def _extract_model_info(model_obj: Any) -> Dict[str, Optional[str]]:
    """
    Fallback model extraction from MODEL object (introspection).
    Prefer workflow-based extraction when possible.
    """
    if model_obj is None:
        return {"name": None, "hash": None}
    
    name = None
    model_hash = None
    
    try:
        # Method 1: ModelPatcher pattern (most common)
        if type(model_obj).__name__ == 'ModelPatcher':
            if hasattr(model_obj, 'model_options') and isinstance(model_obj.model_options, dict):
                model_path = model_obj.model_options.get('model_path')
                if model_path and os.path.exists(model_path):
                    name = _extract_model_name(model_path)
                    model_hash = _get_file_hash(model_path)
            
            # Try additional ModelPatcher attributes for newer ComfyUI versions
            actual_attrs = [attr for attr in dir(model_obj) if not attr.startswith('_')]
            
            # Try to access the underlying model for path info
            if not name and hasattr(model_obj, 'model') and model_obj.model:
                inner_model = model_obj.model
                if hasattr(inner_model, 'model_config') and inner_model.model_config:
                    config = inner_model.model_config
                    # Look for path-related attributes in config
                    for attr in ['unet_config', 'model_path', 'checkpoint_path']:
                        if hasattr(config, attr):
                            attr_val = getattr(config, attr)
                            if hasattr(attr_val, 'model_path'):
                                path_val = attr_val.model_path
                                if path_val and os.path.exists(path_val):
                                    name = _extract_model_name(path_val)
                                    model_hash = _get_file_hash(path_val)
                                    break
        
        # Method 2: Nested model patcher
        if not name and hasattr(model_obj, 'model') and hasattr(model_obj.model, 'model_patcher'):
            patcher = model_obj.model.model_patcher
            if hasattr(patcher, 'model_options') and isinstance(patcher.model_options, dict):
                model_path = patcher.model_options.get('model_path')
                if model_path and os.path.exists(model_path):
                    name = _extract_model_name(model_path)
                    model_hash = _get_file_hash(model_path)
        
        # Method 3: Direct path attributes
        if not name:
            for attr_path in ['checkpoint_path', 'model_path', 'ckpt_path']:
                if hasattr(model_obj, attr_path):
                    path_val = getattr(model_obj, attr_path)
                    if isinstance(path_val, str) and path_val and os.path.exists(path_val):
                        name = _extract_model_name(path_val)
                        model_hash = _get_file_hash(path_val)
                        break
        
        # Method 4: Deep search
        if not name:
            model_path = _deep_search_for_model_path(model_obj)
            if model_path and os.path.exists(model_path):
                name = _extract_model_name(model_path)
                model_hash = _get_file_hash(model_path)
                        
    except Exception as e:
        pass  # Silently handle errors in fallback mode
    
    return {"name": name, "hash": model_hash}


def _extract_model_name(file_path: str) -> Optional[str]:
    """Extract clean model name from file path"""
    if not file_path:
        return None
    name = os.path.splitext(os.path.basename(file_path))[0]
    # Remove common model extensions  
    for ext in ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']:
        name = name.removesuffix(ext)
    return name if name else None


def _deep_search_for_model_path(obj: Any, max_depth: int = 3) -> Optional[str]:
    """Recursively search object for model path attributes"""
    if max_depth <= 0 or obj is None:
        return None
    
    # Check for common path attributes
    path_attrs = ['model_path', 'checkpoint_path', 'ckpt_path', 'file_path', 'path']
    for attr in path_attrs:
        if hasattr(obj, attr):
            path = getattr(obj, attr)
            if isinstance(path, str) and path and os.path.exists(path):
                return path
    
    # Search deeper in common model object attributes
    search_attrs = ['model', 'model_patcher', 'diffusion_model', 'unet', 'model_config', 'config']
    for attr in search_attrs:
        if hasattr(obj, attr):
            sub_obj = getattr(obj, attr)
            result = _deep_search_for_model_path(sub_obj, max_depth - 1)
            if result:
                return result
    
    # Search in dictionaries
    if isinstance(obj, dict):
        for key in ['model_path', 'checkpoint_path', 'ckpt_path', 'file_path', 'path']:
            if key in obj and isinstance(obj[key], str) and obj[key] and os.path.exists(obj[key]):
                return obj[key]
    
    return None


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
                if "sampler_name" in ksampler_inputs.get("required", {}):
                    sampler_choices = ksampler_inputs["required"]["sampler_name"]
                    if isinstance(sampler_choices, (list, tuple)) and len(sampler_choices) > 0:
                        # Handle both (choices, {}) and just [choices] formats
                        choices = sampler_choices[0] if isinstance(sampler_choices[0], (list, tuple)) else sampler_choices
                        sampler_input = (choices, {"default": "euler_ancestral"})
        except Exception:
            # Fallback to common samplers
            common_samplers = ["euler_ancestral", "euler", "dpmpp_2m", "dpmpp_sde", "heun", "dpm_2", "lms"]
            sampler_input = (common_samplers, {"default": "euler_ancestral"})

        return {
            "required": {
                "steps": ("INT", {"default": 25, "min": 1, "max": 1000}),
                "cfg": ("FLOAT", {"default": 7.5, "min": 0.0, "max": 100.0, "step": 0.1}),
                "sampler": sampler_input,
                "filename_prefix": ("STRING", {"default": "Violet", "tooltip": "Prefix for saved filename. Supports folders: 'folder/Violet', 'portraits/fantasy/Violet', etc."})
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Image to save (creates 1x1 placeholder if missing)"}),
                "model": ("MODEL", {"tooltip": "Model object to extract name/hash from"}),  
                "positive": ("STRING", {"forceInput": True, "tooltip": "Positive prompt"}),
                "negative": ("STRING", {"forceInput": True, "tooltip": "Negative prompt"}),
                "seed": ("INT", {"forceInput": True, "tooltip": "Generation seed"})
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
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
        filename_prefix: str,
        image: Optional[np.ndarray] = None,
        model: Any = None,
        positive: Optional[str] = None,
        negative: Optional[str] = None,
        seed: Optional[int] = None,
        prompt: Any = None,
        extra_pnginfo: Any = None
    ) -> Tuple[str]:
        # Extract image dimensions
        w, h = _shape_wh(image)
        size_str = f"{w}x{h}" if (w and h) else None
        
        # Extract model and LoRA info via workflow (preferred) or fallback to introspection
        model_info, loras = extract_model_and_loras(prompt, extra_pnginfo, want_hashes=True)
        
        # If workflow extraction failed, try introspection fallback
        if not model_info.get("name"):
            fallback_info = _extract_model_info(model)
            if fallback_info.get("name"):
                model_info = fallback_info
        
        # Build compact metadata payload
        payload = {}
        
        # Flat structure for external site compatibility
        # Based on analysis of site JS: expects hash, model, positiveprompt, negativeprompt, cfg, etc.
        
        # Core generation parameters
        payload["steps"] = steps
        payload["cfg"] = round(cfg, 2)  # Changed from cfg_scale to cfg for site compatibility
        payload["sampler"] = sampler
        
        # Model info at top level (not nested)
        payload["model"] = model_info.get("name")  # Flat model name
        payload["hash"] = model_info.get("hash")   # Flat model hash
        
        # Prompts with site-expected field names
        if positive and positive.strip():
            payload["positiveprompt"] = positive.strip()  # Changed from "prompt" 
        if negative and negative.strip():
            payload["negativeprompt"] = negative.strip()  # Changed from "negative_prompt"
        
        # Optional fields
        if isinstance(seed, int) and seed >= 0:
            payload["seed"] = seed
        if size_str:
            payload["size"] = size_str
            
        # LoRAs as separate top-level array for easier parsing
        if loras:
            payload["loras"] = loras
        
        payload["saved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Keep raw nested structure commented out for potential future use
        # # Original nested structure (commented out):
        # # model_payload = {"name": model_info.get("name"), "hash": model_info.get("hash")}
        # # if loras:
        # #     model_payload["loras"] = loras
        # # payload["model"] = model_payload
        
        payload["saved_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create compact JSON (no spaces, sorted keys for consistency)
        meta_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
        
        # ALSO create A1111 format for external site compatibility
        a1111_params = _build_a1111_parameters(payload, loras)

        # Build filename with folder support
        timestamp = _now_str()
        raw_prefix = (filename_prefix or "vt").strip()
        
        # Split prefix into folder path and filename components
        # Convert backslashes to forward slashes for consistent handling
        normalized_prefix = raw_prefix.replace("\\", "/")
        
        # Split into folder path and filename prefix
        if "/" in normalized_prefix:
            folder_parts = normalized_prefix.split("/")
            filename_part = folder_parts[-1]  # Last part is filename prefix
            folder_path = "/".join(folder_parts[:-1])  # Everything else is folder path
        else:
            folder_path = ""
            filename_part = normalized_prefix
        
        # Sanitize folder path components for filesystem safety
        if folder_path:
            safe_folder_parts = []
            for part in folder_path.split("/"):
                # Remove any dangerous characters and ensure each part is valid
                safe_part = "".join(c for c in part.strip() if c.isalnum() or c in "._- ")
                safe_part = safe_part.strip()  # Remove leading/trailing spaces
                # Prevent directory traversal and invalid folder names
                if safe_part and safe_part not in [".", ".."] and not safe_part.startswith('.'):
                    safe_folder_parts.append(safe_part)
            safe_folder_path = "/".join(safe_folder_parts) if safe_folder_parts else ""
        else:
            safe_folder_path = ""
        
        # Sanitize filename prefix for filesystem safety
        safe_filename_prefix = "".join(c for c in filename_part if c.isalnum() or c in "._-")
        if not safe_filename_prefix:
            safe_filename_prefix = "vt"
            
        filename = f"{safe_filename_prefix}-{timestamp}.png"

        # Determine output directory
        output_dir = os.path.join(os.getcwd(), "output")
        try:
            import folder_paths
            output_dir = folder_paths.get_output_directory()
        except Exception:
            pass
        
        # Build full path with subfolder support
        if safe_folder_path:
            # Create the subfolder path within the output directory
            full_output_dir = os.path.join(output_dir, safe_folder_path.replace("/", os.sep))
        else:
            full_output_dir = output_dir
        
        # Ensure directory exists (creates all intermediate directories)
        os.makedirs(full_output_dir, exist_ok=True)
        file_path = os.path.join(full_output_dir, filename)

        # Convert to PIL and embed metadata
        pil_image = _to_pil(image)
        pnginfo = PngImagePlugin.PngInfo()
        
        # Embed our compact JSON under custom key
        pnginfo.add_text("vt_json", meta_json)
        
        # Add A1111 format 'parameters' field for external site compatibility
        pnginfo.add_text("parameters", a1111_params)
        
        # Additional metadata that some sites may look for
        # Add individual resource info for better site compatibility
        model_name = model_info.get("name")
        if model_name:
            pnginfo.add_text("model_name", str(model_name))
        model_hash = model_info.get("hash") 
        if model_hash:
            pnginfo.add_text("model_hash", str(model_hash))  # Full hash for Civitai lookup
        
        # Add LoRA info in multiple formats for better site recognition
        if loras:
            # JSON array format for programmatic access
            loras_json = json.dumps(loras, separators=(",", ":"))
            pnginfo.add_text("loras", loras_json)
            
            # Simple LoRA names list
            lora_names = [lora.get("filename", lora.get("name", "")) for lora in loras if lora.get("name")]
            if lora_names:
                pnginfo.add_text("lora_names", ", ".join(lora_names))

        # Save PNG with metadata
        pil_image.save(file_path, format="PNG", pnginfo=pnginfo, optimize=True)

        print(f"🧜‍♀️ Save Siren: Saved {filename} ({os.path.getsize(file_path)} bytes)")
        
        # Return A1111 format metadata for node output (same as what we save)
        return (a1111_params,)


# Node registration
NODE_CLASS_MAPPINGS = {"SaveSiren": SaveSiren}
NODE_DISPLAY_NAME_MAPPINGS = {"SaveSiren": "🧜‍♀️ Save Siren"}