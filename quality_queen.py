import yaml
import os
import random

class QualityQueen:
    """
    A ComfyUI node that generates quality prompts with boilerplate tags and style options.
    Loads quality definitions from feature_lists/qualities.yaml and creates quality prompts.
    """

    quality_path = os.path.join(os.path.dirname(__file__), "feature_lists", "qualities.yaml")
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
                "extra": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("QUALITY_STRING",)
    RETURN_NAMES = ("quality",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(**kwargs):
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def generate(self, include_boilerplate, style, extra):
        """
        Generate quality prompts with boilerplate tags, optional style, and extra instructions.
        
        Args:
            include_boilerplate (bool): Whether to include boilerplate quality tags
            style (str): Style selection or "Random"/"None"
            extra (str): Additional quality instructions from user
            
        Returns:
            str: Quality prompt string
        """
        parts = []

        if include_boilerplate:
            parts.append(", ".join(self.boilerplate_tags))

        selected_style = style
        if style == "Random":
            selected_style = random.choice(list(self.styles.keys()))
        if selected_style != "None":
            style_text = self.styles[selected_style]
            parts.append(style_text)

        # Add extra text if provided
        if extra and extra.strip():
            parts.append(extra.strip())

        quality = ", ".join(parts).strip()

        return (quality,)

NODE_CLASS_MAPPINGS = {
    "QualityQueen": QualityQueen,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QualityQueen": "👑 Quality Queen",
}
