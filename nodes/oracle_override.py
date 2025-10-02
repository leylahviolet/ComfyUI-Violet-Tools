# -*- coding: utf-8 -*-
import time, random, re
from typing import Optional
import sys
import os

# Add node_resources directory to path for prompt_dedupe import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "node_resources"))
from prompt_dedupe import dedupe_and_clean_prompt


class OracleOverride:
    """🔮 Oracle's Override

    Provides a manual multiline text override for the positive prompt.
    Output:
    - override (STRING or None): override text when enabled; otherwise null

    This node is independent of Character Curator.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "override": ("STRING", {"multiline": True, "default": "", "tooltip": "Manual positive prompt override"}),
                "override_prompts": ("BOOLEAN", {"default": False, "tooltip": "If true, Encoding Enchantress will only use this text for positive encoding"}),
            },
            "optional": {
                "chain": ("STRING", {"multiline": False, "forceInput": True, "defaultInput": True, "tooltip": "Text to prepend before override (joined with ', ')"}),
            }
        }

    RETURN_TYPES = ("OVERRIDE_STRING",)
    RETURN_NAMES = ("override",)
    FUNCTION = "build"
    CATEGORY = "Violet Tools 💅/Prompt"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def build(self, override: str, override_prompts: bool, chain: Optional[str] = None):
        # Only emit the override string when enabled; otherwise output None to represent null
        if bool(override_prompts):
            def _resolve_wildcards(text: str) -> str:
                if not text or "{" not in text:
                    return text.strip() if isinstance(text, str) else ""
                pattern = re.compile(r"\{([^{}]+)\}")
                prev = None
                out = text
                while out != prev:
                    prev = out
                    def repl(m):
                        opts = [o.strip() for o in m.group(1).split("|") if o.strip()]
                        return random.choice(opts) if opts else ""
                    out = pattern.sub(repl, out)
                return out.strip()

            text = override if isinstance(override, str) else ""
            prefix = chain if isinstance(chain, str) else ""
            # Resolve wildcards on both parts to mirror other prompt nodes
            text = _resolve_wildcards(text)
            prefix = _resolve_wildcards(prefix)
            parts = []
            if prefix.strip():
                parts.append(prefix.strip())
            if text.strip():
                parts.append(text.strip())
            combined = ", ".join(parts)
            # Deduplicate phrases and clean up comma issues
            combined = dedupe_and_clean_prompt(combined)
            return (combined,)
        return (None,)


NODE_CLASS_MAPPINGS = {"OracleOverride": OracleOverride}
NODE_DISPLAY_NAME_MAPPINGS = {"OracleOverride": "🔮 Oracle's Override"}
