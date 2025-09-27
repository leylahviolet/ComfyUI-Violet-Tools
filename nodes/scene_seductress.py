import yaml
import os
import random

class SceneSeductress:
    """
    A ComfyUI node that generates scene-setting prompts by combining framing, camera angle, 
    emotion, time of day, environment, and lighting elements. Loads scene descriptions from 
    feature_lists/scene_seductress.yaml with individual strength controls for each category.
    """

    scene_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_lists", "scene_seductress.yaml")
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
                "extra": ("STRING", {"multiline": True, "default": "", "label": "extra, wildcards"}),
            }
        }
        
    RETURN_TYPES = ("SCENE_STRING",)
    RETURN_NAMES = ("scene",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅/Prompt"
        
    @staticmethod
    def IS_CHANGED(**_kwargs):
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
                 time_of_day, time_of_day_strength, environment, environment_strength, lighting, lighting_strength, extra):
        # Generate combined scene prompt from selected categories with weighting and optional extra
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

        # Add extra text if provided with wildcard resolution
        def _resolve_wildcards(text: str) -> str:
            if not text or "{" not in text:
                return text.strip() if text else text
            import re
            pattern = re.compile(r"\{([^{}]+)\}")
            def repl(m):
                opts = [o.strip() for o in m.group(1).split("|") if o.strip()]
                return random.choice(opts) if opts else ""
            prev = None
            out = text
            while out != prev:
                prev = out
                out = pattern.sub(repl, out)
            return out.strip()

        if extra and extra.strip():
            parts.append(_resolve_wildcards(extra))

        scene = ", ".join(filter(None, parts))

        meta = {
            "framing": framing,
            "framing_strength": framing_strength,
            "angle": angle,
            "angle_strength": angle_strength,
            "emotion": emotion,
            "emotion_strength": emotion_strength,
            "time_of_day": time_of_day,
            "time_of_day_strength": time_of_day_strength,
            "environment": environment,
            "environment_strength": environment_strength,
            "lighting": lighting,
            "lighting_strength": lighting_strength,
            "extra": extra.strip() if isinstance(extra, str) else extra,
        }

        bundle = (scene, meta)
        return (bundle,)

NODE_CLASS_MAPPINGS = {
    "SceneSeductress": SceneSeductress,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SceneSeductress": "🎭 Scene Seductress",
}
