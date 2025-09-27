import yaml
import os
import random

class AestheticAlchemist:
    """
    A ComfyUI node that generates aesthetic prompts by blending multiple style aesthetics.
    Loads aesthetic definitions from feature_lists/aesthetic_alchemist.yaml and creates weighted positive prompts.
    """
    
    style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_lists", "aesthetic_alchemist.yaml")
    with open(style_path, "r", encoding="utf-8") as f:
        style_prompts = yaml.safe_load(f)

    @classmethod
    def extract_style_names(cls):
        """Return list of style names based on YAML schema.

        Supports two schemas:
        - New: top-level has fem/masc dicts with identical style keys.
        - Legacy: top-level keys are style names (values may be string or dict with fem/masc).
        """
        data = cls.style_prompts or {}
        if isinstance(data, dict) and "fem" in data and "masc" in data and isinstance(data.get("fem"), dict):
            return list(data["fem"].keys())
        return list(data.keys())

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        
        Returns:
            dict: Node input configuration with aesthetic selections and strength controls
        """
        aesthetics = ["None", "Random"] + cls.extract_style_names()
        return {
            "required": {
                "aesthetic_1": (aesthetics, {"default": aesthetics[1]}),
                # Two-option selector to show fem/masc directly (instead of true/false)
                "aesthetic_1_fem": (["fem", "masc"], {"default": "fem", "label": "", "tooltip": "Choose list for aesthetic_1"}),
                "aesthetic_1_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "aesthetic_2": (aesthetics, {"default": aesthetics[2]}),
                "aesthetic_2_fem": (["fem", "masc"], {"default": "fem", "label": "", "tooltip": "Choose list for aesthetic_2"}),
                "aesthetic_2_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "extra": ("STRING", {"multiline": True, "default": "", "label": "extra, wildcards"}),
            }
        }

    RETURN_TYPES = ("AESTHETIC_STRING",)
    RETURN_NAMES = ("aesthetic",)
    FUNCTION = "infuse"
    CATEGORY = "Violet Tools 💅/Prompt"
    
    @staticmethod
    def IS_CHANGED(**_kwargs):
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Args:
            **kwargs: Node input parameters (ignored)
            
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def infuse(self, aesthetic_1, aesthetic_2, aesthetic_1_fem, aesthetic_2_fem, aesthetic_1_strength, aesthetic_2_strength, extra):

        # Use same style list for logic as we present in the dropdown
        available_styles = self.__class__.extract_style_names()

        # Random selection handling
        selected_1 = aesthetic_1
        selected_2 = aesthetic_2
        if aesthetic_1 == "Random" and available_styles:
            selected_1 = random.choice(available_styles)
        if aesthetic_2 == "Random" and available_styles:
            filtered = [s for s in available_styles if s != selected_1]
            selected_2 = random.choice(filtered) if filtered else selected_1

        def _resolve_wildcards(text: str) -> str:
            """Resolve {opt1|opt2|...} wildcards by choosing one option per block."""
            if not text or "{" not in text:
                return text
            import re
            pattern = re.compile(r"\{([^{}]+)\}")
            def repl(m):
                opts = [o.strip() for o in m.group(1).split("|") if o.strip()]
                return random.choice(opts) if opts else ""
            prev = None
            out = text
            while out != prev:
                prev = out
                out = pattern.sub(repl, out)
            return out

        def _is_fem(val) -> bool:
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.strip().lower() == "fem"
            return True

        def weighted_text(style: str, weight: float, use_fem: bool) -> str:
            # Support both new and legacy YAML schemas
            data = self.style_prompts
            if isinstance(data, dict) and "fem" in data and "masc" in data and isinstance(data.get("fem"), dict):
                pool = data["fem" if use_fem else "masc"]
                base_entry = pool.get(style, "")
            else:
                base_entry = data.get(style, "")
                if isinstance(base_entry, dict):
                    base_entry = base_entry.get("fem" if use_fem else "masc", "")
            base = _resolve_wildcards(base_entry)
            if not base:
                return ""
            return f"({base}:{round(weight, 2)})" if weight < 0.99 else base

        styles = []
        if selected_1 != "None" and aesthetic_1_strength > 0.0:
            styles.append((selected_1, aesthetic_1_strength, _is_fem(aesthetic_1_fem)))
        if selected_2 != "None" and aesthetic_2_strength > 0.0:
            styles.append((selected_2, aesthetic_2_strength, _is_fem(aesthetic_2_fem)))

        pos_parts = [weighted_text(style, weight, use_fem) for style, weight, use_fem in styles]
        if extra and extra.strip():
            pos_parts.append(_resolve_wildcards(extra))

        aesthetic = ", ".join(filter(None, pos_parts))

        meta = {
            "aesthetic_1": selected_1,
            "aesthetic_1_fem": "fem" if _is_fem(aesthetic_1_fem) else "masc",
            "aesthetic_1_strength": aesthetic_1_strength,
            "aesthetic_2": selected_2,
            "aesthetic_2_fem": "fem" if _is_fem(aesthetic_2_fem) else "masc",
            "aesthetic_2_strength": aesthetic_2_strength,
            "extra": extra.strip() if isinstance(extra, str) else extra,
        }

        # Bundle text + meta in a single output value
        bundle = (aesthetic, meta)
        return (bundle,)

NODE_CLASS_MAPPINGS = {
    "AestheticAlchemist": AestheticAlchemist,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AestheticAlchemist": "💋 Aesthetic Alchemist",
}
