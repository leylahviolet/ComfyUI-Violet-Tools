import yaml
import os
import random

class SceneSeductress:
    """
    A ComfyUI node that generates scene-setting prompts by combining framing, camera angle, 
    emotion, time of day, environment, and lighting elements. Loads scene descriptions from 
    feature_lists/scene_seductress.yaml with individual strength controls for each category.
    """

    scene_path = os.path.join(os.path.dirname(__file__), "feature_lists", "scene_seductress.yaml")
    with open(scene_path, "r", encoding="utf-8") as f:
        scene_data = yaml.safe_load(f)

    framing = scene_data["framing"]
    angle = scene_data["angle"]
    emotion = scene_data["emotion"]
    time_of_day = scene_data["time_of_day"]
    environment = scene_data["environment"]
    lighting = scene_data["lighting"]

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        
        Returns:
            dict: Node input config with scene selections, strength sliders, and extra text
        """
        
        return {
            "required": {
                "framing": (["None", "Random"] + list(cls.framing.keys()), {"default": "Random"}),
                "framing_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "angle": (["None", "Random"] + list(cls.angle.keys()), {"default": "Random"}),
                "angle_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "emotion": (["None", "Random"] + list(cls.emotion.keys()), {"default": "Random"}),
                "emotion_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "time_of_day": (["None", "Random"] + list(cls.time_of_day.keys()), {"default": "Random"}),
                "time_of_day_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "environment": (["None", "Random"] + list(cls.environment.keys()), {"default": "Random"}),
                "environment_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "lighting": (["None", "Random"] + list(cls.lighting.keys()), {"default": "Random"}),
                "lighting_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "extra": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "character_data": ("CHARACTER_DATA", {}),
                "character_apply": ("BOOLEAN", {"default": False, "tooltip": "Apply loaded character scene overrides"})
            }
        }
        
    RETURN_TYPES = ("SCENE_STRING",)
    RETURN_NAMES = ("scene",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅"
        
    @staticmethod
    def IS_CHANGED(**kwargs):
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Args:
            **kwargs: Node input parameters (ignored)
            
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def generate(self, framing, framing_strength, angle, angle_strength, emotion, emotion_strength, 
                 time_of_day, time_of_day_strength, environment, environment_strength, lighting, lighting_strength, extra,
                 character_data=None, character_apply=False):
        if character_apply and character_data and isinstance(character_data, dict):
            sd = character_data.get("data", {}).get("scene", {})
            if sd:
                framing = sd.get("framing", framing)
                framing_strength = sd.get("framing_strength", framing_strength)
                angle = sd.get("angle", angle)
                angle_strength = sd.get("angle_strength", angle_strength)
                emotion = sd.get("emotion", emotion)
                emotion_strength = sd.get("emotion_strength", emotion_strength)
                time_of_day = sd.get("time_of_day", time_of_day)
                time_of_day_strength = sd.get("time_of_day_strength", time_of_day_strength)
                environment = sd.get("environment", environment)
                environment_strength = sd.get("environment_strength", environment_strength)
                lighting = sd.get("lighting", lighting)
                lighting_strength = sd.get("lighting_strength", lighting_strength)
                if sd.get("extra"):
                    extra = sd.get("extra")
        """
        Generate combined scene prompts with weighted blending from multiple scene categories.
        
        Handles random selection from framing, angle, emotion, time of day, environment, and lighting
        categories, applies strength weighting to descriptions, and combines with comma separation.
        
        Args:
            framing (str): Framing selection or "Random"/"None"
            framing_strength (float): Strength multiplier for framing (0.0-2.0)
            angle (str): Camera angle selection or "Random"/"None"
            angle_strength (float): Strength multiplier for angle (0.0-2.0)
            emotion (str): Emotion selection or "Random"/"None"
            emotion_strength (float): Strength multiplier for emotion (0.0-2.0)
            time_of_day (str): Time of day selection or "Random"/"None"
            time_of_day_strength (float): Strength multiplier for time of day (0.0-2.0)
            environment (str): Environment selection or "Random"/"None"
            environment_strength (float): Strength multiplier for environment (0.0-2.0)
            lighting (str): Lighting selection or "Random"/"None"
            lighting_strength (float): Strength multiplier for lighting (0.0-2.0)
            extra (str): Additional scene instructions from user
              
        Returns:
            str: Scene prompt string
        """
        # Get all scene lists
        frames = list(self.framing.keys())
        angles = list(self.angle.keys())
        emotions = list(self.emotion.keys())
        times_of_day = list(self.time_of_day.keys())
        environments = list(self.environment.keys())
        lights = list(self.lighting.keys())

        # Handle random selections
        if framing == "Random":
            framing = random.choice(frames) if frames else "None"
        if angle == "Random":
            angle = random.choice(angles) if angles else "None"
        if emotion == "Random":
            emotion = random.choice(emotions) if emotions else "None"
        if time_of_day == "Random":
            time_of_day = random.choice(times_of_day) if times_of_day else "None"
        if environment == "Random":
            environment = random.choice(environments) if environments else "None"
        if lighting == "Random":
            lighting = random.choice(lights) if lights else "None"

        def format_scene_element(element, weight, category_dict):
            """
            Format scene element text with optional weight parentheses for prompt weighting.
            
            Args:
                element (str): Element key name
                weight (float): Strength multiplier
                category_dict (dict): Category dictionary to look up values
                
            Returns:
                str: Formatted element text with or without weight syntax
            """
            if element == "None" or weight <= 0:
                return ""
            text = category_dict.get(element, element)
            return f"({text}:{round(weight, 2)})" if weight != 1.0 else text

        parts = []
        
        # Add each scene element with its strength
        framing_text = format_scene_element(framing, framing_strength, self.framing)
        if framing_text:
            parts.append(framing_text)
            
        angle_text = format_scene_element(angle, angle_strength, self.angle)
        if angle_text:
            parts.append(angle_text)
            
        emotion_text = format_scene_element(emotion, emotion_strength, self.emotion)
        if emotion_text:
            parts.append(emotion_text)
            
        time_text = format_scene_element(time_of_day, time_of_day_strength, self.time_of_day)
        if time_text:
            parts.append(time_text)
            
        environment_text = format_scene_element(environment, environment_strength, self.environment)
        if environment_text:
            parts.append(environment_text)
            
        lighting_text = format_scene_element(lighting, lighting_strength, self.lighting)
        if lighting_text:
            parts.append(lighting_text)

        # Add extra text if provided
        if extra and extra.strip():
            parts.append(extra.strip())

        scene = ", ".join(filter(None, parts))
        
        # Add BREAK for prompt segmentation
        if scene:
            scene += ", BREAK"

        return (scene,)

NODE_CLASS_MAPPINGS = {
    "SceneSeductress": SceneSeductress,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SceneSeductress": "🎭 Scene Seductress",
}
