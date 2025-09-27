import yaml
import os
import random

class BodyBard:
    """
    A ComfyUI node that builds modular body descriptions with aesthetic control over size, shape,
    and detailed anatomy features. Outputs a composable body string for character conditioning.
    """

    feature_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_lists", "body_bard.yaml")
    with open(feature_path, "r", encoding="utf-8") as f:
        FEATURES = yaml.safe_load(f)

    @classmethod
    def INPUT_TYPES(cls):
        types = {
            "required": {}
        }
        for key, options in cls.FEATURES.items():
            if isinstance(options, dict):
                option_keys = list(options.keys())
                types["required"][key] = (
                    ["Unspecified", "Random"] + option_keys,
                    {"default": "Unspecified"}
                )
            else:
                types["required"][key] = (
                    ["Unspecified", "Random"] + options,
                    {"default": "Unspecified"}
                )
        types["required"]["extra"] = ("STRING", {"multiline": True, "default": "", "label": "extra, wildcards"})
        types["optional"] = {}
        return types

    RETURN_TYPES = ("BODY_STRING",)
    RETURN_NAMES = ("body",)
    FUNCTION = "compose"
    CATEGORY = "Violet Tools 💅/Prompt"

    @staticmethod
    def IS_CHANGED(**_kwargs):
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
            def _resolve_wildcards(text: str) -> str:
                if not text or "{" not in text:
                    return text.strip() if text else text
                import re
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

            extra = _resolve_wildcards(kwargs["extra"]) if kwargs["extra"] else ""
            if extra:
                parts.append(extra)

        body = ", ".join(parts)

        # Capture raw selections for persistence
        meta = {}
        for key in self.FEATURES:
            meta[key] = kwargs.get(key, "Unspecified")
        meta["extra"] = kwargs.get("extra", "").strip() if isinstance(kwargs.get("extra"), str) else kwargs.get("extra")

        bundle = (body, meta)
        return (bundle,)

NODE_CLASS_MAPPINGS = {
    "BodyBard": BodyBard,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BodyBard": "💃 Body Bard",
}