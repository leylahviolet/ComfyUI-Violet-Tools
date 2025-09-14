# -*- coding: utf-8 -*-
import os, json, time, random

class PersonaPatcher:
    """🗝️ Persona Patcher
Loads a saved character JSON (created by Persona Preserver) and outputs a structured
CHARACTER_DATA dict that other Violet Tools nodes can optionally consume to auto-populate
user selections WITHOUT manual re-entry.

Design:
- Provides a dropdown of character files in /characters
- When a character is chosen, loads JSON and outputs:
  * CHARACTER_DATA (dict)
  * character_name (STRING)
  * status (STRING)
- If None selected, passes through empty data.

Consumption Pattern (in other nodes):
- Add optional input `character_data` of type CHARACTER_DATA.
- At start of node logic, if character_data and relevant section exists, override local
  selections (only when user kept defaults like Random/Unspecified or a new 'Use Character').

This keeps user ability to tweak after loading.
"""

    @classmethod
    def get_characters_folder(cls):
        return os.path.join(os.path.dirname(__file__), "characters")

    @classmethod
    def list_characters(cls):
        folder = cls.get_characters_folder()
        if not os.path.exists(folder):
            os.makedirs(folder)
            return []
        return sorted([f[:-5] for f in os.listdir(folder) if f.endswith('.json')])

    @classmethod
    def INPUT_TYPES(cls):
        chars = cls.list_characters()
        options = ["None"]
        if chars:
            options.append("random")
            options.extend(chars)
        return {
            "required": {
                "character": (options, {"default": "None", "tooltip": "Select saved character or random"}),
                "refresh": ("BOOLEAN", {"default": False, "tooltip": "Toggle to refresh dropdown list"})
            }
        }

    RETURN_TYPES = ("CHARACTER_DATA", "STRING", "STRING")
    RETURN_NAMES = ("character_data", "character_name", "status")
    FUNCTION = "patch"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(refresh=False, **_kwargs):
        # Including refresh in signature so toggling it invalidates cache; time-based ensures dropdown stays reactive
        return time.time() if refresh else time.time()

    def patch(self, character: str, refresh: bool=False):  # refresh included to trigger UI rebuild when toggled
        # Touch refresh to satisfy linters; logic handled in INPUT_TYPES/IS_CHANGED
        _ = refresh
        if character == "None":
            return ({}, "", "🗝️ Persona Patcher idle - select a character to load")

        chars = self.list_characters()
        if not chars:
            return ({}, "", "⚠️ No characters saved yet. Use Persona Preserver to create one.")

        # Random selection
        selected_name = character
        if character == "random":
            selected_name = random.choice(chars)

        path = os.path.join(self.get_characters_folder(), f"{selected_name}.json")
        if not os.path.exists(path):
            return ({}, "", f"❌ Character '{selected_name}' not found (refresh list?)")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            migrated = self._migrate_schema(data)
            # Persist migration silently if structure changed
            if migrated is not data:
                data = migrated
            else:
                data = migrated
            try:
                # Rewrite only if key structural fields differ (cheap checksum via repr length)
                if json.dumps(data, sort_keys=True) != json.dumps(migrated, sort_keys=True):
                    # (Unlikely branch since we reassign above, kept for clarity)
                    pass
                # Always write back to ensure new version stamp or added empty sections persist
                with open(path, 'w', encoding='utf-8') as wf:
                    json.dump(data, wf, indent=2, ensure_ascii=False)
            except OSError:
                pass  # Silent fail per requirement

            status = f"✅ Loaded character '{selected_name}'" if character != "random" else f"🎲 Randomly loaded '{selected_name}'"
            return (data, data.get('name', selected_name), status)
        except (OSError, json.JSONDecodeError) as e:
            return ({}, "", f"❌ Error loading character: {e}")

    # --- Internal helpers ---
    def _migrate_schema(self, data: dict) -> dict:
        """Silently normalize older character JSON structures to current expected layout.

    Current target schema (version 1.3.x):
        {
          name, created, violet_tools_version, data: { quality, scene, glamour, body, aesthetic, pose, negative }
        }

        Migration rules (silent, no warnings):
        - If root lacks 'data' but contains any known section keys, wrap them under data.
        - Rename 'nullifier' section to 'negative'.
        - If 'negative' missing but 'nullifier' present inside data, move/rename.
        - Ensure sub-dicts exist for all expected sections; create empty if absent.
        - If strengths were saved at root level of sections in older format, keep them.
        - Populate missing keys only; never overwrite existing user-provided values.
        """
        if not isinstance(data, dict):
            return {"name": "Unknown", "data": {}}

        known_sections = {"quality", "scene", "glamour", "body", "aesthetic", "pose", "negative", "nullifier"}

        # If no 'data' key but section keys exist at root, wrap them
        if "data" not in data:
            root_section_keys = {k for k in data.keys() if k in known_sections}
            if root_section_keys:
                wrapped = {}
                for k in root_section_keys:
                    wrapped[k] = data.get(k, {}) if isinstance(data.get(k), dict) else {"value": data.get(k)}
                # Remove moved keys
                for k in root_section_keys:
                    data.pop(k, None)
                data["data"] = wrapped
        # Guarantee 'data' exists
        data.setdefault("data", {})

        d = data["data"]

        # Rename nullifier -> negative
        if "nullifier" in d and "negative" not in d:
            d["negative"] = d.pop("nullifier")

        # If still using root-level nullifier (post-wrap scenario missed)
        if "nullifier" in data and "negative" not in d:
            d["negative"] = data.pop("nullifier")

        # Ensure each expected section exists
        for section in ["quality", "scene", "glamour", "body", "aesthetic", "pose", "negative"]:
            d.setdefault(section, {})
            if not isinstance(d[section], dict):
                d[section] = {"value": str(d[section])}

        # Key normalization within sections (future-proof placeholder)
        # Example: older keys or aliases could be mapped here silently.

        return data

NODE_CLASS_MAPPINGS = {"PersonaPatcher": PersonaPatcher}
NODE_DISPLAY_NAME_MAPPINGS = {"PersonaPatcher": "🗝️ Persona Patcher"}
