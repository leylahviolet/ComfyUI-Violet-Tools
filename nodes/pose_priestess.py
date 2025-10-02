import yaml
import os
import random
import sys

# Add node_resources directory to path for prompt_dedupe import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "node_resources"))
from prompt_dedupe import dedupe_and_clean_prompt

class PosePriestess:
    """
    A ComfyUI node that generates weighted pose prompts by combining general poses and arm gestures. 
    Loads pose descriptions from feature_lists/pose_priestess.yaml with individual strength controls 
    for each category. Users can add their own custom content via the extra text field.
    """

    pose_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "feature_lists", "pose_priestess.yaml")
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
        arm_gestures = ["None", "Random"] + list(cls.pose_prompts.get("arm_gestures", {}).keys())
        
        return {
            "required": {
                "general_pose": (general_poses, { "default": general_poses[1] }),
                "general_pose_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "arm_gesture": (arm_gestures, { "default": arm_gestures[1] }),
                "arm_gesture_strength": ("FLOAT", { "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05 }),
                "extra": ("STRING", {"multiline": True, "default": "", "label": "extra, wildcards"}),
            }
        }

    RETURN_TYPES = ("POSE_STRING",)
    RETURN_NAMES = ("pose",)
    FUNCTION = "generate"
    CATEGORY = "Violet Tools 💅/Prompt"

    @staticmethod
    def IS_CHANGED(**_kwargs):
        """
        Force node refresh on every execution to ensure random selections update properly.
        
        Returns:
            float: Current timestamp to trigger node updates
        """
        import time
        return time.time()

    def generate(self, general_pose, general_pose_strength, arm_gesture, arm_gesture_strength, extra):
        # Compose a pose prompt with optional weighting and extra
        general_poses = list(self.pose_prompts.get("general_poses", {}).keys())
        arm_gestures = list(self.pose_prompts.get("arm_gestures", {}).keys())

        if general_pose == "Random":
            general_pose = random.choice(general_poses) if general_poses else "None"
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
        if arm_gesture != "None" and arm_gesture_strength > 0:
            poses.append((arm_gesture, arm_gesture_strength, "arm_gestures"))

        pose_parts = [format_pose(p, w, c) for p, w, c in poses]

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
            pose_parts.append(_resolve_wildcards(extra))

        pose = ", ".join(filter(None, pose_parts))
        # Deduplicate phrases and clean up comma issues
        pose = dedupe_and_clean_prompt(pose)

        meta = {
            "general_pose": general_pose,
            "general_pose_strength": general_pose_strength,
            "arm_gesture": arm_gesture,
            "arm_gesture_strength": arm_gesture_strength,
            "extra": extra.strip() if isinstance(extra, str) else extra,
        }

        bundle = (pose, meta)
        return (bundle,)

NODE_CLASS_MAPPINGS = {
    "PosePriestess": PosePriestess,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PosePriestess": "🤩 Pose Priestess",
}
