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
    def rgb_to_name(cls, color_input) -> str:
        """
        Convert color input (hex string or integer) to natural color name using HSV quantization.
        
        Args:
            color_input (str|int): Hex color string or integer color value
            
        Returns:
            str: Natural color name with optional light/dark modifier
        """
        try:
            # Handle different input types
            if isinstance(color_input, int):
                # Convert integer to hex string
                hexrgb = f"{color_input:06X}"
            elif isinstance(color_input, str):
                # Clean hex string
                hexrgb = color_input.lstrip("#")
                if len(hexrgb) != 6:
                    return "natural"
            else:
                return "natural"
                
            # Parse RGB values
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
        Color fields use INT type with color display widget, others use dropdown selections.
        
        Returns:
            dict: Node input configuration with mix of color pickers and dropdowns
        """
        types = {"required": {}}
        
        for key, options in cls.FEATURES.items():
            if key in cls.COLOR_FIELDS:
                # Use INT type with color display widget for color picker
                types["required"][key] = ("INT", {
                    "default": 0x8B4513,  # Default brown color as integer
                    "min": 0x000000,      # Black
                    "max": 0xFFFFFF,      # White
                    "step": 1,
                    "display": "color"    # This triggers the color picker widget!
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
        Process field selection, converting color integer values to natural names.
        
        Args:
            key (str): Field name
            choice (str|int): User selection (dropdown choice or color integer)
            
        Returns:
            str: Processed field value
        """
        if key in self.COLOR_FIELDS:
            # Handle color picker input (integer value)
            if choice is None or choice == 0 or choice == 0x000000:
                return ""  # Skip black/empty colors
            # Convert color integer to natural color name
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