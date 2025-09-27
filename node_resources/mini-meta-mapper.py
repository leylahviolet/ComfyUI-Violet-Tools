# -*- coding: utf-8 -*-
"""
Mini Meta Mapper

Purpose: Build a compact, shareable JSON metadata object from typical ComfyUI
workflow parameters without embedding the entire workflow. Designed to be
embedded into PNG text chunks (PngInfo) under a single key `generation_data` and
optionally mirrored into human-readable keys.

This module is intentionally standalone: it only depends on Pillow (PIL) which
ships with ComfyUI. It does not import ComfyUI internals.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

try:
    from PIL import Image, PngImagePlugin  # type: ignore
except Exception:  # pragma: no cover
    Image = None
    PngImagePlugin = None


@dataclass
class LoraRef:
    lora: str
    weight: float = 1.0
    civitai_model_id: Optional[int] = None


@dataclass
class GenerationMeta:
    model_name: Optional[str] = None
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    size: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    cfg_scale: Optional[float] = None
    sampler: Optional[str] = None
    steps: Optional[int] = None
    seed: Optional[int] = None
    is_adetailer: Optional[bool] = None
    loras: List[LoraRef] = field(default_factory=list)
    civitai_model_ids: List[int] = field(default_factory=list)

    def to_json_obj(self) -> Dict[str, Any]:
        d = asdict(self)
        # Remove None values for compactness
        return {k: v for k, v in d.items() if v is not None and v != []}


def build_meta(
    model_name: Optional[str] = None,
    prompt: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    cfg_scale: Optional[float] = None,
    sampler: Optional[str] = None,
    steps: Optional[int] = None,
    seed: Optional[int] = None,
    is_adetailer: Optional[bool] = None,
    loras: Optional[List[Dict[str, Any]]] = None,
    civitai_model_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    mm = GenerationMeta(
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
        loras=[LoraRef(**it) if not isinstance(it, LoraRef) else it for it in (loras or [])],
        civitai_model_ids=list(civitai_model_ids or []),
    )
    if width and height and not mm.size:
        mm.size = f"{width}x{height}"
    return mm.to_json_obj()


def add_png_text_chunks(im, meta: Dict[str, Any], human_readable: bool = True):
    """Return (image, pnginfo) ready for saving with compact metadata.

    The caller should use: im.save(path, pnginfo=pnginfo, optimize=True)
    """
    if PngImagePlugin is None:
        raise RuntimeError("Pillow not available")
    pnginfo = PngImagePlugin.PngInfo()
    try:
        pnginfo.add_text("generation_data", json.dumps(meta, ensure_ascii=False))
    except Exception:
        # Fallback to ASCII-only if non-UTF characters cause issues in some viewers
        pnginfo.add_text("generation_data", json.dumps(meta, ensure_ascii=True))

    if human_readable:
        # Mirror a few helpful keys for platforms that display textual chunks
        if 'prompt' in meta:
            pnginfo.add_text("Prompt", meta['prompt'])
        if 'negative_prompt' in meta:
            pnginfo.add_text("Negative Prompt", meta['negative_prompt'])
        if 'sampler' in meta:
            pnginfo.add_text("Sampler", str(meta['sampler']))
        if 'cfg_scale' in meta:
            pnginfo.add_text("CFG Scale", str(meta['cfg_scale']))
        if 'steps' in meta:
            pnginfo.add_text("Steps", str(meta['steps']))
        if 'seed' in meta:
            pnginfo.add_text("Seed", str(meta['seed']))
        if 'width' in meta:
            pnginfo.add_text("Width", str(meta['width']))
        if 'height' in meta:
            pnginfo.add_text("Height", str(meta['height']))
        if 'model_name' in meta:
            pnginfo.add_text("Model", str(meta['model_name']))
        if 'is_adetailer' in meta:
            pnginfo.add_text("Using ADetailer", "Yes" if meta['is_adetailer'] else "No")
    return im, pnginfo
