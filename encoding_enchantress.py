class EncodingEnchantress:
    """
    A ComfyUI node that combines and encodes multiple prompt strings with individual strength controls.
    Supports quality, glamour, body, aesthetic, pose, and negative inputs from Violet Tools nodes.
    
    Four operation modes:
    - "closeup": Encodes glamour separately, adds closeup/portrait keywords for facial focus
    - "portrait": Combines glamour + body, puts pose + aesthetic + quality together with portrait keyword
    - "smooth blend": Combines all prompts into a single conditioning for smooth blending (default)
    - "compete combine": Creates separate conditionings for each element to compete/oscillate
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "mode": (["closeup", "portrait", "compete combine", "smooth blend"], {"default": "smooth blend"}),
                "body_strength": ("FLOAT", {
                    "default": 1.0, 
                    "min": 0.0, 
                    "max": 3.0, 
                    "step": 0.01,
                    "tooltip": "Strength for body-related prompts (not used in smooth blend)"
                }),
                "vibe_strength": ("FLOAT", {
                    "default": 1.0, 
                    "min": 0.0, 
                    "max": 3.0, 
                    "step": 0.01,
                    "tooltip": "Strength for quality + aesthetic prompts (not used in smooth blend)"
                }),
                "negative_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.01}),
            },
            "optional": {
                "quality": ("QUALITY_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "glamour": ("GLAMOUR_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "body": ("BODY_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "aesthetic": ("AESTHETIC_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "pose": ("POSE_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "nullifier": ("NULLIFIER_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "pos_text", "neg_text")
    FUNCTION = "condition"
    CATEGORY = "Violet Tools 💅"

    def encode_with_strength(self, clip, text, strength):
        """
        Encode text using CLIP with a strength multiplier applied to token weights.
        
        Args:
            clip: The CLIP model instance for tokenization and encoding
            text (str): The text prompt to encode
            strength (float): Multiplier for token weights (0.0 to 3.0+)
            
        Returns:
            list: Conditioning data in ComfyUI format [[cond, {"pooled_output": pooled}]]
        """
        if not text or not text.strip():
            tokens = clip.tokenize("")
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            return [[cond, {"pooled_output": pooled}]]
        tokens = clip.tokenize(text)
        if strength != 1.0:
            for token_list in tokens.values():
                for token_group in token_list:
                    for i, (token_id, weight) in enumerate(token_group):
                        token_group[i] = (token_id, weight * strength)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        return [[cond, {"pooled_output": pooled}]]

    def decode(self, conditioning):
        """
        Attempt to extract text information from conditioning data.
        
        Note: This is a best-effort approach since conditioning data doesn't always
        contain easily retrievable text. ComfyUI conditioning typically stores
        encoded embeddings rather than original text tokens.
        
        Args:
            conditioning: Conditioning data in ComfyUI format [[cond, {"pooled_output": pooled}]]
            
        Returns:
            str: Decoded text string if possible, or empty string if not decodable
        """
        if not conditioning or len(conditioning) == 0:
            return ""
        
        try:
            # Check if conditioning contains text metadata (some nodes store this)
            for cond_item in conditioning:
                if len(cond_item) > 1 and isinstance(cond_item[1], dict):
                    # Look for text in the conditioning metadata
                    metadata = cond_item[1]
                    if 'text' in metadata:
                        return metadata['text']
                    if 'prompt' in metadata:
                        return metadata['prompt']
            
            # If no text metadata found, return empty string
            # Note: Direct decoding from embeddings is not straightforward
            return ""
            
        except (IndexError, AttributeError, TypeError, KeyError):
            # If decoding fails for any reason, return empty string
            return ""

    def _combine_text(self, *args):
        """
        Combine multiple text strings with comma separation, filtering out empty strings.
        
        Args:
            *args: Variable number of text strings to combine
            
        Returns:
            str: Combined text string with comma separation
        """
        return ", ".join(filter(None, [s.strip() for s in args if s]))

    def _combine_conditioning(self, *conds):
        """
        Combine multiple conditioning inputs, filtering out None values.
        
        Args:
            *conds: Variable number of conditioning inputs
            
        Returns:
            list: Combined conditioning data, or empty list if no valid conditionings
        """
        valid = [c for c in conds if c]
        if not valid:
            return [[]]
        result = valid[0]
        for c in valid[1:]:
            result = result + c
        return result

    def condition(self, clip, mode, body_strength, vibe_strength, negative_strength,
                  quality="", glamour="", body="", aesthetic="", pose="", nullifier=""):
        """
        Main function that combines prompts and creates weighted conditioning data.
        
        Four operation modes:
        
        "closeup" mode:
        - Encodes glamour separately with body_strength for character emphasis
        - Combines body + pose with closeup keywords, encoded with body_strength
        - Combines quality + aesthetic with closeup keywords, encoded with vibe_strength
        - Uses _combine_conditioning to merge glamour, body, and vibe conditionings
        
        "portrait" mode:
        - Combines glamour + body into one conditioning with body_strength
        - Combines quality + pose + aesthetic with portrait keyword, encoded with vibe_strength
        - Uses _combine_conditioning to merge the two conditionings
        
        "smooth blend" mode (default):
        - Combines all prompts (quality, body, glamour, aesthetic, pose) into single conditioning
        - Encodes everything together with neutral strength (1.0) for smooth blending
        
        "compete combine" mode:
        - Creates separate conditionings for each element to compete/oscillate
        - Combines body + glamour with full body keyword, encoded with body_strength
        - Encodes pose separately with body_strength
        - Encodes aesthetic separately with vibe_strength
        - Encodes quality with vibe_strength
        - Uses _combine_conditioning to merge all separate conditionings
        
        Args:
            clip: CLIP model instance
            mode (str): Operation mode - "closeup", "portrait", "compete combine", or "smooth blend"
            body_strength (float): Strength multiplier for body-related prompts
            vibe_strength (float): Strength multiplier for quality + aesthetic combination
            negative_strength (float): Strength multiplier for negative prompt
            quality (str): Quality prompt string
            glamour (str): Glamour prompt string
            body (str): Body prompt string
            aesthetic (str): Aesthetic prompt string
            pose (str): Pose prompt string
            nullifier (str): Negative prompt string
            
        Returns:
            tuple: (positive_conditioning, negative_conditioning, positive_text, negative_text)
        """
        
        # Combine all text for reference
        pos_text = self._combine_text(quality, body, glamour, aesthetic, pose)
        
        # Encode negative
        enc_negative = self.encode_with_strength(clip, nullifier, negative_strength) if nullifier else None
        negative_combined = self._combine_conditioning(enc_negative)
        
        if mode == "closeup":
            # Closeup mode: encode glamour separately for character emphasis with closeup focus
            enc_glamour = self.encode_with_strength(clip, glamour, body_strength) if glamour else None
            
            # Combine body and pose, encode with body_strength
            body_pose_text = self._combine_text(body, pose, "portrait, closeup, face focus")
            enc_body = self.encode_with_strength(clip, body_pose_text, body_strength) if body_pose_text else None
            
            # Combine quality, aesthetic, encode with vibe_strength
            vibe_combined_text = self._combine_text(quality, aesthetic, "portrait, closeup, face focus")
            enc_vibe = self.encode_with_strength(clip, vibe_combined_text, vibe_strength) if vibe_combined_text else None
            
            # Combine all conditionings: glamour, body, and vibe
            positive_combined = self._combine_conditioning(enc_glamour, enc_body, enc_vibe)
        elif mode == "portrait":
            # Portrait mode: combine glamour + body, then put pose + aesthetic + quality together
            body_combined_text = self._combine_text(glamour, body, "(body turned to the side, face turned to viewer, dynamic portrait with upper chest visible:1.5)")
            enc_body = self.encode_with_strength(clip, body_combined_text, body_strength) if body_combined_text else None

            # Concat quality, pose, aesthetic with portrait keyword, encode with vibe_strength
            vibe_combined_text = self._combine_text(quality, pose, aesthetic, "(head and shoulders portrait, body turned to the side, face turned to viewer, dynamic portrait with upper chest visible:1.5)")
            enc_vibe = self.encode_with_strength(clip, vibe_combined_text, vibe_strength) if vibe_combined_text else None

            # Combine the two main conditionings
            positive_combined = self._combine_conditioning(enc_body, enc_vibe)
        elif mode == "compete combine":
            # Compete combine mode: create separate conditionings for each element to compete/oscillate
            body_combined_text = self._combine_text("(full body:1.2)", body, glamour)
            enc_body = self.encode_with_strength(clip, body_combined_text, body_strength) if body_combined_text else None
            
            # Encode pose with body_strength if present
            enc_pose = self.encode_with_strength(clip, pose, body_strength) if pose else None
            
            # Encode aesthetic with vibe_strength if present
            enc_aesthetic = self.encode_with_strength(clip, aesthetic, vibe_strength) if aesthetic else None

            # Encode quality with vibe_strength
            enc_vibe = self.encode_with_strength(clip, quality, vibe_strength) if quality else None

            # Combine all separate conditionings for competing behavior
            positive_combined = self._combine_conditioning(enc_vibe, enc_body, enc_pose, enc_aesthetic)
        else:
            # Smooth blend mode: encode all prompts together as single conditioning
            enc_all_positive = self.encode_with_strength(clip, pos_text, 1.0) if pos_text else None
            positive_combined = enc_all_positive if enc_all_positive else [[]]

        return (positive_combined, negative_combined, pos_text, nullifier)

NODE_CLASS_MAPPINGS = {
    "EncodingEnchantress": EncodingEnchantress,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EncodingEnchantress": "🧬 Encoding Enchantress",
}