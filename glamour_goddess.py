import yaml
import os
import random

class GlamourGoddess:
    """
    A ComfyUI node that assembles descriptive strings for hair and makeup using modular aesthetic features.
    Pulls options from feature_lists/glamour_goddess.yaml and supports Unspecified, Random, or user-specified values.
    Now includes intelligent color picker functionality with automatic color name quantization.
    """

    style_path = os.path.join(os.path.dirname(__file__), "feature_lists", "glamour_goddess.yaml")
    colors_path = os.path.join(os.path.dirname(__file__), "feature_lists", "violet_colors.yaml")
    
    with open(style_path, "r", encoding="utf-8") as f:
        FEATURES = yaml.safe_load(f)
    
    with open(colors_path, "r", encoding="utf-8") as f:
        COLOR_CONFIG = yaml.safe_load(f)

    # Color picker fields that will use color dropdown instead of style dropdowns
    COLOR_FIELDS = {
        "hair_color", "highlight_color", "tips_color", "eye_color", 
        "eyeliner_color", "blush_color", "eyeshadow_color", "lipstick_color", "brow_color",
        "fingernail_color", "toenail_color"
    }

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        Color fields use dropdown with 24 curated colors, others use their original dropdown selections.
        
        Returns:
            dict: Node input configuration with color dropdowns and style dropdowns
        """
        types = {"required": {}}
        
        # Generate color options from our color configuration
        color_options = ["Unspecified", "Random"]
        base_colors = list(cls.COLOR_CONFIG["base_names"].values())
        
        # Add base colors and light/dark variants
        for color in base_colors:
            color_options.extend([color, f"light {color}", f"dark {color}"])
        
        # Add special colors
        color_options.extend(["white", "black", "gray", "silver", "charcoal"])
        
        for key, options in cls.FEATURES.items():
            if key in cls.COLOR_FIELDS:
                # Use dropdown with curated color options
                types["required"][key] = (
                    color_options,
                    {"default": "Unspecified"}
                )
            else:
                # Standard dropdown for non-color fields
                types["required"][key] = (
                    ["Unspecified", "Random"] + options,
                    {"default": "Unspecified"}
                )
        
        types["required"]["extra"] = ("STRING", {"multiline": True, "default": ""})
        return types

    RETURN_TYPES = ("GLAMOUR_STRING",)
    RETURN_NAMES = ("glamour",)
    FUNCTION = "invoke"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED():
        import time
        return time.time()

    def pick(self, key, choice):
        """
        Process field selection, handling both color and style dropdown selections.
        
        Args:
            key (str): Field name
            choice (str): User selection from dropdown
            
        Returns:
            str: Processed field value
        """
        if key in self.COLOR_FIELDS:
            # Handle color dropdown selection
            if choice == "Unspecified":
                return ""
            elif choice == "Random":
                # Get all color options except Unspecified and Random
                color_options = self.INPUT_TYPES()["required"][key][0][2:]  # Skip first 2 items
                choice = random.choice(color_options)
            
            # Format color name with field type
            return f"{choice} {key.replace('_', ' ')}"
        else:
            # Handle standard dropdown input
            if choice == "Unspecified":
                return ""
            elif choice == "Random":
                return random.choice(self.FEATURES[key])
            return choice

    def invoke(self, **kwargs):
        parts = []

        for key in self.FEATURES:
            val = self.pick(key, kwargs.get(key, "Unspecified"))
            if val:
                parts.append(val.lower())

        if kwargs.get("extra"):
            extra = kwargs["extra"].strip()
            if extra:
                parts.append(extra)

        glamour = ", ".join(parts)
        return (glamour,)

NODE_CLASS_MAPPINGS = {
    "GlamourGoddess": GlamourGoddess,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GlamourGoddess": "✨ Glamour Goddess",
}