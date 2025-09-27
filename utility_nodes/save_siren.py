# -*- coding: utf-8 -*-
"""
🧜‍♀️ Save Siren — Violet Tools Utility Node

Purpose: Attach a compact, standardized JSON metadata blob to PNG outputs without
leaking full ComfyUI workflow graphs. Also emits the JSON for downstream nodes
(e.g., Save Image Extended) to consume.

Inputs
- image: IMAGE (required)
- ckpt_name: STRING (socket only)
- positive: STRING (multiline, socket only)
- negative: STRING (multiline, socket only)
- cfg_scale: FLOAT (socket only)
- sampler: STRING (socket only)
- steps: INT (socket only)
- seed: INT (socket only)
- is_adetailer: BOOLEAN
- loras: STRING (JSON list of {lora, weight, civitai_model_id}) (socket only)
- civitai_model_ids: STRING (JSON list of ints) (socket only)
- save_image: BOOLEAN (default True)
- human_readable_text_chunks: BOOLEAN (default True)

Outputs
- image: passthrough IMAGE
- metadata: STRING (metadata JSON)

Notes
- Pillow (PIL) is expected to be available in ComfyUI runtime.
- If `save_image==True`, writes PNG text chunks using Mini Meta Mapper.
"""

from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional

# Import the mini meta mapper helper dynamically
try:
    import importlib.util
    _pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _mmm_path = os.path.join(_pkg_root, 'node_resources', 'mini-meta-mapper.py')
    _spec = importlib.util.spec_from_file_location('vt_mini_meta_mapper', _mmm_path)
    if _spec and _spec.loader:
        vt_mmm = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(vt_mmm)  # type: ignore
    else:
        vt_mmm = None
except Exception:
    vt_mmm = None


class SaveSiren:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"forceInput": True}),
                "save_image": ("BOOLEAN", {"default": True, "tooltip": "Write compact metadata into PNG chunks"}),
                "human_readable_text_chunks": ("BOOLEAN", {"default": True, "tooltip": "Also write Prompt/Steps/etc. text chunks"}),
            },
            "optional": {
                # Socket-only parameters (no inline widgets); play nice with cg-use-everywhere
                "ckpt_name": ("STRING", {"forceInput": True, "defaultInput": True, "multiline": False}),
                "positive": ("STRING", {"forceInput": True, "defaultInput": True, "multiline": True}),
                "negative": ("STRING", {"forceInput": True, "defaultInput": True, "multiline": True}),
                "cfg_scale": ("FLOAT", {"forceInput": True}),
                "sampler": ("STRING", {"forceInput": True, "defaultInput": True, "multiline": False}),
                "steps": ("INT", {"forceInput": True}),
                # Prevent ComfyUI seed widget: socket-only INT input, no default/min/max UI
                "seed": ("INT", {"forceInput": True}),
                "is_adetailer": ("BOOLEAN", {"forceInput": True}),
                "loras": ("STRING", {"forceInput": True, "defaultInput": True, "multiline": True, "tooltip": "JSON list: [{\"lora\":\"name\", \"weight\":0.8, \"civitai_model_id\":123}]"}),
                "civitai_model_ids": ("STRING", {"forceInput": True, "defaultInput": True, "multiline": False, "tooltip": "JSON list of integers"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "metadata")
    FUNCTION = "save"
    CATEGORY = "Violet Tools 💅/Utility"

    def _infer_dimensions(self, image) -> tuple[Optional[int], Optional[int]]:
        # Try PIL path first
        try:
            from PIL import Image as PILImage  # type: ignore
            if hasattr(image, 'to_pil'):
                pil = image.to_pil()
                if isinstance(pil, PILImage.Image):
                    w, h = pil.size
                    return int(w), int(h)
            if isinstance(image, PILImage.Image):
                w, h = image.size
                return int(w), int(h)
        except Exception:
            pass
        # Try numpy / tensor shapes
        try:
            import numpy as np  # type: ignore
            arr = image
            if isinstance(arr, (list, tuple)) and arr:
                arr = arr[0]
            if hasattr(arr, 'shape'):
                shp = tuple(int(x) for x in arr.shape)
                if len(shp) == 4:
                    # Assume (B, H, W, C)
                    return shp[2], shp[1]
                if len(shp) == 3:
                    # Assume (H, W, C)
                    return shp[1], shp[0]
        except Exception:
            pass
        return None, None

    def _to_meta(self, image=None, **kwargs) -> Dict[str, Any]:
        if vt_mmm and hasattr(vt_mmm, 'build_meta'):
            try:
                # Parse JSON fields
                loras = json.loads(kwargs.get('loras') or '[]')
                civitai_ids = json.loads(kwargs.get('civitai_model_ids') or '[]')
            except json.JSONDecodeError:
                loras, civitai_ids = [], []
            # Auto-infer width/height from image if not explicitly provided
            w, h = self._infer_dimensions(image)
            return vt_mmm.build_meta(
                model_name=kwargs.get('ckpt_name') or None,
                prompt=kwargs.get('positive') or None,
                negative_prompt=kwargs.get('negative') or None,
                width=w,
                height=h,
                cfg_scale=(
                    (lambda v: (float(str(v)) if (v is not None and str(v).strip() != "") else None))(kwargs.get('cfg_scale'))
                ),
                sampler=kwargs.get('sampler') or None,
                steps=(int(kwargs.get('steps')) if kwargs.get('steps') is not None else None),
                seed=(int(kwargs.get('seed')) if kwargs.get('seed') is not None else None),
                is_adetailer=(bool(kwargs.get('is_adetailer')) if kwargs.get('is_adetailer') is not None else None),
                loras=loras or None,
                civitai_model_ids=civitai_ids or None,
            )
        # Minimal fallback if helper missing
        w, h = self._infer_dimensions(image)
        meta = {
            "model_name": kwargs.get('ckpt_name') or None,
            "prompt": kwargs.get('positive') or None,
            "negative_prompt": kwargs.get('negative') or None,
            "width": w,
            "height": h,
            "cfg_scale": (float(kwargs.get('cfg_scale')) if kwargs.get('cfg_scale') is not None else None),
            "sampler": kwargs.get('sampler') or None,
            "steps": (int(kwargs.get('steps')) if kwargs.get('steps') is not None else None),
            "seed": (int(kwargs.get('seed')) if kwargs.get('seed') is not None else None),
            "is_adetailer": (bool(kwargs.get('is_adetailer')) if kwargs.get('is_adetailer') is not None else None),
        }
        if w and h:
            meta["size"] = f"{w}x{h}"
        # Strip None
        return {k: v for k, v in meta.items() if v is not None}

    def _write_png_chunks(self, image, meta: Dict[str, Any], human_readable: bool):
        # Attempt non-destructive save into metadata if PIL is around and image has the correct backend
        try:
            from PIL import Image as PILImage  # type: ignore
        except Exception:
            return image  # PIL missing; skip

        # ComfyUI IMAGE is typically a tensor-like object. We'll try best-effort conversion.
        # If `image` already carries a PIL Image in first element (e.g., from Load Image), reuse it.
        pil = None
        try:
            # Common pattern: image is a dict or list with 'pil' or direct PIL object
            if hasattr(image, 'to_pil'):
                pil = image.to_pil()
            elif isinstance(image, PILImage.Image):
                pil = image
        except Exception:
            pil = None

        if pil is None:
            # Last resort: attempt to extract from numpy if present
            try:
                import numpy as np  # type: ignore
                if isinstance(image, np.ndarray):
                    pil = PILImage.fromarray(image)
            except Exception:
                pil = None

        if pil is None:
            # If we cannot access PIL image representation, we skip embedding but still return pass-through
            return image

        try:
            if vt_mmm and hasattr(vt_mmm, 'add_png_text_chunks'):
                vt_mmm.add_png_text_chunks(pil, meta, human_readable=human_readable)
            # We won't write to disk here; this utility's role is to attach metadata for downstream save nodes.
            # Some downstream nodes (like Save Image Extended) can accept metadata dicts directly; we surface JSON instead.
        except Exception:
            pass
        return image

    def save(self,
             image,
             save_image: bool,
             human_readable_text_chunks: bool,
             ckpt_name: Optional[str] = None,
             positive: Optional[str] = None,
             negative: Optional[str] = None,
             cfg_scale: Optional[float] = None,
             sampler: Optional[str] = None,
             steps: Optional[int] = None,
             seed: Optional[int] = None,
             is_adetailer: Optional[bool] = None,
             loras: Optional[str] = None,
             civitai_model_ids: Optional[str] = None):
        # Build compact metadata JSON
        meta = self._to_meta(
            image=image,
            ckpt_name=ckpt_name,
            positive=positive,
            negative=negative,
            cfg_scale=cfg_scale,
            sampler=sampler,
            steps=steps,
            seed=seed,
            is_adetailer=is_adetailer,
            loras=loras,
            civitai_model_ids=civitai_model_ids,
        )
        json_str = json.dumps(meta, ensure_ascii=False)

        # Optionally attach text chunks (best effort) — pass-through image regardless
        if save_image:
            image = self._write_png_chunks(image, meta, human_readable_text_chunks)

        return (image, json_str)


NODE_CLASS_MAPPINGS = {
    "SaveSiren": SaveSiren,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveSiren": "🧜‍♀️ Save Siren",
}
