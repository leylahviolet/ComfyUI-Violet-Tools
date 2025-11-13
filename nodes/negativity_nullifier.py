import yaml
import os
import sys

# Add node_resources directory to path for prompt_dedupe import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "node_resources"))
from prompt_dedupe import dedupe_and_clean_prompt

class NegativityNullifier:
    """
    A ComfyUI node that assembles negative prompt strings from
    user-editable boilerplate and optional manual input.
    """

    neg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_lists", "negativity_nullifier.yaml")
    with open(neg_path, "r", encoding="utf-8") as f:
        boilerplate = yaml.safe_load(f).get("boilerplate", [])

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "include_boilerplate": ("BOOLEAN", {"default": True}),
                "extra": ("STRING", {"multiline": True, "default": "", "label": "extra, wildcards"}),
            },
            "optional": {
                "extra_input": ("STRING", {"multiline": True, "forceInput": True, "tooltip": "Optional chained input - will be prepended to extra field with ', '"})
            }
        }

    RETURN_TYPES = ("NULLIFIER_STRING",)
    RETURN_NAMES = ("nullifier",)
    FUNCTION = "purify"
    CATEGORY = "Violet Tools 💅/Prompt"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        import time
        return time.time()

    def purify(self, include_boilerplate, extra, extra_input=None):
        parts = []

        if include_boilerplate and self.boilerplate:
            parts.extend(self.boilerplate)

        # Chain extra_input + extra with chaining logic
        def _resolve_wildcards(text: str) -> str:
            if not text or "{" not in text:
                return text.strip() if text else text
            import re, random
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

        nullifier = ", ".join(parts).strip()
        # Deduplicate phrases and clean up comma issues
        nullifier = dedupe_and_clean_prompt(nullifier)

        meta = {
            "include_boilerplate": include_boilerplate,
            "extra": extra.strip() if isinstance(extra, str) else extra,
        }

        bundle = (nullifier, meta)
        return (bundle,)

NODE_CLASS_MAPPINGS = {
    "NegativityNullifier": NegativityNullifier,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NegativityNullifier": "🚫 Negativity Nullifier",
}