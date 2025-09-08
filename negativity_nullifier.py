import yaml
import os

class NegativityNullifier:
    """
    A ComfyUI node that assembles negative prompt strings from
    user-editable boilerplate and optional manual input.
    """

    neg_path = os.path.join(os.path.dirname(__file__), "feature_lists", "negative_defaults.yaml")
    with open(neg_path, "r", encoding="utf-8") as f:
        boilerplate = yaml.safe_load(f).get("boilerplate", [])

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "include_boilerplate": ("BOOLEAN", {"default": True}),
                "extra": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("NULLIFIER_STRING",)
    RETURN_NAMES = ("nullifier",)
    FUNCTION = "purify"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(**kwargs):
        import time
        return time.time()

    def purify(self, include_boilerplate, extra):
        parts = []

        if include_boilerplate and self.boilerplate:
            parts.extend(self.boilerplate)

        if extra and extra.strip():
            parts.append(extra.strip())

        nullifier = ", ".join(parts).strip()
        return (nullifier,)

NODE_CLASS_MAPPINGS = {
    "NegativityNullifier": NegativityNullifier,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NegativityNullifier": "🚫 Negativity Nullifier",
}