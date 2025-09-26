# -*- coding: utf-8 -*-
import os, json, time, random

class CharacterCache:
    """🗃️ Character Cache
    
    Loads saved characters and outputs their data for use with other Violet Tools nodes.
    
    Simple dropdown interface:
    - Select a character to load their saved configuration
    - Use "random" to pick a random character
    - Connect CHARACTER_DATA output to other Violet Tools nodes
    """

    @classmethod
    def get_characters_folder(cls):
        """Preferred load path with legacy fallback.

        New: ComfyUI/user/default/comfyui-violet-tools/characters
        Legacy: ComfyUI/output/characters
        """
        try:
            import importlib
            folder_paths = importlib.import_module("folder_paths")  # type: ignore
            # Preferred user path
            user_dir = getattr(folder_paths, "get_user_directory", None)
            if callable(user_dir):
                base_user = user_dir()
            else:
                out_dir = folder_paths.get_output_directory()
                base_user = os.path.join(os.path.dirname(str(out_dir)), "user")
            preferred = os.path.join(str(base_user), "default", "comfyui-violet-tools", "characters")
            if os.path.exists(preferred):
                return preferred
            # Legacy fallback under output
            legacy = os.path.join(folder_paths.get_output_directory(), "characters")
            if os.path.exists(legacy):
                return legacy
            return preferred  # default to preferred if neither exists
        except (ImportError, AttributeError, OSError, TypeError):
            # Fallback to current working directory under user-like path
            return os.path.join(os.getcwd(), "user", "default", "comfyui-violet-tools", "characters")

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
                "character": (options, {"default": "None", "tooltip": "Select saved character or random"})
            }
        }

    RETURN_TYPES = ("CHARACTER_DATA", "STRING", "STRING")
    RETURN_NAMES = ("character", "name", "status")
    FUNCTION = "load_character"
    CATEGORY = "Violet Tools 💅/Character"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        # Always refresh to keep character list up-to-date
        return time.time()

    def load_character(self, character: str):
        if character == "None":
            return ({}, "", "🗝️ Select a character to load")

        chars = self.list_characters()
        if not chars:
            folder = self.get_characters_folder()
            return ({}, "", f"⚠️ No characters found. Save some with Character Creator first.\nLooking in: {folder}")

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
            
            # Create detailed profile for status message
            profile_lines = []
            if character != "random":
                profile_lines.append(f"✅ Loaded '{name}':")
            else:
                profile_lines.append(f"🎲 Random: '{name}':")
            
            char_data = data.get('data', {})
            
            # Quality Queen
            if 'quality' in char_data and char_data['quality'].get('text'):
                text = char_data['quality']['text']
                profile_lines.append(f"👑 Quality Queen: {text}")
            
            # Scene Seductress
            if 'scene' in char_data and char_data['scene'].get('text'):
                text = char_data['scene']['text']
                profile_lines.append(f"🎭 Scene Seductress: {text}")
            
            # Glamour Goddess
            if 'glamour' in char_data and char_data['glamour'].get('text'):
                text = char_data['glamour']['text']
                profile_lines.append(f"✨ Glamour Goddess: {text}")
            
            # Body Bard
            if 'body' in char_data and char_data['body'].get('text'):
                text = char_data['body']['text']
                profile_lines.append(f"💃 Body Bard: {text}")
            
            # Aesthetic Alchemist
            if 'aesthetic' in char_data and char_data['aesthetic'].get('text'):
                text = char_data['aesthetic']['text']
                profile_lines.append(f"💋 Aesthetic Alchemist: {text}")
            
            # Pose Priestess
            if 'pose' in char_data and char_data['pose'].get('text'):
                text = char_data['pose']['text']
                profile_lines.append(f"🤩 Pose Priestess: {text}")
            
            # Negativity Nullifier
            if 'negative' in char_data and char_data['negative'].get('text'):
                text = char_data['negative']['text']
                profile_lines.append(f"🚫 Negativity Nullifier: {text}")
            
            if len(profile_lines) == 1:  # Only the header line
                profile_lines.append("(No character data found)")
            
            status = "\n".join(profile_lines)
            
            return (data, name, status)
            
        except (OSError, json.JSONDecodeError) as e:
            return ({}, "", f"❌ Error loading '{selected_name}': {e}")

NODE_CLASS_MAPPINGS = {"CharacterCache": CharacterCache}
NODE_DISPLAY_NAME_MAPPINGS = {"CharacterCache": "🗃️ Character Cache"}
