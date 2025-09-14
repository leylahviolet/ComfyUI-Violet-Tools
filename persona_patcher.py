# -*- coding: utf-8 -*-
import os, json, time, random

class PersonaPatcher:
    """🗝️ Persona Patcher
    
    Loads saved characters and outputs their data for use with other Violet Tools nodes.
    
    Simple dropdown interface:
    - Select a character to load their saved configuration
    - Use "random" to pick a random character
    - Connect CHARACTER_DATA output to other Violet Tools nodes
    """

    @classmethod
    def get_characters_folder(cls):
        # Try to use ComfyUI's output directory, fallback to current directory
        try:
            import folder_paths
            return os.path.join(folder_paths.get_output_directory(), "characters")
        except ImportError:
            # Fallback to a characters folder in current working directory
            return os.path.join(os.getcwd(), "characters")

    @classmethod
    def list_characters(cls):
        folder = cls.get_characters_folder()
        if not os.path.exists(folder):
            return []
        try:
            return sorted([f[:-5] for f in os.listdir(folder) if f.endswith('.json')])
        except OSError:
            return []

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
                "refresh": ("BOOLEAN", {"default": False, "tooltip": "Toggle to refresh character list"})
            }
        }

    RETURN_TYPES = ("CHARACTER_DATA", "STRING", "STRING")
    RETURN_NAMES = ("character_data", "character_name", "status")
    FUNCTION = "patch"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(refresh=False, **_kwargs):
        # refresh parameter triggers UI updates when toggled
        return time.time()

    def patch(self, character: str, refresh: bool = False):
        # refresh parameter handled by IS_CHANGED for UI updates
        if character == "None":
            return ({}, "", "🗝️ Select a character to load")

        chars = self.list_characters()
        if not chars:
            folder = self.get_characters_folder()
            return ({}, "", f"⚠️ No characters found. Save some with Persona Preserver first.\nLooking in: {folder}")

        # Random selection
        selected_name = character
        if character == "random":
            selected_name = random.choice(chars)

        if selected_name not in chars:
            return ({}, "", f"❌ Character '{selected_name}' not found. Try refreshing.")

        path = os.path.join(self.get_characters_folder(), f"{selected_name}.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Simple validation
            if not isinstance(data, dict) or 'data' not in data:
                return ({}, "", f"❌ Invalid character file format for '{selected_name}'")

            name = data.get('name', selected_name)
            status = f"✅ Loaded '{name}'" if character != "random" else f"🎲 Random: '{name}'"
            
            return (data, name, status)
            
        except (OSError, json.JSONDecodeError) as e:
            return ({}, "", f"❌ Error loading '{selected_name}': {e}")

NODE_CLASS_MAPPINGS = {"PersonaPatcher": PersonaPatcher}
NODE_DISPLAY_NAME_MAPPINGS = {"PersonaPatcher": "🗝️ Persona Patcher"}
