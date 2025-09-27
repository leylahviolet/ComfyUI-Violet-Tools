# -*- coding: utf-8 -*-
import json
import time


class CharacterInspector:
    """🪞 Character Inspector

    Utility node: Accepts CHARACTER_DATA and prints a concise, copy-friendly
    summary of selections per Violet Tools domain. This helps when you want to
    load a character, tweak a field manually in prompt nodes, and re-save.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character": ("CHARACTER_DATA", {"forceInput": True, "tooltip": "Connect from Character Cache or Encoding Enchantress"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "inspect"
    CATEGORY = "Violet Tools 💅/Character"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def inspect(self, character):
        if not character or not isinstance(character, dict):
            return ("🪞 Connect a CHARACTER_DATA input to inspect.",)

        name = character.get("name", "(unnamed)")
        data = character.get("data", {}) if isinstance(character.get("data", {}), dict) else {}

        lines = [f"🪞 Character: {name}"]

        def section(title, key):
            seg = data.get(key, {})
            if not isinstance(seg, dict):
                return
            text = seg.get("text")
            if text:
                lines.append(f"{title}: {text}")
            # Dump key:value pairs excluding 'text' for clarity
            keys = [k for k in seg.keys() if k != "text"]
            if keys:
                lines.append("  • selections:")
                for k in sorted(keys):
                    v = seg.get(k)
                    # Render compact JSON for complex structures
                    if isinstance(v, (dict, list)):
                        v_str = json.dumps(v, ensure_ascii=False)
                    else:
                        v_str = str(v)
                    lines.append(f"    - {k}: {v_str}")

        section("👑 Quality Queen", "quality")
        section("🎭 Scene Seductress", "scene")
        section("✨ Glamour Goddess", "glamour")
        section("💃 Body Bard", "body")
        section("💋 Aesthetic Alchemist", "aesthetic")
        section("🤩 Pose Priestess", "pose")
        section("🚫 Negativity Nullifier", "negative")

        # Provide a compact JSON block for copy/paste if needed
        try:
            compact = json.dumps({"name": name, "data": data}, ensure_ascii=False)
            lines.append("")
            lines.append("— compact JSON —")
            lines.append(compact)
        except (TypeError, ValueError):
            pass

        return ("\n".join(lines),)


NODE_CLASS_MAPPINGS = {"CharacterInspector": CharacterInspector}
NODE_DISPLAY_NAME_MAPPINGS = {"CharacterInspector": "🪞 Character Inspector"}
