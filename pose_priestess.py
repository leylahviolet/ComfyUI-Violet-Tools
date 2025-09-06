import yaml
import os
import random

class PosePriestess:
    """
    A ComfyUI node that generates weighted pose prompts by combining general poses, spicy poses, 
    and arm gestures. Loads pose descriptions from feature_lists/poses.yaml with separate 
    categories for general and adult content, allowing targeted pose selection with strength controls.
    """

    pose_path = os.path.join(os.path.dirname(__file__), "feature_lists", "poses.yaml")
    with open(pose_path, "r", encoding="utf-8") as f:
        pose_prompts = yaml.safe_load(f)

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        
        Returns:
            dict: Node input config with pose selections, strength sliders, and gesture options
        """
        general_poses = ["None", "Random"] + list(cls.pose_prompts.get("general_poses", {}).keys())
        spicy_poses = ["None", "Random"] + list(cls.pose_prompts.get("spicy_poses", {}).keys())
        gestures = ["None", "Random"] + cls.pose_prompts.get("ArmGestures", [])
        return {
            "required": {
                "general_pose": (general_poses, { "default": general_poses[1] }),
                "general_pose_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "spicy_pose": (spicy_poses, { "default": spicy_poses[0] }),
                "spicy_pose_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "gesture": (gestures, { "default": gestures[1] }),
                "include_gesture": ("BOOLEAN", { "default": True }),
                "extra": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("POSE_STRING",)
    RETURN_NAMES = ("pose",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED():
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def generate(self, general_pose, general_pose_strength, spicy_pose, spicy_pose_strength, gesture, include_gesture, extra):
        """
        Generate combined pose prompts with weighted blending and optional gesture inclusion.
        
        Handles random pose selection from both general and spicy categories, applies strength 
        weighting to pose descriptions, and combines multiple poses with comma separation.
        
        Args:
            general_pose (str): General pose selection or "Random"/"None"
            general_pose_strength (float): Strength multiplier for general pose (0.0-2.0)
            spicy_pose (str): Spicy pose selection or "Random"/"None" 
            spicy_pose_strength (float): Strength multiplier for spicy pose (0.0-2.0)
            gesture (str): Arm gesture selection or "Random"/"None"
            include_gesture (bool): Whether to include gesture in final prompt
            extra (str): Additional pose instructions from user
              
        Returns:
            str: Pose prompt string
        """
        general_poses = list(self.pose_prompts.get("general_poses", {}).keys())
        spicy_poses = list(self.pose_prompts.get("spicy_poses", {}).keys())

        if general_pose == "Random":
            general_pose = random.choice(general_poses) if general_poses else "None"
        if spicy_pose == "Random":
            spicy_pose = random.choice(spicy_poses) if spicy_poses else "None"

        def format_pose(pose, weight, category):
            """
            Format pose text with optional weight parentheses for prompt weighting.
            
            Args:
                pose (str): Pose key name
                weight (float): Strength multiplier
                category (str): Category ("general_poses" or "spicy_poses")
                
            Returns:
                str: Formatted pose text with or without weight syntax
            """
            text = self.pose_prompts.get(category, {}).get(pose, "")
            return f"({text}:{round(weight, 2)})" if weight < 0.99 else text

        poses = []
        if general_pose != "None" and general_pose_strength > 0:
            poses.append((general_pose, general_pose_strength, "general_poses"))
        if spicy_pose != "None" and spicy_pose_strength > 0:
            poses.append((spicy_pose, spicy_pose_strength, "spicy_poses"))

        pose_parts = [format_pose(p, w, c) for p, w, c in poses]

        gesture_part = ""
        if include_gesture and gesture != "None":
            if gesture == "Random":
                gesture = random.choice(self.pose_prompts.get("ArmGestures", []))
            gesture_part = gesture

        # Add extra text if provided
        if extra and extra.strip():
            pose_parts.append(extra.strip())

        pose = ", ".join(filter(None, pose_parts + [gesture_part]))

        return (pose.strip(),)

NODE_CLASS_MAPPINGS = {
    "PosePriestess": PosePriestess,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PosePriestess": "🤩 Pose Priestess",
}
