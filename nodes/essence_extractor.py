import os
import toml


# Resolve base resources directory for Essence Extractor (fixed location inside this package)
PKG_ROOT = os.path.dirname(os.path.dirname(__file__))
BASE_DIR = os.path.normpath(os.path.join(PKG_ROOT, "node_resources", "essence-extractor"))


def _scan_models(base_dir: str):
    """Scan for ONNX models under the base_dir and return (names, mapping)."""
    names = []
    mapping = {}
    seen = {}
    for root, _dirs, files in os.walk(base_dir):
        for fn in files:
            if fn.lower().endswith(".onnx"):
                name = fn  # show file name only
                # ensure uniqueness if multiple with same file name
                if name in seen:
                    seen[name] += 1
                    disp = f"{name} ({seen[name]})"
                else:
                    seen[name] = 1
                    disp = name
                abs_path = os.path.join(root, fn)
                names.append(disp)
                mapping[disp] = abs_path
    if not names:
        names = ["<no .onnx models found>"]
        mapping[names[0]] = ""
    return names, mapping


class EssenceExtractor:
    """
    Lightweight handle node exposing configuration and paths required for the
    Essence Extractor pipeline (algorithmic consolidator + optional ONNX LLM).

    This node does not process prompts itself; it exposes an `ESSENCE_EXTRACTOR`
    object consumed by Encoding Enchantress when `prompt_processor` is enabled.
    """

    @classmethod
    def INPUT_TYPES(cls):
        # Build model dropdown at import time (YAML-like static behavior)
        model_names, _ = _scan_models(BASE_DIR)
        return {
            "required": {
                "model": (model_names, {"default": model_names[0], "tooltip": "Select an Essentia Ex Machina model (.onnx) found in the bundled resources"}),
            },
            "optional": {
                "sfw_mode": ("BOOLEAN", {"default": False, "tooltip": "Apply SFW covering rules when consolidating"}),
                "auto_install_requirements": ("BOOLEAN", {"default": True, "tooltip": "If missing, auto-install required Python packages (rapidfuzz, toml, PyYAML) into the current ComfyUI environment."}),
            },
        }

    RETURN_TYPES = ("ESSENCE_EXTRACTOR",)
    RETURN_NAMES = ("essence",)
    FUNCTION = "build"
    CATEGORY = "Violet Tools 💅/Prompt"

    def build(self, model, sfw_mode=False, auto_install_requirements=True):
        # Resolve selected model name to absolute path
        _, mapping = _scan_models(BASE_DIR)
        model_path = mapping.get(model, "")
        config_path_abs = os.path.join(BASE_DIR, "config.toml")

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
            "resources_dir": BASE_DIR,
            "config": cfg,
            "model_name": model,
            "model_path": model_path,
            "auto_install_requirements": bool(auto_install_requirements),
            "sfw_mode": bool(sfw_mode),
        }
        return (payload,)


NODE_CLASS_MAPPINGS = {
    "EssenceExtractor": EssenceExtractor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EssenceExtractor": "🧪 Essence Extractor",
}
 
