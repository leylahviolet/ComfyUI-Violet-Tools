import yaml
import os
import random

class BodyBard:
    """
    A ComfyUI node that builds modular body descriptions with aesthetic control over size, shape,
    and detailed anatomy features. Outputs a composable body string for character conditioning.
    """

    feature_path = os.path.join(os.path.dirname(__file__), "feature_lists", "body_bard.yaml")
    with open(feature_path, "r", encoding="utf-8") as f:
        FEATURES = yaml.safe_load(f)

    @classmethod
    def INPUT_TYPES(cls):
        types = {
            "required": {}
        }
        for key, options in cls.FEATURES.items():
            # Handle key-value pairs without tooltips for now
            if isinstance(options, dict):
                option_keys = list(options.keys())
                
                types["required"][key] = (
                    ["Unspecified", "Random"] + option_keys,
                    {"default": "Unspecified"}
                )
            else:
                # Handle any remaining list-style options
                types["required"][key] = (
                    ["Unspecified", "Random"] + options,
                    {"default": "Unspecified"}
                )
        
        types["required"]["extra"] = ("STRING", {"multiline": True, "default": ""})
        return types

    RETURN_TYPES = ("BODY_STRING",)
    RETURN_NAMES = ("body",)
    FUNCTION = "compose"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(**kwargs):
        import time
        return time.time()

    def pick(self, name, choice):
        if choice == "Unspecified":
            return ""
        elif choice == "Random":
            options = self.FEATURES[name]
            if isinstance(options, dict):
                # For key-value pairs, return a random value
                return random.choice(list(options.values()))
            else:
                # For list options (shouldn't be any after conversion)
                return random.choice(options)
        else:
            # For specific choices, look up the value if it's a key-value pair
            options = self.FEATURES[name]
            if isinstance(options, dict) and choice in options:
                return options[choice]
            else:
                # Fallback to the choice itself
                return choice

    def compose(self, **kwargs):
        parts = []

        for key in self.FEATURES:
            value = self.pick(key, kwargs.get(key, "Unspecified"))
            if value:
                parts.append(value.lower())

        if kwargs.get("extra"):
            extra = kwargs["extra"].strip()
            if extra:
                parts.append(extra)

        body = ", ".join(parts)
        
        # Add BREAK for prompt segmentation
        if body:
            body += ", BREAK"
            
        return (body,)

NODE_CLASS_MAPPINGS = {
    "BodyBard": BodyBard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BodyBard": "💃 Body Bard",
}