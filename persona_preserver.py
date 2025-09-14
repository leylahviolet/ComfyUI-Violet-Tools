# -*- coding: utf-8 -*-
import json
import os
import time

class PersonaPreserver:
    """💖 Persona Preserver (Save Only)
    
    Connects to outputs from other Violet Tools nodes and saves them as a named character.
    Much simpler - just provide the character name and connect your configured nodes!
    
    Loading is handled by 🗝️ Persona Patcher.
    """

    @classmethod
    def get_characters_folder(cls):
        # Try to save in ComfyUI's output directory, fallback to current directory
        try:
            import folder_paths
            return os.path.join(folder_paths.get_output_directory(), "characters")
        except ImportError:
            # Fallback to a characters folder in current working directory
            return os.path.join(os.getcwd(), "characters")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_name": ("STRING", {"multiline": False, "default": "", "tooltip": "Enter a name to save this character configuration"}),
            },
            "optional": {
                "character": ("CHARACTER_DATA", {"forceInput": True, "tooltip": "Connect from Encoding Enchantress character output"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "save_persona"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def save_persona(self, character_name="", character=None):
        if not character_name or not character_name.strip():
            return ("💖 Enter a character name to save",)
        
        if not character:
            return ("💖 Connect Encoding Enchantress character output to save",)
        
        name = character_name.strip()
        
        # Use the character data directly from Encoding Enchantress
        character_data = {
            "name": name,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "violet_tools_version": "1.3.0",
            "data": character.get("data", {}) if isinstance(character, dict) else {}
        }
        
        try:
            folder = self.get_characters_folder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            file_path = os.path.join(folder, f"{name}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(character_data, f, indent=2, ensure_ascii=False)
            
            return (f"✅ Character '{name}' saved to {file_path}",)
            
        except OSError as e:
            return (f"❌ Error saving character: {e}",)

NODE_CLASS_MAPPINGS = {"PersonaPreserver": PersonaPreserver}
NODE_DISPLAY_NAME_MAPPINGS = {"PersonaPreserver": "💖 Persona Preserver"}

NODE_CLASS_MAPPINGS = {"PersonaPreserver": PersonaPreserver}
NODE_DISPLAY_NAME_MAPPINGS = {"PersonaPreserver": "💖 Persona Preserver"}