import yaml
import os

class NegativityNullifier:
    """
    A ComfyUI node that assembles negative prompt strings from
    user-editable boilerplate and optional manual input.
    """

    neg_path = os.path.join(os.path.dirname(__file__), "feature_lists", "negativity_nullifier.yaml")
    with open(neg_path, "r", encoding="utf-8") as f:
        boilerplate = yaml.safe_load(f).get("boilerplate", [])

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "include_boilerplate": ("BOOLEAN", {"default": True}),
                "extra": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "character_data": ("CHARACTER_DATA", {}),
                "character_apply": ("BOOLEAN", {"default": False, "tooltip": "Apply loaded character negative overrides"})
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

    def purify(self, include_boilerplate, extra, character_data=None, character_apply=False):
        if character_apply and character_data and isinstance(character_data, dict):
            nd = character_data.get("data", {}).get("negative", {})
            if nd:
                include_boilerplate = nd.get("include_boilerplate", include_boilerplate)
                if nd.get("extra"):
                    extra = nd.get("extra")
        parts = []

        if include_boilerplate and self.boilerplate:
            parts.extend(self.boilerplate)

        if extra and extra.strip():
            parts.append(extra.strip())

        nullifier = ", ".join(parts).strip()
        
        # Add BREAK for prompt segmentation
        if nullifier:
            nullifier += ", BREAK"
            
        return (nullifier,)

NODE_CLASS_MAPPINGS = {
    "NegativityNullifier": NegativityNullifier,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "NegativityNullifier": "🚫 Negativity Nullifier",
}