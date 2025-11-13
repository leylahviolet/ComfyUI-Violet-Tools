import yaml
import os
import random
import sys

# Add node_resources directory to path for prompt_dedupe import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "node_resources"))
from prompt_dedupe import dedupe_and_clean_prompt

class QualityQueen:
    """
    A ComfyUI node that generates quality prompts with boilerplate tags and style options.
    Loads quality definitions from feature_lists/quality_queen.yaml and creates quality prompts.
    """

    quality_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_lists", "quality_queen.yaml")
    with open(quality_path, "r", encoding="utf-8") as f:
        quality_data = yaml.safe_load(f)

    boilerplate_tags = quality_data["boilerplate"]
    styles = quality_data["styles"]

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        
        Returns:
            dict: Node input configuration with boilerplate toggle, style selection, and extra text
        """
        return {
            "required": {
                "include_boilerplate": ("BOOLEAN", { "default": True }),
                "style": (
                    ["None", "Random"] + list(cls.styles.keys()),
                    { "default": "Random" }
                ),
                "extra": ("STRING", {"multiline": True, "default": "", "label": "extra, wildcards"}),
            },
            "optional": {
                "extra_input": ("STRING", {"multiline": True, "forceInput": True, "tooltip": "Optional chained input - will be prepended to extra field with ', '"})
            }
        }

    RETURN_TYPES = ("QUALITY_STRING",)
    RETURN_NAMES = ("quality",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅/Prompt"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def generate(self, include_boilerplate, style, extra, extra_input=None):
        # Build quality prompt from boilerplate, optional style, and extra instructions
        parts = []

        if include_boilerplate:
            parts.append(", ".join(self.boilerplate_tags))

        selected_style = style
        if style == "Random":
            selected_style = random.choice(list(self.styles.keys()))
        if selected_style != "None":
            style_text = self.styles[selected_style]
            parts.append(style_text)

        # Add extra text if provided with wildcard resolution
        def _resolve_wildcards(text: str) -> str:
            if not text or "{" not in text:
                return text.strip() if text else text
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
            return out.strip()

        # NEW: Chain extra_input + extra with chaining logic
        extra_parts = []
        
        # Add optional chained input first
        if extra_input and extra_input.strip():
            extra_parts.append(_resolve_wildcards(extra_input.strip()))
        
        # Add extra field content second  
        if extra and extra.strip():
            extra_parts.append(_resolve_wildcards(extra.strip()))
        
        # Combine with ", " separator and add to parts if anything exists
        if extra_parts:
            extra_combined = ", ".join(extra_parts)
            parts.append(extra_combined)

        quality = ", ".join(parts).strip()
        # Deduplicate phrases and clean up comma issues
        quality = dedupe_and_clean_prompt(quality)

        # Build metadata capturing resolved selections for persistence
        meta = {
            "include_boilerplate": include_boilerplate,
            "style": selected_style,
            "extra": extra.strip() if isinstance(extra, str) else extra,
        }

        bundle = (quality, meta)
        return (bundle,)

NODE_CLASS_MAPPINGS = {
    "QualityQueen": QualityQueen,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QualityQueen": "👑 Quality Queen",
}
