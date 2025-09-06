import yaml
import os
import random

class BodyBard:
    """
    A ComfyUI node that builds modular body descriptions with aesthetic control over size, shape,
    and detailed anatomy features. Outputs a composable body string for character conditioning.
    """

    feature_path = os.path.join(os.path.dirname(__file__), "feature_lists", "body_features.yaml")
    with open(feature_path, "r", encoding="utf-8") as f:
        FEATURES = yaml.safe_load(f)

    @classmethod
    def INPUT_TYPES(cls):
        types = {
            "required": {}
        }
        for key, options in cls.FEATURES.items():
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
    def IS_CHANGED():
        import time
        return time.time()

    def pick(self, name, choice):
        if choice == "Unspecified":
            return ""
        elif choice == "Random":
            return random.choice(self.FEATURES[name])
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
        return (body,)

NODE_CLASS_MAPPINGS = {
    "BodyBard": BodyBard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BodyBard": "💃 Body Bard",
}