import yaml
import os
import random

class PosePriestess:
    """
    A ComfyUI node that generates weighted pose prompts by combining general poses, specialized 
    adult poses, and arm gestures. Loads pose descriptions from feature_lists/pose_priestess.yaml with 
    separate categories for different content types, allowing targeted pose selection with 
    individual strength controls for each category.
    """

    pose_path = os.path.join(os.path.dirname(__file__), "feature_lists", "pose_priestess.yaml")
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
        spicy_pussy_poses = ["None", "Random"] + list(cls.pose_prompts.get("spicy_pussy_poses", {}).keys())
        spicy_penis_poses = ["None", "Random"] + list(cls.pose_prompts.get("spicy_penis_poses", {}).keys())
        arm_gestures = ["None", "Random"] + list(cls.pose_prompts.get("arm_gestures", {}).keys())
        return {
            "required": {
                "general_pose": (general_poses, { "default": general_poses[1] }),
                "general_pose_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "spicy_pussy_pose": (spicy_pussy_poses, { "default": spicy_pussy_poses[0] }),
                "spicy_pussy_pose_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "spicy_penis_pose": (spicy_penis_poses, { "default": spicy_penis_poses[0] }),
                "spicy_penis_pose_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "arm_gesture": (arm_gestures, { "default": arm_gestures[0] }),
                "arm_gesture_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "extra": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("POSE_STRING",)
    RETURN_NAMES = ("pose",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅"

    @staticmethod
    def IS_CHANGED(**kwargs):
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def generate(self, general_pose, general_pose_strength, spicy_pussy_pose, spicy_pussy_pose_strength, 
                 spicy_penis_pose, spicy_penis_pose_strength, arm_gesture, arm_gesture_strength, extra):
        """
        Generate combined pose prompts with weighted blending from multiple pose categories.
        
        Handles random pose selection from general, spicy pussy, spicy penis, and arm gesture 
        categories, applies strength weighting to descriptions, and combines with comma separation.
        
        Args:
            general_pose (str): General pose selection or "Random"/"None"
            general_pose_strength (float): Strength multiplier for general pose (0.0-2.0)
            spicy_pussy_pose (str): Spicy pussy pose selection or "Random"/"None" 
            spicy_pussy_pose_strength (float): Strength multiplier for spicy pussy pose (0.0-2.0)
            spicy_penis_pose (str): Spicy penis pose selection or "Random"/"None"
            spicy_penis_pose_strength (float): Strength multiplier for spicy penis pose (0.0-2.0)
            arm_gesture (str): Arm gesture selection or "Random"/"None"
            arm_gesture_strength (float): Strength multiplier for arm gesture (0.0-2.0)
            extra (str): Additional pose instructions from user
              
        Returns:
            str: Pose prompt string
        """
        general_poses = list(self.pose_prompts.get("general_poses", {}).keys())
        spicy_pussy_poses = list(self.pose_prompts.get("spicy_pussy_poses", {}).keys())
        spicy_penis_poses = list(self.pose_prompts.get("spicy_penis_poses", {}).keys())
        arm_gestures = list(self.pose_prompts.get("arm_gestures", {}).keys())

        if general_pose == "Random":
            general_pose = random.choice(general_poses) if general_poses else "None"
        if spicy_pussy_pose == "Random":
            spicy_pussy_pose = random.choice(spicy_pussy_poses) if spicy_pussy_poses else "None"
        if spicy_penis_pose == "Random":
            spicy_penis_pose = random.choice(spicy_penis_poses) if spicy_penis_poses else "None"
        if arm_gesture == "Random":
            arm_gesture = random.choice(arm_gestures) if arm_gestures else "None"

        def format_pose(pose, weight, category):
            """
            Format pose text with optional weight parentheses for prompt weighting.
            
            Args:
                pose (str): Pose key name
                weight (float): Strength multiplier
                category (str): Category name
                
            Returns:
                str: Formatted pose text with or without weight syntax
            """
            text = self.pose_prompts.get(category, {}).get(pose, "")
            return f"({text}:{round(weight, 2)})" if weight < 0.99 else text

        poses = []
        if general_pose != "None" and general_pose_strength > 0:
            poses.append((general_pose, general_pose_strength, "general_poses"))
        if spicy_pussy_pose != "None" and spicy_pussy_pose_strength > 0:
            poses.append((spicy_pussy_pose, spicy_pussy_pose_strength, "spicy_pussy_poses"))
        if spicy_penis_pose != "None" and spicy_penis_pose_strength > 0:
            poses.append((spicy_penis_pose, spicy_penis_pose_strength, "spicy_penis_poses"))
        if arm_gesture != "None" and arm_gesture_strength > 0:
            poses.append((arm_gesture, arm_gesture_strength, "arm_gestures"))

        pose_parts = [format_pose(p, w, c) for p, w, c in poses]

        # Add extra text if provided
        if extra and extra.strip():
            pose_parts.append(extra.strip())

        pose = ", ".join(filter(None, pose_parts))

        return (pose.strip(),)

NODE_CLASS_MAPPINGS = {
    "PosePriestess": PosePriestess,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PosePriestess": "🤩 Pose Priestess",
}
