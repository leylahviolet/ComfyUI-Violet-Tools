# -*- coding: utf-8 -*-
import os, time, random


class CharacterCurator:
    """💖 Character Curator (Wireless)

    Combined loader/saver node for Violet Tools characters.
    - load_character: choose which character to load via wireless frontend buttons
    - save_character: name to save current UI selections (wireless)

    Outputs only the selected name for optional wiring into metadata.
    """

    @classmethod
    def get_characters_folder(cls):
        """Preferred path for character storage (no legacy fallback)."""
        try:
            import importlib
            folder_paths = importlib.import_module("folder_paths")  # type: ignore
            user_dir = getattr(folder_paths, "get_user_directory", None)
            if callable(user_dir):
                base_user = user_dir()
            else:
                out_dir = folder_paths.get_output_directory()
                base_user = os.path.join(os.path.dirname(str(out_dir)), "user")
            preferred = os.path.join(str(base_user), "default", "comfyui-violet-tools", "characters")
            return preferred
        except (ImportError, AttributeError, OSError, TypeError):
            return os.path.join(os.getcwd(), "user", "default", "comfyui-violet-tools", "characters")

    @classmethod
    def list_characters(cls):
        names = set()
        paths = []
        try:
            import importlib
            folder_paths = importlib.import_module("folder_paths")  # type: ignore
            user_dir = getattr(folder_paths, "get_user_directory", None)
            if callable(user_dir):
                base_user = user_dir()
            else:
                out_dir = folder_paths.get_output_directory()
                base_user = os.path.join(os.path.dirname(str(out_dir)), "user")
            preferred = os.path.join(str(base_user), "default", "comfyui-violet-tools", "characters")
            paths = [preferred]
        except (ImportError, AttributeError, OSError, TypeError):
            paths = [os.path.join(os.getcwd(), "user", "default", "comfyui-violet-tools", "characters")]

        for p in paths:
            if os.path.exists(p):
                try:
                    for f in os.listdir(p):
                        if f.endswith('.json'):
                            names.add(f[:-5])
                except OSError:
                    continue
        return sorted(names)

    @classmethod
    def INPUT_TYPES(cls):
        chars = cls.list_characters()
        options = ["None"]
        if chars:
            options.append("random")
            options.extend(chars)
        return {
            "required": {
                "save_character": ("STRING", {"default": "", "multiline": False, "tooltip": "Enter a name to save current selections (wireless)"}),
                "load_character": (options, {"default": "None", "tooltip": "Select saved character or random"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("name",)
    FUNCTION = "select"
    CATEGORY = "Violet Tools 💅/Character"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def select(self, load_character: str, _save_character: str):
        # Just pass through the selected name for optional metadata wiring
        if load_character == "random":
            chars = self.list_characters()
            if chars:
                return (random.choice(chars),)
            return ("",)
        if load_character == "None":
            return ("",)
        return (load_character,)


NODE_CLASS_MAPPINGS = {"CharacterCurator": CharacterCurator}
NODE_DISPLAY_NAME_MAPPINGS = {"CharacterCurator": "💖 Character Curator"}
