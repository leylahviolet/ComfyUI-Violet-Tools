import yaml
import os
import random

class PosePriestess:
    """
    A ComfyUI node that generates weighted pose prompts by combining body poses and arm gestures.
    Loads pose descriptions from feature_lists/poses.yaml and allows blending of multiple poses
    with strength controls.
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
        poses = ["None", "Random"] + [k for k in cls.pose_prompts.keys() if k != "ArmGestures"]
        gestures = ["None", "Random"] + cls.pose_prompts.get("ArmGestures", [])
        return {
            "required": {
                "pose_1": (poses, { "default": poses[1] }),
                "pose_1_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "pose_2": (poses, { "default": poses[2] }),
                "pose_2_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
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

    def generate(self, pose_1, pose_1_strength, pose_2, pose_2_strength, gesture, include_gesture, extra):
        """
        Generate combined pose prompts with weighted blending and optional gesture inclusion.
        
        Handles random pose selection, applies strength weighting to pose descriptions,
        and combines multiple poses with comma separation for prompt generation.
        
        Args:
            pose_1 (str): First pose selection or "Random"/"None"
            pose_1_strength (float): Strength multiplier for first pose (0.0-2.0)
            pose_2 (str): Second pose selection or "Random"/"None" 
            pose_2_strength (float): Strength multiplier for second pose (0.0-2.0)
            gesture (str): Arm gesture selection or "Random"/"None"
            include_gesture (bool): Whether to include gesture in final prompt
            extra (str): Additional pose instructions from user
              Returns:
            str: Pose prompt string
        """
        available_poses = [k for k in self.pose_prompts if k != "ArmGestures"]

        if pose_1 == "Random":
            pose_1 = random.choice(available_poses)
        if pose_2 == "Random":
            filtered = [p for p in available_poses if p != pose_1]
            pose_2 = random.choice(filtered) if filtered else pose_1

        def format_pose(pose, weight):
            """
            Format pose text with optional weight parentheses for prompt weighting.
            
            Args:
                pose (str): Pose key name
                weight (float): Strength multiplier
                
            Returns:
                str: Formatted pose text with or without weight syntax
            """
            text = self.pose_prompts.get(pose, "")
            return f"({text}:{round(weight, 2)})" if weight < 0.99 else text

        poses = []
        if pose_1 != "None" and pose_1_strength > 0:
            poses.append((pose_1, pose_1_strength))
        if pose_2 != "None" and pose_2_strength > 0:
            poses.append((pose_2, pose_2_strength))

        pose_parts = [format_pose(p, w) for p, w in poses]

        gesture_part = ""
        if include_gesture and gesture != "None":
            if gesture == "Random":
                gesture = random.choice(self.pose_prompts.get("ArmGestures", []))
            gesture_part = gesture        # Add extra text if provided
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
