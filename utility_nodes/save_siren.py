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

def _extract_model_info(model_obj: Any) -> Dict[str, Optional[str]]:
    """
    Extract model name and hash from ComfyUI MODEL object.
    Handles various ComfyUI model object structures.
    """
    if model_obj is None:
        return {"name": None, "hash": None}
    
    name = None
    model_hash = None
    
    try:
        # Debug: Print model object structure (remove this after debugging)
        print(f"🧜‍♀️ Save Siren Debug: Model object type: {type(model_obj)}")
        print(f"🧜‍♀️ Save Siren Debug: Model object attrs: {[attr for attr in dir(model_obj) if not attr.startswith('_')][:15]}")
        
        # Method 0: Try ComfyUI's checkpoint state manager (most direct approach)
        try:
            import comfy.sd
            if hasattr(comfy.sd, 'current_checkpoint') and comfy.sd.current_checkpoint:
                checkpoint_info = comfy.sd.current_checkpoint
                print(f"🧜‍♀️ Save Siren Debug: Found current_checkpoint: {checkpoint_info}")
                if isinstance(checkpoint_info, str):
                    name = _extract_model_name(checkpoint_info)
                    if os.path.exists(checkpoint_info):
                        model_hash = _get_file_hash(checkpoint_info)
                        print(f"🧜‍♀️ Save Siren Debug: Found via checkpoint state: {name}")
                elif hasattr(checkpoint_info, 'filename'):
                    name = _extract_model_name(checkpoint_info.filename)
                    if os.path.exists(checkpoint_info.filename):
                        model_hash = _get_file_hash(checkpoint_info.filename)
                        print(f"🧜‍♀️ Save Siren Debug: Found via checkpoint.filename: {name}")
        except ImportError:
            print("🧜‍♀️ Save Siren Debug: comfy.sd not available")
        except Exception as e:
            print(f"🧜‍♀️ Save Siren Debug: checkpoint state error: {e}")
        
        # Method 0b: Try model_management module
        if not name:
            try:
                import comfy.model_management
                # Some versions store checkpoint info in model_management
                if hasattr(comfy.model_management, 'current_loaded_model'):
                    current_model = comfy.model_management.current_loaded_model
                    print(f"🧜‍♀️ Save Siren Debug: current_loaded_model type: {type(current_model)}")
                    if hasattr(current_model, 'model_path'):
                        model_path = current_model.model_path
                        if model_path and os.path.exists(model_path):
                            name = _extract_model_name(model_path)
                            model_hash = _get_file_hash(model_path)
                            print(f"🧜‍♀️ Save Siren Debug: Found via model_management: {name}")
            except ImportError:
                print("🧜‍♀️ Save Siren Debug: comfy.model_management not available")
            except Exception as e:
                print(f"🧜‍♀️ Save Siren Debug: model_management error: {e}")
        
        # Method 0c: Try folder_paths checkpoint tracking
        if not name:
            try:
                import folder_paths
                # Sometimes ComfyUI stores recently used checkpoints
                if hasattr(folder_paths, 'folder_names_and_paths'):
                    checkpoints_info = folder_paths.folder_names_and_paths.get('checkpoints', None)
                    print(f"🧜‍♀️ Save Siren Debug: checkpoints folder info: {checkpoints_info}")
                
                # Try to get the currently loaded model files
                if hasattr(folder_paths, 'get_filename_list'):
                    try:
                        checkpoint_files = folder_paths.get_filename_list('checkpoints')
                        print(f"🧜‍♀️ Save Siren Debug: available checkpoints: {checkpoint_files[:5]}...")  # First 5 only
                    except Exception as e:
                        print(f"🧜‍♀️ Save Siren Debug: get_filename_list error: {e}")
                        
            except ImportError:
                print("🧜‍♀️ Save Siren Debug: folder_paths not available")
            except Exception as e:
                print(f"🧜‍♀️ Save Siren Debug: folder_paths error: {e}")
        
        # Method 0d: Try to inspect the ModelPatcher's model_state_dict or backup for hints
        if not name and type(model_obj).__name__ == 'ModelPatcher':
            try:
                # Sometimes the model path is in backup info
                if hasattr(model_obj, 'backup') and model_obj.backup:
                    print(f"🧜‍♀️ Save Siren Debug: ModelPatcher.backup type: {type(model_obj.backup)}")
                    if hasattr(model_obj.backup, 'items'):
                        backup_keys = list(model_obj.backup.keys())[:10]  # First 10 keys only
                        print(f"🧜‍♀️ Save Siren Debug: backup keys sample: {backup_keys}")
                
                # Check if there are any string attributes that might contain paths
                all_attrs = [attr for attr in dir(model_obj) if not attr.startswith('_')]
                for attr_name in all_attrs:
                    try:
                        attr_value = getattr(model_obj, attr_name)
                        if isinstance(attr_value, str) and ('.safetensors' in attr_value or '.ckpt' in attr_value or '.pt' in attr_value):
                            print(f"🧜‍♀️ Save Siren Debug: Found model file reference in {attr_name}: {attr_value}")
                            if os.path.exists(attr_value):
                                name = _extract_model_name(attr_value)
                                model_hash = _get_file_hash(attr_value)
                                print(f"🧜‍♀️ Save Siren Debug: Found model via string scan: {name}")
                                break
                    except:
                        continue
                        
            except Exception as e:
                print(f"🧜‍♀️ Save Siren Debug: ModelPatcher inspection error: {e}")
        if type(model_obj).__name__ == 'ModelPatcher':
            print(f"🧜‍♀️ Save Siren Debug: ModelPatcher-specific attrs: {[attr for attr in dir(model_obj) if 'model' in attr.lower() or 'path' in attr.lower() or 'file' in attr.lower() or 'ckpt' in attr.lower()]}")
            if hasattr(model_obj, 'model_options'):
                print(f"🧜‍♀️ Save Siren Debug: model_options = {model_obj.model_options}")
            if hasattr(model_obj, 'model_config'):
                print("🧜‍♀️ Save Siren Debug: has model_config")
            if hasattr(model_obj, 'model'):
                print("🧜‍♀️ Save Siren Debug: has model attribute")
                # Let's explore the nested model object
                model_inner = model_obj.model
                print(f"🧜‍♀️ Save Siren Debug: Inner model type: {type(model_inner)}")
                print(f"🧜‍♀️ Save Siren Debug: Inner model attrs: {[attr for attr in dir(model_inner) if not attr.startswith('_')][:15]}")
                
                # Check if inner model has current_patcher that might lead back to path info
                if hasattr(model_inner, 'current_patcher') and model_inner.current_patcher:
                    patcher = model_inner.current_patcher
                    print(f"🧜‍♀️ Save Siren Debug: Found current_patcher: {type(patcher)}")
                    if hasattr(patcher, 'filename') or hasattr(patcher, 'model_path'):
                        path = getattr(patcher, 'filename', None) or getattr(patcher, 'model_path', None)
                        if path and os.path.exists(path):
                            name = _extract_model_name(path)
                            model_hash = _get_file_hash(path)
                            print(f"🧜‍♀️ Save Siren Debug: Found via current_patcher: {name}")
                
                # Look for path-related attributes in inner model
                path_attrs = [attr for attr in dir(model_inner) if 'path' in attr.lower() or 'file' in attr.lower() or 'ckpt' in attr.lower()]
                if path_attrs:
                    print(f"🧜‍♀️ Save Siren Debug: Inner model path attrs: {path_attrs}")
                    for attr in path_attrs:
                        try:
                            value = getattr(model_inner, attr)
                            print(f"🧜‍♀️ Save Siren Debug: Inner model.{attr} = {value}")
                        except:
                            pass
            
            # Also check if ModelPatcher itself has any direct path attributes
            all_attrs = [attr for attr in dir(model_obj) if not attr.startswith('_')]
            path_attrs = [attr for attr in all_attrs if 'path' in attr.lower() or 'file' in attr.lower() or 'ckpt' in attr.lower() or 'checkpoint' in attr.lower()]
            if path_attrs:
                print(f"🧜‍♀️ Save Siren Debug: ModelPatcher path attrs: {path_attrs}")
                for attr in path_attrs:
                    try:
                        value = getattr(model_obj, attr)
                        print(f"🧜‍♀️ Save Siren Debug: ModelPatcher.{attr} = {value}")
                    except:
                        pass
        
        # Method 1: Try model.model.model_config.unet_config approach
        if hasattr(model_obj, 'model') and hasattr(model_obj.model, 'model_config'):
            config = model_obj.model.model_config
            if hasattr(config, 'unet_config') and hasattr(config.unet_config, 'model_path'):
                model_path = config.unet_config.model_path
                if model_path and os.path.exists(model_path):
                    name = _extract_model_name(model_path)
                    model_hash = _get_file_hash(model_path)
                    print(f"🧜‍♀️ Save Siren Debug: Found via method 1: {name}")
        
        # Method 2: Try ModelPatcher pattern (very common in ComfyUI)
        if not name and hasattr(model_obj, 'model_patcher'):
            patcher = model_obj.model_patcher
            print(f"🧜‍♀️ Save Siren Debug: Found model_patcher, attrs: {[attr for attr in dir(patcher) if not attr.startswith('_')][:10]}")
            # Check for model_options dict
            if hasattr(patcher, 'model_options') and isinstance(patcher.model_options, dict):
                print(f"🧜‍♀️ Save Siren Debug: model_options keys: {list(patcher.model_options.keys())}")
                model_path = patcher.model_options.get('model_path')
                if model_path and os.path.exists(model_path):
                    name = _extract_model_name(model_path)
                    model_hash = _get_file_hash(model_path)
                    print(f"🧜‍♀️ Save Siren Debug: Found via method 2: {name}")
        
        # Method 2b: The model object IS the ModelPatcher (direct case)
        if not name and type(model_obj).__name__ == 'ModelPatcher':
            print(f"🧜‍♀️ Save Siren Debug: Model object IS ModelPatcher, checking for model path...")
            # Check if ModelPatcher has model_options
            if hasattr(model_obj, 'model_options') and isinstance(model_obj.model_options, dict):
                print(f"🧜‍♀️ Save Siren Debug: ModelPatcher.model_options keys: {list(model_obj.model_options.keys())}")
                model_path = model_obj.model_options.get('model_path')
                if model_path:
                    print(f"🧜‍♀️ Save Siren Debug: Found model_path: {model_path}")
                    if os.path.exists(model_path):
                        name = _extract_model_name(model_path)
                        model_hash = _get_file_hash(model_path)
                        print(f"🧜‍♀️ Save Siren Debug: Found via method 2b: {name}")
                    else:
                        print(f"🧜‍♀️ Save Siren Debug: model_path does not exist: {model_path}")
            
            # Also try folder_paths approach for ModelPatcher
            if not name:
                try:
                    import folder_paths
                    # ModelPatcher might store just the filename, need to resolve full path
                    if hasattr(model_obj, 'model_options'):
                        model_opts = model_obj.model_options
                        # Try different keys that might contain the model file
                        for key in ['model_path', 'ckpt_name', 'checkpoint', 'filename']:
                            if key in model_opts and model_opts[key]:
                                model_file = model_opts[key]
                                print(f"🧜‍♀️ Save Siren Debug: Trying key '{key}': {model_file}")
                                # If it's just a filename, try to resolve full path
                                if not os.path.isabs(model_file):
                                    full_path = folder_paths.get_full_path("checkpoints", model_file)
                                    if full_path and os.path.exists(full_path):
                                        name = _extract_model_name(full_path)
                                        model_hash = _get_file_hash(full_path)
                                        print(f"🧜‍♀️ Save Siren Debug: Found via folder_paths resolution: {name}")
                                        break
                                else:
                                    if os.path.exists(model_file):
                                        name = _extract_model_name(model_file)
                                        model_hash = _get_file_hash(model_file)
                                        print(f"🧜‍♀️ Save Siren Debug: Found via absolute path: {name}")
                                        break
                except ImportError:
                    print("🧜‍♀️ Save Siren Debug: folder_paths not available")
                except Exception as e:
                    print(f"🧜‍♀️ Save Siren Debug: folder_paths resolution error: {e}")
        
        # Method 3: Try direct model patcher approach
        if not name and hasattr(model_obj, 'model') and hasattr(model_obj.model, 'model_patcher'):
            patcher = model_obj.model.model_patcher
            if hasattr(patcher, 'model_options') and isinstance(patcher.model_options, dict):
                model_path = patcher.model_options.get('model_path')
                if model_path and os.path.exists(model_path):
                    name = _extract_model_name(model_path)
                    model_hash = _get_file_hash(model_path)
                    print(f"🧜‍♀️ Save Siren Debug: Found via method 3: {name}")
        
        # Method 3b: Check inner model object for path attributes
        if not name and hasattr(model_obj, 'model'):
            inner_model = model_obj.model
            # Check common path attributes on inner model
            for attr_name in ['model_path', 'checkpoint_path', 'ckpt_path', 'file_path', 'path']:
                if hasattr(inner_model, attr_name):
                    model_path = getattr(inner_model, attr_name)
                    if model_path and isinstance(model_path, str) and os.path.exists(model_path):
                        name = _extract_model_name(model_path)
                        model_hash = _get_file_hash(model_path)
                        print(f"🧜‍♀️ Save Siren Debug: Found via method 3b ({attr_name}): {name}")
                        break
        
        # Method 4: Look for checkpoint_path attribute (another pattern)
        if not name:
            for attr_path in ['checkpoint_path', 'model_path', 'ckpt_path']:
                if hasattr(model_obj, attr_path):
                    model_path = getattr(model_obj, attr_path)
                    if model_path and os.path.exists(model_path):
                        name = _extract_model_name(model_path)
                        model_hash = _get_file_hash(model_path)
                        print(f"🧜‍♀️ Save Siren Debug: Found via method 4 ({attr_path}): {name}")
                        break
        
        # Method 5: Deep search through model object structure
        if not name:
            model_path = _deep_search_for_model_path(model_obj)
            if model_path and os.path.exists(model_path):
                name = _extract_model_name(model_path)
                model_hash = _get_file_hash(model_path)
                print(f"🧜‍♀️ Save Siren Debug: Found via method 5 (deep search): {name}")
                        
    except Exception as e:
        # Debug: Print the exception
        print(f"🧜‍♀️ Save Siren Debug: Model extraction error: {e}")
    
    if not name:
        print("🧜‍♀️ Save Siren Debug: No model name found - all methods failed")
    
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
        import json  # Import at function level to avoid lint issues
        import datetime
        
        # Extract image dimensions
        w, h = _shape_wh(image)
        size_str = f"{w}x{h}" if (w and h) else None
        
        # Extract model info with fallback to execution context scanning
        model_info = _extract_model_info(model)
        
        # If model extraction failed, try to get it from global ComfyUI context
        if model_info.get("name") is None:
            try:
                # Try to access execution context for model references
                import sys
                if hasattr(sys.modules.get('execution', None), 'current_execution') or hasattr(sys.modules.get('execution', None), 'last_execution'):
                    print("🧜‍♀️ Save Siren Debug: Found execution module, checking for model references")
                
                # Alternative: scan all modules for recent checkpoint loading
                for module_name in ['model_management', 'sd', 'checkpoint_state', 'execution']:
                    full_name = f"comfy.{module_name}"
                    if full_name in sys.modules:
                        module = sys.modules[full_name]
                        print(f"🧜‍♀️ Save Siren Debug: Found {full_name}, attrs: {[a for a in dir(module) if 'model' in a.lower() or 'checkpoint' in a.lower()]}")
                        
                        # Special handling for model_management module
                        if module_name == 'model_management':
                            try:
                                # Check current_loaded_models
                                if hasattr(module, 'current_loaded_models') and module.current_loaded_models:
                                    loaded_models = module.current_loaded_models
                                    print(f"🧜‍♀️ Save Siren Debug: === Analyzing {len(loaded_models)} LoadedModel objects ===")
                                    
                                    # First, let's categorize what types of models we have
                                    model_types = {}
                                    for i, loaded_model in enumerate(loaded_models):
                                        if hasattr(loaded_model, 'model') and loaded_model.model:
                                            model_patch = loaded_model.model
                                            model_type = str(type(model_patch))
                                            if model_type not in model_types:
                                                model_types[model_type] = []
                                            model_types[model_type].append((i, loaded_model))
                                    
                                    print(f"🧜‍♀️ Save Siren Debug: Model types found: {list(model_types.keys())}")
                                    
                                    # Now examine each LoadedModel in detail
                                    for i, loaded_model in enumerate(loaded_models):
                                        print(f"🧜‍♀️ Save Siren Debug: === LoadedModel[{i}] ===")
                                        print(f"  Type: {type(loaded_model)}")
                                        print(f"  Currently used: {getattr(loaded_model, 'currently_used', 'unknown')}")
                                        
                                        if hasattr(loaded_model, 'model') and loaded_model.model:
                                            model_patch = loaded_model.model
                                            print(f"  Model type: {type(model_patch)}")
                                            
                                            # Check if this is our target model
                                            is_target_model = model_patch is model
                                            print(f"  Is target model: {is_target_model}")
                                            
                                            # Look for model path in model options
                                            if hasattr(model_patch, 'model_options') and isinstance(model_patch.model_options, dict):
                                                opts = model_patch.model_options
                                                print(f"  Model options keys: {list(opts.keys())}")
                                                
                                                if 'model_path' in opts and opts['model_path']:
                                                    model_path = opts['model_path']
                                                    print(f"  Found model_path: {model_path}")
                                                    if os.path.exists(model_path):
                                                        # Use this model regardless of target match since we need a model
                                                        model_info["name"] = _extract_model_name(model_path)
                                                        model_info["hash"] = _get_file_hash(model_path)
                                                        print(f"  *** Using model: {model_info['name']} (target={is_target_model}) ***")
                                            
                                            # Check for patches (where LoRAs usually live) - check all models
                                            if hasattr(model_patch, 'patches') and model_patch.patches:
                                                print(f"  Has patches: {len(model_patch.patches)} items")
                                                for patch_key in list(model_patch.patches.keys())[:5]:  # Show first 5
                                                    patch_data = model_patch.patches[patch_key]
                                                    print(f"    Patch key: {patch_key} -> {type(patch_data)}")
                                                    if hasattr(patch_data, '__len__') and len(patch_data) > 0:
                                                        print(f"      Patch data sample: {str(patch_data)[:100]}...")
                                            
                                            # Check additional_models (LoRAs often stored here) - check all models
                                            if hasattr(model_patch, 'additional_models') and model_patch.additional_models:
                                                print(f"  Additional models: {len(model_patch.additional_models)} items")
                                                lora_list = []  # Create local list for LoRAs
                                                for add_key, add_model in model_patch.additional_models.items():
                                                    print(f"    Additional: {add_key} -> {type(add_model)}")
                                                    # Check if additional model has path info
                                                    if hasattr(add_model, 'model_path'):
                                                        add_path = add_model.model_path
                                                        print(f"      Additional model path: {add_path}")
                                                        if 'lora' in str(add_path).lower():
                                                            lora_name = _extract_model_name(add_path)
                                                            print(f"      *** Found LoRA: {lora_name} ***")
                                                            lora_list.append({
                                                                'name': lora_name,
                                                                'hash': _get_file_hash(add_path) if os.path.exists(add_path) else None
                                                            })
                                                
                                                # Add LoRA list to model_info if we found any
                                                if lora_list:
                                                    # Store as JSON string to match metadata format
                                                    import json
                                                    model_info['loras_json'] = json.dumps(lora_list)
                                                    print(f"      Added {len(lora_list)} LoRAs to metadata")
                                            else:
                                                print(f"  No additional_models found")
                                            
                                            # Also check for direct model path attributes on ModelPatcher
                                            path_attrs = [attr for attr in dir(model_patch) if 'path' in attr.lower() or 'file' in attr.lower()]
                                            if path_attrs:
                                                print(f"  Path-related attrs: {path_attrs}")
                                                for attr in path_attrs:
                                                    try:
                                                        value = getattr(model_patch, attr)
                                                        if isinstance(value, str) and any(ext in value for ext in ['.safetensors', '.ckpt', '.pt']):
                                                            print(f"    {attr}: {value}")
                                                            if os.path.exists(value) and not model_info.get("name"):
                                                                model_info["name"] = _extract_model_name(value)
                                                                model_info["hash"] = _get_file_hash(value)
                                                                print(f"    *** Using model from {attr}: {model_info['name']} ***")
                                                    except:
                                                        pass
                                            
                                            # Check for LoRA-specific attributes
                                            lora_attrs = [attr for attr in dir(model_patch) if 'lora' in attr.lower()]
                                            if lora_attrs:
                                                print(f"  LoRA-related attrs: {lora_attrs}")
                                                for attr in lora_attrs:
                                                    try:
                                                        value = getattr(model_patch, attr)
                                                        if value:
                                                            print(f"    {attr}: {str(value)[:100]}...")
                                                    except:
                                                        pass
                                        print()
                                    
                                    if model_info.get("name"):
                                        print(f"🧜‍♀️ Save Siren Debug: Successfully extracted model: {model_info['name']}")
                                        if 'loras_json' in model_info:
                                            loras_json = model_info['loras_json']
                                            if loras_json:
                                                loras = json.loads(loras_json)
                                                print(f"🧜‍♀️ Save Siren Debug: Found {len(loras)} LoRAs: {[l['name'] for l in loras]}")
                                    
                                    # Additional debug: inspect our target model directly
                                    print(f"🧜‍♀️ Save Siren Debug: === Direct Target Model Inspection ===")
                                    print(f"  Target model type: {type(model)}")
                                    print(f"  Target model id: {id(model)}")
                                    for lm in loaded_models:
                                        if hasattr(lm, 'model'):
                                            print(f"  LoadedModel.model id: {id(lm.model)} (match: {lm.model is model})")
                                    
                                    # Check if target model has patches or additional_models directly
                                    if hasattr(model, 'patches') and model.patches:
                                        print(f"  Target has {len(model.patches)} patches")
                                    if hasattr(model, 'additional_models') and model.additional_models:
                                        print(f"  Target has {len(model.additional_models)} additional_models")
                                        for add_key, add_model in model.additional_models.items():
                                            print(f"    Target additional: {add_key} -> {type(add_model)}")
                                            if hasattr(add_model, 'model_path'):
                                                print(f"      Target additional path: {add_model.model_path}")
                                    print()
                            except Exception as e:
                                print(f"🧜‍♀️ Save Siren Debug: model_management scanning error: {e}")
                                import traceback
                                traceback.print_exc()
                                
                                # Check loaded_models if current_loaded_models didn't work
                                if not model_info.get("name") and hasattr(module, 'loaded_models') and module.loaded_models:
                                    loaded_models = module.loaded_models
                                    print(f"🧜‍♀️ Save Siren Debug: loaded_models: {loaded_models}")
                                    # Try to get the most recently loaded model
                                    if isinstance(loaded_models, list) and loaded_models:
                                        recent_model = loaded_models[-1]  # Last loaded
                                        print(f"🧜‍♀️ Save Siren Debug: recent_model type: {type(recent_model)}")
                                        if hasattr(recent_model, 'model_path') or hasattr(recent_model, 'filename'):
                                            path = getattr(recent_model, 'model_path', None) or getattr(recent_model, 'filename', None)
                                            if path and os.path.exists(path):
                                                model_info["name"] = _extract_model_name(path)
                                                model_info["hash"] = _get_file_hash(path)
                                                print(f"🧜‍♀️ Save Siren Debug: Found model via loaded_models: {model_info['name']}")
                                                break
                            except Exception as e:
                                print(f"🧜‍♀️ Save Siren Debug: model_management scanning error: {e}")
                        
                        # Look for any checkpoint or model path attributes in other modules
                        for attr in dir(module):
                            if any(keyword in attr.lower() for keyword in ['checkpoint', 'model_path', 'current_model', 'loaded_model']):
                                try:
                                    value = getattr(module, attr)
                                    if isinstance(value, str) and any(ext in value for ext in ['.safetensors', '.ckpt', '.pt']):
                                        print(f"🧜‍♀️ Save Siren Debug: Found model path in {full_name}.{attr}: {value}")
                                        if os.path.exists(value):
                                            model_info["name"] = _extract_model_name(value)
                                            model_info["hash"] = _get_file_hash(value)
                                            break
                                except:
                                    continue
                        if model_info.get("name"):
                            break
                            
                # Final attempt: Use folder_paths to check for recently accessed checkpoints
                if not model_info.get("name"):
                    try:
                        import folder_paths
                        # Get list of available checkpoints and try to match with current model object
                        checkpoint_files = folder_paths.get_filename_list('checkpoints')
                        if checkpoint_files:
                            # Try to correlate with model object properties
                            # This is a heuristic - take the first checkpoint as fallback
                            # (In a real workflow, the user would know which one they loaded)
                            first_checkpoint = checkpoint_files[0]
                            full_path = folder_paths.get_full_path('checkpoints', first_checkpoint)
                            if full_path and os.path.exists(full_path):
                                model_info["name"] = _extract_model_name(full_path)
                                model_info["hash"] = _get_file_hash(full_path)
                                print(f"🧜‍♀️ Save Siren Debug: Fallback to first checkpoint: {model_info['name']} (may not be accurate)")
                    except Exception as e:
                        print(f"🧜‍♀️ Save Siren Debug: folder_paths fallback error: {e}")
                        
            except Exception as e:
                print(f"🧜‍♀️ Save Siren Debug: execution context scan error: {e}")
        
        # Build compact metadata payload
        payload = {}
        
        # Process LoRA info if present
        if 'loras_json' in model_info and model_info['loras_json']:
            try:
                loras_data = json.loads(model_info['loras_json'])
                # Add LoRAs as separate field in model_info
                model_info['loras'] = loras_data
                # Remove the temporary JSON field
                del model_info['loras_json']
            except:
                # If parsing fails, just remove the temp field
                if 'loras_json' in model_info:
                    del model_info['loras_json']
        
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
