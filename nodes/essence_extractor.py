import os
import toml


class EssenceExtractor:
    """
    Lightweight handle node exposing configuration and paths required for the
    Essence Extractor pipeline (algorithmic consolidator + optional ONNX LLM).

    This node does not process prompts itself; it exposes an `ESSENCE_EXTRACTOR`
    object consumed by Encoding Enchantress when `prompt_processor` is enabled.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Show relative defaults in UI; resolve to absolute in build()
        rel_base = os.path.join(".", "node_resources", "essence-extractor")
        rel_config = os.path.join(rel_base, "config.toml")
        return {
            "required": {
                "resources_dir": ("STRING", {"default": rel_base, "multiline": False, "tooltip": "Folder containing prompt_consolidator.py and data/"}),
                "config_path": ("STRING", {"default": rel_config, "multiline": False, "tooltip": "Path to config.toml inside the resources folder"}),
                "use_local_model": ("BOOLEAN", {"default": True, "tooltip": "Use bundled ONNX model if available"}),
            },
            "optional": {
                "sfw_mode": ("BOOLEAN", {"default": False, "tooltip": "Apply SFW covering rules when consolidating"}),
            },
        }

    RETURN_TYPES = ("ESSENCE_EXTRACTOR",)
    RETURN_NAMES = ("essence",)
    FUNCTION = "build"
    CATEGORY = "Violet Tools 💅/Prompt"

    def build(self, resources_dir, config_path, use_local_model, sfw_mode=False):
        # Resolve relative paths against this package root so users can keep inputs tidy
        pkg_root = os.path.dirname(os.path.dirname(__file__))
        def _resolve(p: str) -> str:
            if not p:
                return p
            return os.path.normpath(p if os.path.isabs(p) else os.path.join(pkg_root, p))

        resources_dir_abs = _resolve(resources_dir)
        config_path_abs = _resolve(config_path)

        cfg = {}
        if os.path.isfile(config_path_abs):
            try:
                with open(config_path_abs, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
                    if txt:
                        cfg = toml.loads(txt)
            except (toml.TomlDecodeError, OSError, ValueError):
                cfg = {}

        payload = {
            "resources_dir": resources_dir_abs,
            "config": cfg,
            "use_local_model": bool(use_local_model),
            "sfw_mode": bool(sfw_mode),
        }
        return (payload,)


NODE_CLASS_MAPPINGS = {
    "EssenceExtractor": EssenceExtractor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EssenceExtractor": "🧪 Essence Extractor",
}
 
