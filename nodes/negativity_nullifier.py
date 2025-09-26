import yaml
import os

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
                "character": ("CHARACTER_DATA", {}),
                "character_apply": ("BOOLEAN", {"default": False, "tooltip": "Apply loaded character negative overrides"})
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

    def purify(self, include_boilerplate, extra, character=None, character_apply=False):
        if character_apply and character and isinstance(character, dict):
            nd = character.get("data", {}).get("negative", {})
            if nd:
                include_boilerplate = nd.get("include_boilerplate", include_boilerplate)
                if nd.get("extra"):
                    extra = nd.get("extra")
        parts = []

        if include_boilerplate and self.boilerplate:
            parts.extend(self.boilerplate)

        if extra and extra.strip():
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

            parts.append(_resolve_wildcards(extra))

        nullifier = ", ".join(parts).strip()

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