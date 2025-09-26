# -*- coding: utf-8 -*-
import json
import os
import time

class CharacterCreator:
    """💖 Character Creator (Save Only)
    
    Connects to outputs from other Violet Tools nodes and saves them as a named character.
    Much simpler - just provide the character name and connect your configured nodes!
    
    Loading is handled by 🗃️ Character Cache.
    """

    @classmethod
    def get_characters_folder(cls):
        """Resolve preferred character storage directory.

        New location: ComfyUI/user/default/comfyui-violet-tools/characters
        Legacy (read-only fallback): ComfyUI/output/characters
        """
        # Preferred path under ComfyUI/user
        try:
            import importlib
            folder_paths = importlib.import_module("folder_paths")  # type: ignore
            # Try to use ComfyUI's user directory if available
            user_dir = getattr(folder_paths, "get_user_directory", None)
            if callable(user_dir):
                base_user = user_dir()
            else:
                # Derive from output directory if user dir API is unavailable
                out_dir = folder_paths.get_output_directory()
                base_user = os.path.join(os.path.dirname(str(out_dir)), "user")
            base_user_str = str(base_user)
            preferred = os.path.join(base_user_str, "default", "comfyui-violet-tools", "characters")
            return preferred
        except (ImportError, AttributeError, OSError, TypeError):
            # Fallback: put under current working directory in a user-like layout
            cwd_user = os.path.join(os.getcwd(), "user", "default", "comfyui-violet-tools", "characters")
            return cwd_user

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
    FUNCTION = "save_character"
    CATEGORY = "Violet Tools 💅/Character"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def save_character(self, character_name="", character=None):
        if not character_name or not character_name.strip():
            return ("💖 Enter a character name to save",)
        
        if not character:
            return ("💖 Connect Encoding Enchantress character output to save",)
        
        # Preserve display name, but sanitize filename for Windows safety
        name = character_name.strip()
        def _sanitize_filename(s: str) -> str:
            # Replace invalid Windows filename characters and trim
            invalid = '<>:"/\\|?*'
            trans = str.maketrans({c: '_' for c in invalid})
            s2 = s.translate(trans)
            s2 = ' '.join(s2.split())  # collapse whitespace
            s2 = s2.strip('. ')  # remove trailing dots/spaces
            return s2 or "character"
        file_stem = _sanitize_filename(name)
        
        # Use the character data directly from Encoding Enchantress
        character_data = {
            "name": name,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "violet_tools_version": "1.5.0",
            "data": character.get("data", {}) if isinstance(character, dict) else {}
        }
        
        try:
            folder = self.get_characters_folder()
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

            file_path = os.path.join(folder, f"{file_stem}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(character_data, f, indent=2, ensure_ascii=False)
            
            return (f"✅ Character '{name}' saved to {file_path}",)
            
        except OSError as e:
            return (f"❌ Error saving character: {e}",)

NODE_CLASS_MAPPINGS = {"CharacterCreator": CharacterCreator}
NODE_DISPLAY_NAME_MAPPINGS = {"CharacterCreator": "💖 Character Creator"}
