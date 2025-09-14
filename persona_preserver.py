import json
import os
import time

class PersonaPreserver:
    """💖 Persona Preserver (Save Only)
    Save current Violet Tools selections into a named character JSON preset.

    Loading is handled by 🗝️ Persona Patcher.
    """

    @classmethod
    def get_characters_folder(cls):
        return os.path.join(os.path.dirname(__file__), "characters")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "save_character_name": ("STRING", {"multiline": False, "default": "", "tooltip": "Enter a name to save current character settings"}),
            },
            "optional": {
                "quality_include_boilerplate": ("BOOLEAN", {"default": True}),
                "quality_style": ("STRING", {"default": "Random"}),
                "quality_extra": ("STRING", {"multiline": True, "default": ""}),
                "scene_framing": ("STRING", {"default": "Random"}),
                "scene_framing_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "scene_angle": ("STRING", {"default": "Random"}),
                "scene_angle_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "scene_emotion": ("STRING", {"default": "Random"}),
                "scene_emotion_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "scene_time_of_day": ("STRING", {"default": "Random"}),
                "scene_time_of_day_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "scene_environment": ("STRING", {"default": "Random"}),
                "scene_environment_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "scene_lighting": ("STRING", {"default": "Random"}),
                "scene_lighting_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "scene_extra": ("STRING", {"multiline": True, "default": ""}),
                "glamour_hair_color": ("STRING", {"default": "Unspecified"}),
                "glamour_hair_length": ("STRING", {"default": "Unspecified"}),
                "glamour_hair_style": ("STRING", {"default": "Unspecified"}),
                "glamour_eyes": ("STRING", {"default": "Unspecified"}),
                "glamour_eyebrows": ("STRING", {"default": "Unspecified"}),
                "glamour_eyelashes": ("STRING", {"default": "Unspecified"}),
                "glamour_makeup": ("STRING", {"default": "Unspecified"}),
                "glamour_lipstick": ("STRING", {"default": "Unspecified"}),
                "glamour_extra": ("STRING", {"multiline": True, "default": ""}),
                "body_height": ("STRING", {"default": "Unspecified"}),
                "body_build": ("STRING", {"default": "Unspecified"}),
                "body_chest": ("STRING", {"default": "Unspecified"}),
                "body_waist": ("STRING", {"default": "Unspecified"}),
                "body_hips": ("STRING", {"default": "Unspecified"}),
                "body_legs": ("STRING", {"default": "Unspecified"}),
                "body_skin": ("STRING", {"default": "Unspecified"}),
                "body_extra": ("STRING", {"multiline": True, "default": ""}),
                "aesthetic_1": ("STRING", {"default": "Random"}),
                "aesthetic_1_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "aesthetic_2": ("STRING", {"default": "Random"}),
                "aesthetic_2_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "aesthetic_extra": ("STRING", {"multiline": True, "default": ""}),
                "pose_general_pose": ("STRING", {"default": "Random"}),
                "pose_general_pose_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "pose_arm_gesture": ("STRING", {"default": "Random"}),
                "pose_arm_gesture_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "pose_extra": ("STRING", {"multiline": True, "default": ""}),
                "nullifier_include_boilerplate": ("BOOLEAN", {"default": True}),
                "nullifier_extra": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("status", "character_file", "character_data_json")
    FUNCTION = "save_persona"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        return time.time()

    def save_persona(self, save_character_name="", **kwargs):
        folder = self.get_characters_folder()
        status = "💖 Persona Preserver idle - enter a name to save"
        character_file = ""
        character_json = ""
        if save_character_name and save_character_name.strip():
            name = save_character_name.strip()
            data = {
                "name": name,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "violet_tools_version": "1.3.0",
                "data": {
                    "quality": {
                        "include_boilerplate": kwargs.get("quality_include_boilerplate", True),
                        "style": kwargs.get("quality_style", "Random"),
                        "extra": kwargs.get("quality_extra", "")
                    },
                    "scene": {
                        "framing": kwargs.get("scene_framing", "Random"),
                        "framing_strength": kwargs.get("scene_framing_strength", 1.0),
                        "angle": kwargs.get("scene_angle", "Random"),
                        "angle_strength": kwargs.get("scene_angle_strength", 1.0),
                        "emotion": kwargs.get("scene_emotion", "Random"),
                        "emotion_strength": kwargs.get("scene_emotion_strength", 1.0),
                        "time_of_day": kwargs.get("scene_time_of_day", "Random"),
                        "time_of_day_strength": kwargs.get("scene_time_of_day_strength", 1.0),
                        "environment": kwargs.get("scene_environment", "Random"),
                        "environment_strength": kwargs.get("scene_environment_strength", 1.0),
                        "lighting": kwargs.get("scene_lighting", "Random"),
                        "lighting_strength": kwargs.get("scene_lighting_strength", 1.0),
                        "extra": kwargs.get("scene_extra", "")
                    },
                    "glamour": {
                        "hair_color": kwargs.get("glamour_hair_color", "Unspecified"),
                        "hair_length": kwargs.get("glamour_hair_length", "Unspecified"),
                        "hair_style": kwargs.get("glamour_hair_style", "Unspecified"),
                        "eyes": kwargs.get("glamour_eyes", "Unspecified"),
                        "eyebrows": kwargs.get("glamour_eyebrows", "Unspecified"),
                        "eyelashes": kwargs.get("glamour_eyelashes", "Unspecified"),
                        "makeup": kwargs.get("glamour_makeup", "Unspecified"),
                        "lipstick": kwargs.get("glamour_lipstick", "Unspecified"),
                        "extra": kwargs.get("glamour_extra", "")
                    },
                    "body": {
                        "height": kwargs.get("body_height", "Unspecified"),
                        "build": kwargs.get("body_build", "Unspecified"),
                        "chest": kwargs.get("body_chest", "Unspecified"),
                        "waist": kwargs.get("body_waist", "Unspecified"),
                        "hips": kwargs.get("body_hips", "Unspecified"),
                        "legs": kwargs.get("body_legs", "Unspecified"),
                        "skin": kwargs.get("body_skin", "Unspecified"),
                        "extra": kwargs.get("body_extra", "")
                    },
                    "aesthetic": {
                        "aesthetic_1": kwargs.get("aesthetic_1", "Random"),
                        "aesthetic_1_strength": kwargs.get("aesthetic_1_strength", 1.0),
                        "aesthetic_2": kwargs.get("aesthetic_2", "Random"),
                        "aesthetic_2_strength": kwargs.get("aesthetic_2_strength", 1.0),
                        "extra": kwargs.get("aesthetic_extra", "")
                    },
                    "pose": {
                        "general_pose": kwargs.get("pose_general_pose", "Random"),
                        "general_pose_strength": kwargs.get("pose_general_pose_strength", 1.0),
                        "arm_gesture": kwargs.get("pose_arm_gesture", "Random"),
                        "arm_gesture_strength": kwargs.get("pose_arm_gesture_strength", 1.0),
                        "extra": kwargs.get("pose_extra", "")
                    },
                    "negative": {
                        "include_boilerplate": kwargs.get("nullifier_include_boilerplate", True),
                        "extra": kwargs.get("nullifier_extra", "")
                    }
                }
            }
            try:
                if not os.path.exists(folder):
                    os.makedirs(folder)
                character_file = os.path.join(folder, f"{name}.json")
                with open(character_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                character_json = json.dumps(data, indent=2)
                status = f"✅ Character '{name}' saved successfully!"
            except OSError as e:
                status = f"❌ Error saving character: {e}"
        return (status, character_file, character_json)

NODE_CLASS_MAPPINGS = {"PersonaPreserver": PersonaPreserver}
NODE_DISPLAY_NAME_MAPPINGS = {"PersonaPreserver": "💖 Persona Preserver"}