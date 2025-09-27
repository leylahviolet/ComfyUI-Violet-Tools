# -*- coding: utf-8 -*-
import time


class OracleOverride:
    """🔮 Oracle's Override

    Provides a manual multiline text override for the positive prompt.
    Outputs:
    - override (STRING): the text to use for positive prompt when enabled
    - override_prompts (BOOLEAN): whether to override

    This node is independent of Character Curator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "override": ("STRING", {"multiline": True, "default": "", "tooltip": "Manual positive prompt override"}),
                "override_prompts": ("BOOLEAN", {"default": False, "tooltip": "If true, Encoding Enchantress will only use this text for positive encoding"}),
            }
        }

    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("override", "override_prompts")
    FUNCTION = "build"
    CATEGORY = "Violet Tools 💅/Prompt"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def build(self, override: str, override_prompts: bool):
        # Pass through the values
        text = override if isinstance(override, str) else ""
        flag = bool(override_prompts)
        return (text, flag)


NODE_CLASS_MAPPINGS = {"OracleOverride": OracleOverride}
NODE_DISPLAY_NAME_MAPPINGS = {"OracleOverride": "🔮 Oracle's Override"}
