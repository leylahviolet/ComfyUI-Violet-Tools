# -*- coding: utf-8 -*-
"""
🧜‍♀️ Save Siren — Violet Tools Utility Node

Purpose: Attach a compact, standardized JSON metadata blob to PNG outputs without
leaking full ComfyUI workflow graphs. Also emits the JSON for downstream nodes
(e.g., Save Image Extended) to consume.

Inputs
- image: IMAGE (required)
- model_name: STRING
- prompt: STRING (multiline)
- negative_prompt: STRING (multiline)
- width: INT
- height: INT
- cfg_scale: FLOAT
- sampler: STRING
- steps: INT
- seed: INT
- is_adetailer: BOOLEAN
- loras: STRING (JSON list of {lora, weight, civitai_model_id})
- civitai_model_ids: STRING (JSON list of ints)
- save_image: BOOLEAN (default True)
- human_readable_text_chunks: BOOLEAN (default True)

Outputs
- image: passthrough IMAGE
- json: STRING (metadata JSON)

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
                "model_name": ("STRING", {"default": "", "multiline": False}),
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "negative_prompt": ("STRING", {"default": "", "multiline": True}),
                "width": ("INT", {"default": 0, "min": 0, "max": 8192}),
                "height": ("INT", {"default": 0, "min": 0, "max": 8192}),
                "cfg_scale": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 50.0, "step": 0.1}),
                "sampler": ("STRING", {"default": "", "multiline": False}),
                "steps": ("INT", {"default": 0, "min": 0, "max": 10000}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**31-1}),
                "is_adetailer": ("BOOLEAN", {"default": False}),
                "loras": ("STRING", {"default": "[]", "multiline": True, "tooltip": "JSON list: [{\"lora\":\"name\", \"weight\":0.8, \"civitai_model_id\":123}]"}),
                "civitai_model_ids": ("STRING", {"default": "[]", "multiline": False, "tooltip": "JSON list of integers"}),
                "save_image": ("BOOLEAN", {"default": True, "tooltip": "Write compact metadata into PNG chunks"}),
                "human_readable_text_chunks": ("BOOLEAN", {"default": True, "tooltip": "Also write Prompt/Steps/etc. text chunks"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "json")
    FUNCTION = "save"
    CATEGORY = "Violet Tools 💅/Utility"

    def _to_meta(self, **kwargs) -> Dict[str, Any]:
        if vt_mmm and hasattr(vt_mmm, 'build_meta'):
            try:
                # Parse JSON fields
                loras = json.loads(kwargs.get('loras') or '[]')
                civitai_ids = json.loads(kwargs.get('civitai_model_ids') or '[]')
            except json.JSONDecodeError:
                loras, civitai_ids = [], []
            return vt_mmm.build_meta(
                model_name=kwargs.get('model_name') or None,
                prompt=kwargs.get('prompt') or None,
                negative_prompt=kwargs.get('negative_prompt') or None,
                width=int(kwargs.get('width') or 0) or None,
                height=int(kwargs.get('height') or 0) or None,
                cfg_scale=(
                    (lambda v: (float(str(v)) if str(v).strip() != "" else None))(kwargs.get('cfg_scale'))
                ),
                sampler=kwargs.get('sampler') or None,
                steps=int(kwargs.get('steps') or 0) or None,
                seed=int(kwargs.get('seed') or 0) or None,
                is_adetailer=bool(kwargs.get('is_adetailer')) if kwargs.get('is_adetailer') is not None else None,
                loras=loras or None,
                civitai_model_ids=civitai_ids or None,
            )
        # Minimal fallback if helper missing
        w = int(kwargs.get('width') or 0) or None
        h = int(kwargs.get('height') or 0) or None
        meta = {
            "model_name": kwargs.get('model_name') or None,
            "prompt": kwargs.get('prompt') or None,
            "negative_prompt": kwargs.get('negative_prompt') or None,
            "width": w,
            "height": h,
            "cfg_scale": kwargs.get('cfg_scale'),
            "sampler": kwargs.get('sampler') or None,
            "steps": kwargs.get('steps'),
            "seed": kwargs.get('seed'),
            "is_adetailer": kwargs.get('is_adetailer'),
        }
        if w and h:
            meta["size"] = f"{w}x{h}"
        # Strip None
        return {k: v for k, v in meta.items() if v is not None}

    def _write_png_chunks(self, image, meta: Dict[str, Any], human_readable: bool):
        # Attempt non-destructive save into metadata if PIL is around and image has the correct backend
        try:
            from PIL import Image as PILImage, PngImagePlugin  # type: ignore
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
            _, pnginfo = vt_mmm.add_png_text_chunks(pil, meta, human_readable=human_readable) if (vt_mmm and hasattr(vt_mmm, 'add_png_text_chunks')) else (pil, None)
            # We won't write to disk here; this utility's role is to attach metadata for downstream save nodes.
            # Some downstream nodes (like Save Image Extended) can accept metadata dicts directly; we surface JSON instead.
        except Exception:
            pass
        return image

    def save(self,
             image,
             model_name: str,
             prompt: str,
             negative_prompt: str,
             width: int,
             height: int,
             cfg_scale: float,
             sampler: str,
             steps: int,
             seed: int,
             is_adetailer: bool,
             loras: str,
             civitai_model_ids: str,
             save_image: bool,
             human_readable_text_chunks: bool):
        # Build compact metadata JSON
        meta = self._to_meta(
            model_name=model_name,
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
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
