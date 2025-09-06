import yaml
import os
import random
import colorsys
import pathlib

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

    # Color picker fields that will use hex input instead of dropdowns
    COLOR_FIELDS = {
        "hair_color", "highlight_color", "tips_color", "eye_color", 
        "eyeliner_color", "blush_color", "eyeshadow_color", "lipstick_color", "brow_color"
    }

    @classmethod
    def rgb_to_name(cls, hexrgb: str) -> str:
        """
        Convert hex RGB color to natural color name using HSV quantization.
        
        Args:
            hexrgb (str): Hex color string (with or without #)
            
        Returns:
            str: Natural color name with optional light/dark modifier
        """
        try:
            # Clean and parse hex color
            hexrgb = hexrgb.lstrip("#")
            if len(hexrgb) != 6:
                return "natural"
                
            r, g, b = [int(hexrgb[i:i+2], 16)/255.0 for i in (0, 2, 4)]
            
            # Convert to HSV for analysis
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            
            # Handle grayscale/low saturation colors
            if s <= cls.COLOR_CONFIG.get("gray_threshold", 0.15):
                if v >= 0.95:
                    return "white"
                elif v <= 0.05:
                    return "black"
                elif v >= 0.8:
                    return "silver"
                elif v <= 0.3:
                    return "charcoal"
                else:
                    return "gray"
            
            # Find closest base hue for saturated colors
            h_deg = h * 360
            base_hues = sorted(map(int, cls.COLOR_CONFIG["base_names"].keys()))
            
            # Handle wraparound (e.g., 350° is closer to 0° than 330°)
            distances = []
            for hue in base_hues:
                diff = abs(h_deg - hue)
                if diff > 180:
                    diff = 360 - diff
                distances.append(diff)
            
            closest_idx = distances.index(min(distances))
            base_name = cls.COLOR_CONFIG["base_names"][base_hues[closest_idx]]
            
            # Apply lightness modifiers based on value
            if v >= cls.COLOR_CONFIG["light_threshold"]:
                return f"light {base_name}"
            elif v <= cls.COLOR_CONFIG["dark_threshold"]:
                return f"dark {base_name}"
            else:
                return base_name
                
        except (ValueError, KeyError, TypeError):
            return "natural"

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        Color fields use color picker input, others use dropdown selections.
        
        Returns:
            dict: Node input configuration with mix of color pickers and dropdowns
        """
        types = {"required": {}}
        
        for key, options in cls.FEATURES.items():
            if key in cls.COLOR_FIELDS:
                # Color picker input for color-related fields
                types["required"][key] = ("STRING", {
                    "default": "#8B4513",  # Default brown color
                    "multiline": False
                })
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
        Process field selection, converting color hex codes to natural names.
        
        Args:
            key (str): Field name
            choice (str): User selection (dropdown choice or hex color)
            
        Returns:
            str: Processed field value
        """
        if key in self.COLOR_FIELDS:
            # Handle color picker input
            if not choice or choice.strip() == "":
                return ""
            # Convert hex color to natural color name
            color_name = self.rgb_to_name(choice)
            return f"{color_name} {key.replace('_', ' ')}"
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