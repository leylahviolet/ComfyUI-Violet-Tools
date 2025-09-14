import yaml
import os
import random

class AestheticAlchemist:
    """
    A ComfyUI node that generates aesthetic prompts by blending multiple style aesthetics.
    Loads aesthetic definitions from feature_lists/aesthetic_alchemist.yaml and creates weighted positive prompts.
    """
    
    style_path = os.path.join(os.path.dirname(__file__), "feature_lists", "aesthetic_alchemist.yaml")
    with open(style_path, "r", encoding="utf-8") as f:
        style_prompts = yaml.safe_load(f)

    @classmethod
    def INPUT_TYPES(cls):
        """
        Define the input parameters for the ComfyUI node interface.
        
        Returns:
            dict: Node input configuration with aesthetic selections and strength controls
        """
        aesthetics = ["None", "Random"] + list(cls.style_prompts.keys())
        return {
            "required": {
                "aesthetic_1": (aesthetics, {"default": aesthetics[1]}),
                "aesthetic_1_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "aesthetic_2": (aesthetics, {"default": aesthetics[2]}),
                "aesthetic_2_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.05}),
                "extra": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "character": ("CHARACTER_DATA", {}),
                "character_apply": ("BOOLEAN", {"default": False, "tooltip": "Apply loaded character aesthetic overrides"})
            }
        }

    RETURN_TYPES = ("AESTHETIC_STRING",)
    RETURN_NAMES = ("aesthetic",)
    FUNCTION = "infuse"
    CATEGORY = "Violet Tools 💅/Prompt"
    
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

    def infuse(self, aesthetic_1, aesthetic_2, aesthetic_1_strength, aesthetic_2_strength, extra, character=None, character_apply=False):
        if character_apply and character and isinstance(character, dict):
            ad = character.get("data", {}).get("aesthetic", {})
            if ad:
                aesthetic_1 = ad.get("aesthetic_1", aesthetic_1)
                aesthetic_1_strength = ad.get("aesthetic_1_strength", aesthetic_1_strength)
                aesthetic_2 = ad.get("aesthetic_2", aesthetic_2)
                aesthetic_2_strength = ad.get("aesthetic_2_strength", aesthetic_2_strength)
                if ad.get("extra"):
                    extra = ad.get("extra")
        """
        Generate aesthetic prompts by optionally blending selected styles.
        
        Handles random aesthetic selection, applies strength weighting to style elements,
        and combines positive prompts based on aesthetic definitions.
        
        Args:
            aesthetic_1 (str): First aesthetic selection or "Random"/"None"
            aesthetic_1_strength (float): Strength multiplier for first aesthetic (0.0-2.0)
            aesthetic_2 (str): Second aesthetic selection or "Random"/"None"
            aesthetic_2_strength (float): Strength multiplier for second aesthetic (0.0-2.0)
            extra (string): Additional aesthetic instructions from user
              Returns:
            str: Aesthetic prompt string
        """
        # Grab all real styles
        available_styles = list(self.style_prompts.keys())

        # Handle randomization logic
        selected_1 = aesthetic_1
        selected_2 = aesthetic_2

        if aesthetic_1 == "Random":
            selected_1 = random.choice(available_styles)

        if aesthetic_2 == "Random":
            filtered = [s for s in available_styles if s != selected_1]
            selected_2 = random.choice(filtered) if filtered else selected_1

        def weighted_text(style, weight):
            """
            Format aesthetic text with optional weight parentheses for prompt weighting.
            
            Args:
                style (str): Aesthetic style name
                weight (float): Strength multiplier
                
            Returns:
                str: Formatted aesthetic text with or without weight syntax
            """
            base = self.style_prompts.get(style, "")
            if not base:
                return ""
            return f"({base}:{round(weight, 2)})" if weight < 0.99 else base

        styles = []
        if selected_1 != "None" and aesthetic_1_strength > 0.0:
            styles.append((selected_1, aesthetic_1_strength))
        if selected_2 != "None" and aesthetic_2_strength > 0.0:
            styles.append((selected_2, aesthetic_2_strength))

        pos_parts = [weighted_text(style, weight) for style, weight in styles]

        # Add extra text if provided
        if extra and extra.strip():
            pos_parts.append(extra.strip())

        aesthetic = ", ".join(filter(None, pos_parts))
        
        # Add BREAK for prompt segmentation
        if aesthetic:
            aesthetic += ", BREAK"

        return (aesthetic,)

NODE_CLASS_MAPPINGS = {
    "AestheticAlchemist": AestheticAlchemist,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AestheticAlchemist": "💋 Aesthetic Alchemist",
}
