import yaml
import os
import random

class GlamourGoddess:
    """
    A ComfyUI node that assembles descriptive strings for hair and makeup using modular aesthetic features.
    Pulls options from feature_lists/glamour_goddess.yaml with field-specific color lists.
    """

    style_path = os.path.join(os.path.dirname(__file__), "feature_lists", "glamour_goddess.yaml")
    
    with open(style_path, "r", encoding="utf-8") as f:
        FEATURES = yaml.safe_load(f)

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        All fields now use their complete lists from the YAML file with tooltip support.
        
        Returns:
            dict: Node input configuration with dropdown selections and tooltips
        """
        types = {"required": {}}
        
        for key, options in cls.FEATURES.items():
            # Extract keys for key-value pairs, but disable tooltips for now
            if isinstance(options, dict):
                option_keys = list(options.keys())
                
                types["required"][key] = (
                    ["Unspecified", "Random"] + option_keys,
                    {"default": "Unspecified"}
                )
            else:
                # Handle any remaining list-style options (shouldn't be any after conversion)
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
    def IS_CHANGED(**kwargs):
        import time
        return time.time()

    def pick(self, key, choice):
        """
        Process field selection with key-value structure support.
        
        Args:
            key (str): Field name
            choice (str): User selection from dropdown
            
        Returns:
            str: Processed field value
        """
        if choice == "Unspecified":
            return ""
        elif choice == "Random":
            options = self.FEATURES[key]
            if isinstance(options, dict):
                # For key-value pairs, return a random value
                return random.choice(list(options.values()))
            else:
                # For list options (shouldn't be any after conversion)
                return random.choice(options)
        else:
            # For specific choices, look up the value if it's a key-value pair
            options = self.FEATURES[key]
            if isinstance(options, dict) and choice in options:
                return options[choice]
            else:
                # Fallback to the choice itself
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
        
        # Add BREAK for prompt segmentation
        if glamour:
            glamour += ", BREAK"
            
        return (glamour,)

NODE_CLASS_MAPPINGS = {
    "GlamourGoddess": GlamourGoddess,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GlamourGoddess": "✨ Glamour Goddess",
}