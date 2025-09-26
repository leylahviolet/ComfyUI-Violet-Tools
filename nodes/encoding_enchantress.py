import os

class EncodingEnchantress:
    """
    A ComfyUI node that combines and encodes multiple prompt strings with individual strength controls.
    Supports quality, scene, glamour, body, aesthetic, pose, and negative inputs from Violet Tools nodes.
    
    Four operation modes:
    - "closeup": Encodes glamour separately, adds closeup/portrait keywords for facial focus
    - "portrait": Combines glamour + body, puts pose + aesthetic + quality together with portrait keyword
    - "smooth blend": Combines all prompts into a single conditioning for smooth blending (default)
    - "compete combine": Creates separate conditionings for each element to compete/oscillate
    
    Features:
    - Token reporting: Optional detailed analysis of token usage per prompt node with 77-token chunk breakdown
    - Character system integration: Direct prompt injection from saved character profiles
    - SDXL support: Handles both 'g' and 'l' token streams with max-per-chunk merging for accurate reporting
    """

    def _ensure_requirements(self, packages, allow_auto_install=True):
        """Best-effort: import each package; if missing and allowed, attempt pip install."""
        if not allow_auto_install:
            return
        import importlib
        missing = []
        for pkg in packages:
            try:
                importlib.import_module(pkg)
            except ImportError:
                missing.append(pkg)
        if not missing:
            return
        try:
            import sys, subprocess
            cmd = [sys.executable, "-m", "pip", "install", *missing]
            subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (OSError, RuntimeError):
            # Silent failure; we'll surface ImportErrors later if they persist
            return
    

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "mode": (["closeup", "portrait", "compete combine", "smooth blend"], {"default": "smooth blend"}),
                # Toggle to optimize prompts using the Essence Algorithm (no LLM)
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
                "optimize_prompt": ("BOOLEAN", {"default": False, "tooltip": "Optimize tags using the Essence Algorithm"}),
                "token_report": ("BOOLEAN", {"default": False, "tooltip": "Generate detailed token usage report for each prompt"}),
            },
            "optional": {
                "quality": ("QUALITY_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "scene": ("SCENE_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "glamour": ("GLAMOUR_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "body": ("BODY_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "aesthetic": ("AESTHETIC_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "pose": ("POSE_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "nullifier": ("NULLIFIER_STRING", {"multiline": False, "forceInput": True, "defaultInput": True}),
                "character": ("CHARACTER_DATA", {}),
                "character_apply": ("BOOLEAN", {"default": False, "tooltip": "Generate prompts directly from character without intermediate nodes"})
            }
        }

    # Output order updated: positive, negative, tokens, character, pos, neg
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "STRING", "CHARACTER_DATA", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "tokens", "character", "pos", "neg")
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

    def _per_chunk_counts(self, stream_chunks):
        """
        Count real (non-padding) tokens in each chunk of a stream.

        ComfyUI / SDXL tokenization typically returns fixed-length (77) chunks.
        After the actual text tokens, the sequence is padded – frequently by
        repeating the end-of-text token (e.g. 49407) rather than using id 0.
        The previous implementation only excluded id==0, which caused every
        chunk to report a full 77 tokens (since padding was not filtered).

        Heuristic implemented here:
        1. Identify a trailing run of a single repeated token id at the end
           of the chunk (candidate padding id).
        2. Trim that entire trailing run (we do NOT count those).
        3. From the remaining tokens, exclude known special tokens:
           - start token (49406)
           - end token (49407)
           - explicit pad (0) if present
        4. If the heuristic would yield zero but the old method produced >0,
           fall back to the old method (safety for unusual vocabularies).

        Args:
            stream_chunks: list of chunks, each a list of (token_id, weight, ...)
        Returns:
            list[int]: Count of non-padding, non-special tokens per chunk.
        """
        out = []
        SPECIAL_IDS = {0, 49406, 49407}
        for chunk in stream_chunks:
            if not chunk:
                out.append(0)
                continue

            token_ids = [t[0] for t in chunk]

            # Identify trailing run of identical id
            pad_id = token_ids[-1]
            idx = len(token_ids) - 1
            while idx >= 0 and token_ids[idx] == pad_id:
                idx -= 1
            # All indices > idx are trailing repeats of pad_id
            trimmed_ids = token_ids[:idx+1]

            # If everything was the same token (empty / fully padded)
            if not trimmed_ids:
                out.append(0)
                continue

            # Remove a *single* final end token if present after trim stage
            # (Sometimes there is exactly one end token followed by repeats of same id.)
            if trimmed_ids and trimmed_ids[-1] in SPECIAL_IDS:
                trimmed_ids = trimmed_ids[:-1]

            # Count non-special ids
            count = sum(1 for tid in trimmed_ids if tid not in SPECIAL_IDS)

            # Fallback: if heuristic collapses everything but raw (old) count was non-zero
            if count == 0:
                legacy = sum(1 for tid in token_ids if tid != 0)
                if legacy > 0:
                    count = legacy  # fallback to previous behavior

            out.append(count)
        return out

    def _merge_streams_by_max(self, tokens_dict):
        """
        Merge multiple token streams by taking max count per chunk index.
        
        Args:
            tokens_dict: dict like {'g': [[...], [...]], 'l': [[...], ...]} (keys optional)
            
        Returns:
            list: Merged token counts using max per chunk index
        """
        g_counts = self._per_chunk_counts(tokens_dict.get('g', []))
        l_counts = self._per_chunk_counts(tokens_dict.get('l', []))
        num_chunks = max(len(g_counts), len(l_counts))
        merged = []
        for i in range(num_chunks):
            gi = g_counts[i] if i < len(g_counts) else 0
            li = l_counts[i] if i < len(l_counts) else 0
            merged.append(max(gi, li))
        return merged

    def _section(self, label, merged_counts):
        """
        Build a section of the token report for one node.
        
        Args:
            label: Node display name with emoji
            merged_counts: list of token counts per chunk
            
        Returns:
            str: Formatted section or None if empty
        """
        if not merged_counts or sum(merged_counts) == 0:
            return None  # skip empty
        lines = [label]
        for i, n in enumerate(merged_counts):
            lines.append(f"chunk {i}: {n} tokens")
        return "\n".join(lines)

    def _make_token_report(self, clip, items, enabled):
        """
        Generate comprehensive token usage report.
        
        Args:
            clip: CLIP model instance for tokenization
            items: list of (label, text) pairs to analyze
            enabled: boolean flag for report generation
            
        Returns:
            str: Formatted token report or disabled message
        """
        if not enabled:
            return "Toggle on token_report for a full report of tokens used for each prompt node of Violet Tools."
        
        # Check if CLIP is valid
        if not clip or not hasattr(clip, 'tokenize'):
            print("[Encoding Enchantress] Warning: CLIP is missing or invalid for token report")
            return "There was a problem with CLIP... Check your connections?"
            
        sections = []
        for label, text in items:
            if not text or not text.strip():
                continue
            try:
                tokens_dict = clip.tokenize(text)
                merged = self._merge_streams_by_max(tokens_dict)
                sec = self._section(label, merged)
                if sec:
                    sections.append(sec)
            except (AttributeError, KeyError, IndexError, TypeError) as e:
                print(f"[Encoding Enchantress] token report error in '{label}': {e}")
                continue
        return "\n\n".join(sections)

    def _filter_scene_framing(self, scene_text):
        """
        Remove framing-related terms from scene text to avoid conflicts in closeup/portrait modes.
        Dynamically loads framing terms from scene_seductress.yaml to stay in sync with user edits.
        
        Args:
            scene_text (str): Original scene text that may contain framing elements
            
        Returns:
            str: Scene text with framing elements removed
        """
        if not scene_text:
            return scene_text
            
        # Load framing terms dynamically from scene_seductress.yaml
        framing_terms = self._load_framing_terms()
        
        # Split scene text into parts
        parts = [part.strip() for part in scene_text.split(',')]
        filtered_parts = []
        
        for part in parts:
            # Check if this part contains framing terms (with strength notation support)
            part_lower = part.lower()
            
            # Handle weighted terms like "(portrait:1.2)" or "portrait"
            is_framing = False
            for term in framing_terms:
                if term in part_lower:
                    # Check if it's actually a framing term and not part of something else
                    # Simple check: if the term appears as a standalone word or in parentheses
                    if (f" {term} " in f" {part_lower} " or 
                        part_lower.startswith(f"({term}:") or 
                        part_lower == term or
                        part_lower.startswith(f"{term}:")):
                        is_framing = True
                        break
            
            if not is_framing:
                filtered_parts.append(part)
        
        return ", ".join(filtered_parts)

    def _load_framing_terms(self):
        """
        Load framing and angle terms from scene_seductress.yaml file.
        
        Returns:
            list: List of framing-related terms to filter out (case-insensitive)
        """
        try:
            # Lazy import yaml so the node loads even if PyYAML isn't installed
            try:
                import yaml  # type: ignore
            except ImportError as exc:
                raise FileNotFoundError("PyYAML not available") from exc

            # Get the path to the YAML file
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            yaml_path = os.path.join(current_dir, "feature_lists", "scene_seductress.yaml")
            
            # Load the YAML file
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            framing_terms = []
            
            # Extract framing terms (both keys and values)
            if 'framing' in data:
                for key, value in data['framing'].items():
                    framing_terms.append(key.lower())
                    framing_terms.append(value.lower())
            
            # Extract angle terms (also framing-related)
            if 'angle' in data:
                for key, value in data['angle'].items():
                    framing_terms.append(key.lower())
                    framing_terms.append(value.lower())
            
            # Add some common close-up variants not in the YAML
            additional_terms = [
                "close-up", "closeup", "medium shot", "long shot",
                "extreme close-up", "extreme closeup", "bust shot", "waist shot"
            ]
            framing_terms.extend(additional_terms)
            
            return framing_terms
            
        except (FileNotFoundError, KeyError, OSError, TypeError) as e:
            # Fallback to hardcoded list if YAML loading fails
            print(f"Warning: Could not load framing terms from YAML ({e}), using fallback list")
            return [
                "portrait", "upper body", "cowboy shot", "cowboy-shot", "feet out of frame", 
                "full body", "wide shot", "very wide shot", "lower body", "head out of frame", 
                "eyes out of frame", "close-up", "closeup", "medium shot", "long shot",
                "extreme close-up", "extreme closeup", "bust shot", "waist shot",
                "panoramic view", "panoramic", "bird's eye view", "birds eye view",
                "top-down perspective", "top down perspective", "aerial shot", "aerial view",
                "overhead shot", "overhead view", "worm's eye view", "low angle shot",
                "high angle shot", "dutch angle", "profile shot", "three-quarter view",
                "front view", "back view", "side view", "cropped", "framing"
            ]

    def _check_for_cowboys(self, scene_text):
        """
        Check if scene text contains "cowboy shot" or "cowboy-shot" framing terms.
        Returns "cowboy" to add to negative prompt if found.
        
        Args:
            scene_text (str): Scene text to check for cowboy shot framing
            
        Returns:
            str: "cowboy" if cowboy shot framing is detected, empty string otherwise
        """
        if not scene_text:
            return ""
            
        scene_lower = scene_text.lower()
        if "cowboy shot" in scene_lower or "cowboy-shot" in scene_lower:
            return "cowboy"
        
        return ""

    def condition(self, clip, mode, body_strength, vibe_strength, negative_strength, optimize_prompt, token_report,
                  quality="",
                  scene="",
                  glamour="",
                  body="",
                  aesthetic="",
                  pose="",
                  nullifier="",
                  character=None, character_apply=False):
        """
        Main function that combines prompts and creates weighted conditioning data.
        
        Four operation modes:
        
        "closeup" mode:
        - Encodes glamour separately with body_strength for character emphasis
        - Combines body + pose with closeup keywords, encoded with body_strength
        - Combines quality + scene + aesthetic with closeup keywords, encoded with vibe_strength
        - Uses _combine_conditioning to merge glamour, body, and vibe conditionings
        
        "portrait" mode:
        - Combines glamour + body into one conditioning with body_strength
        - Combines quality + scene + pose + aesthetic with portrait keyword, encoded with vibe_strength
        - Uses _combine_conditioning to merge the two conditionings
        
        "smooth blend" mode (default):
        - Combines all prompts (quality, scene, body, glamour, aesthetic, pose) into single conditioning
        - Encodes everything together with neutral strength (1.0) for smooth blending
        
        "compete combine" mode:
        - Creates separate conditionings for each element to compete/oscillate
        - Combines body + glamour with full body keyword, encoded with body_strength
        - Encodes pose separately with body_strength
        - Encodes aesthetic separately with vibe_strength
        - Encodes quality + scene with vibe_strength
        - Uses _combine_conditioning to merge all separate conditionings
        
        Args:
            clip: CLIP model instance
            mode (str): Operation mode - "closeup", "portrait", "compete combine", or "smooth blend"
            body_strength (float): Strength multiplier for body-related prompts
            vibe_strength (float): Strength multiplier for quality + aesthetic combination
            negative_strength (float): Strength multiplier for negative prompt
            quality (str): Quality prompt string
            scene (str): Scene prompt string
            glamour (str): Glamour prompt string
            body (str): Body prompt string
            aesthetic (str): Aesthetic prompt string
            pose (str): Pose prompt string
            nullifier (str): Negative prompt string
            
        Returns:
            tuple: (positive, negative, tokens, character, pos, neg)
        """
        
        # If character_apply is true, pull segments straight from character when missing
        if character_apply and character and isinstance(character, dict):
            cd = character.get("data", {})
            # Only inject if the provided segment is blank (user didn't connect node) to avoid overwriting explicit inputs
            if not quality and "quality" in cd:
                quality = cd["quality"].get("text", "")
            if not scene and "scene" in cd:
                scene = cd["scene"].get("text", "")
            if not glamour and "glamour" in cd:
                glamour = cd["glamour"].get("text", "")
            if not body and "body" in cd:
                body = cd["body"].get("text", "")
            if not aesthetic and "aesthetic" in cd:
                aesthetic = cd["aesthetic"].get("text", "")
            if not pose and "pose" in cd:
                pose = cd["pose"].get("text", "")
            if not nullifier and "negative" in cd:
                nullifier = cd["negative"].get("text", "")

        # Accept either plain string or (text, meta) bundle and unwrap EARLY
        def _unwrap_bundle(val):
            if isinstance(val, (list, tuple)) and len(val) == 2 and isinstance(val[1], dict):
                return val[0], val[1]
            return val, None

        quality, quality_meta = _unwrap_bundle(quality)
        scene, scene_meta = _unwrap_bundle(scene)
        glamour, glamour_meta = _unwrap_bundle(glamour)
        body, body_meta = _unwrap_bundle(body)
        aesthetic, aesthetic_meta = _unwrap_bundle(aesthetic)
        pose, pose_meta = _unwrap_bundle(pose)
        nullifier, negative_meta = _unwrap_bundle(nullifier)

        # Normalize to strings for downstream processing
        def _ensure_str(v):
            return v if isinstance(v, str) else ("" if v is None else str(v))
        quality = _ensure_str(quality)
        scene = _ensure_str(scene)
        glamour = _ensure_str(glamour)
        body = _ensure_str(body)
        aesthetic = _ensure_str(aesthetic)
        pose = _ensure_str(pose)
        nullifier = _ensure_str(nullifier)

        # Save originals for token savings calculations (strings only)
        original_segments = {
            "quality": quality or "", "scene": scene or "", "glamour": glamour or "",
            "body": body or "", "aesthetic": aesthetic or "", "pose": pose or "",
            "negative": nullifier or "",
        }

        # Combine all text for reference (pre-processing)
        pos_text = self._combine_text(quality, scene, body, glamour, aesthetic, pose)

        # Optional prompt processing pipeline (Essence Algorithm only)
        processor_choice = "Essence Algorithm" if optimize_prompt else "None"

        # Token counts before processing
        def _count_tokens(text: str) -> int:
            if not text:
                return 0
            try:
                tokens = clip.tokenize(text)
                merged = self._merge_streams_by_max(tokens)
                return sum(merged)
            except (AttributeError, KeyError, IndexError, TypeError, RuntimeError):
                return 0

        pre_counts = {k: _count_tokens(v) for k, v in original_segments.items()}

        if processor_choice != "None":
            try:
                # Use bundled algorithm-only consolidator
                # Ensure dependency for fuzzy matching exists
                self._ensure_requirements(["rapidfuzz"], allow_auto_install=False)
                import importlib.util, sys
                pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                base_dir = os.path.join(pkg_root, "node_resources")
                consolidator_path = os.path.join(base_dir, "prompt_consolidator.py")
                spec = importlib.util.spec_from_file_location("vt_prompt_consolidator", consolidator_path)
                if not spec or not spec.loader:
                    raise ImportError(f"Unable to load consolidator at {consolidator_path}")
                # Reuse a single loaded module to preserve global caches and avoid repeated logs
                if spec.name in sys.modules:
                    pc = sys.modules[spec.name]
                else:
                    pc = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = pc
                    spec.loader.exec_module(pc)  # type: ignore

                cfg = pc.ConsolidationConfig(base_dir, sfw_mode=False)

                def process_one(text: str) -> str:
                    if not text:
                        return ""
                    if processor_choice == "Essence Algorithm":
                        return pc.consolidate_algorithmic(text, cfg)
                    else:  # None
                        return text

                # Apply to positive segments only; negative untouched here
                quality = process_one(quality)
                scene = process_one(scene)
                glamour = process_one(glamour)
                body = process_one(body)
                aesthetic = process_one(aesthetic)
                pose = process_one(pose)

                # Recompute combined text
                pos_text = self._combine_text(quality, scene, body, glamour, aesthetic, pose)
            except ImportError as e:
                print(f"[Encoding Enchantress] Essence processing ImportError: {e}.")
            except (AttributeError, FileNotFoundError, OSError, RuntimeError, TypeError, ValueError) as e:
                print(f"[Encoding Enchantress] Essence processing error: {e}")
        
        # Check for cowboy shot framing and add "cowboy" to negative if needed
        cowboy_negative = self._check_for_cowboys(scene)
        combined_negative = self._combine_text(nullifier, cowboy_negative)
        
        # Encode negative
        enc_negative = self.encode_with_strength(clip, combined_negative, negative_strength) if combined_negative else None
        negative_combined = self._combine_conditioning(enc_negative)
        
        if mode == "closeup":
            # Closeup mode: encode glamour separately for character emphasis with closeup focus
            # Filter framing from scene to avoid conflicts with closeup framing
            filtered_scene = self._filter_scene_framing(scene)
            
            enc_glamour = self.encode_with_strength(clip, glamour, body_strength) if glamour else None
            
            # Combine body and pose, encode with body_strength
            body_pose_text = self._combine_text(body, pose, "portrait, closeup, face focus")
            enc_body = self.encode_with_strength(clip, body_pose_text, body_strength) if body_pose_text else None
            
            # Combine quality, filtered scene, aesthetic, encode with vibe_strength
            vibe_combined_text = self._combine_text(quality, filtered_scene, aesthetic, "portrait, closeup, face focus")
            enc_vibe = self.encode_with_strength(clip, vibe_combined_text, vibe_strength) if vibe_combined_text else None
            
            # Combine all conditionings: glamour, body, and vibe
            positive_combined = self._combine_conditioning(enc_glamour, enc_body, enc_vibe)
        elif mode == "portrait":
            # Portrait mode: body dominates, quality, scene, and aesthetics support
            # Filter framing from scene to avoid conflicts with portrait framing
            filtered_scene = self._filter_scene_framing(scene)
            
            # Combine body and pose with portrait focus, encode with body_strength
            body_pose_text = self._combine_text(body, pose, "portrait")
            enc_body = self.encode_with_strength(clip, body_pose_text, body_strength) if body_pose_text else None
            
            # Combine glamour, quality, filtered scene, and aesthetic, encode with vibe_strength
            vibe_combined_text = self._combine_text(glamour, quality, filtered_scene, aesthetic, "portrait")
            enc_vibe = self.encode_with_strength(clip, vibe_combined_text, vibe_strength) if vibe_combined_text else None
            
            # Combine body and vibe conditionings
            positive_combined = self._combine_conditioning(enc_body, enc_vibe)
        elif mode == "compete combine":
            # Compete combine mode: create separate conditionings for each element to compete/oscillate
            body_combined_text = self._combine_text("(full body:1.2)", body, glamour)
            enc_body = self.encode_with_strength(clip, body_combined_text, body_strength) if body_combined_text else None
            
            # Encode pose with body_strength if present
            enc_pose = self.encode_with_strength(clip, pose, body_strength) if pose else None
            
            # Encode aesthetic with vibe_strength if present
            enc_aesthetic = self.encode_with_strength(clip, aesthetic, vibe_strength) if aesthetic else None

            # Encode quality + scene with vibe_strength
            enc_vibe = self.encode_with_strength(clip, self._combine_text(quality, scene), vibe_strength) if quality or scene else None

            # Combine all separate conditionings for competing behavior
            positive_combined = self._combine_conditioning(enc_vibe, enc_body, enc_pose, enc_aesthetic)
        else:
            # Smooth blend mode: encode all prompts together as single conditioning
            enc_all_positive = self.encode_with_strength(clip, pos_text, 1.0) if pos_text else None
            positive_combined = enc_all_positive if enc_all_positive else [[]]

        def _merge_meta(text_value, meta_value):
            base = {"text": text_value} if text_value else {}
            if isinstance(meta_value, dict):
                # If node provided a plain dict, merge its keys
                base.update({k: v for k, v in meta_value.items() if k != "text"})
            elif isinstance(meta_value, (list, tuple)) and len(meta_value) >= 1 and isinstance(meta_value[0], dict):
                # Defensive: handle unusual wrappers (shouldn't occur)
                base.update(meta_value[0])
            return base

        character_output = {
            "data": {
                "quality": _merge_meta(quality, quality_meta),
                "scene": _merge_meta(scene, scene_meta),
                "glamour": _merge_meta(glamour, glamour_meta),
                "body": _merge_meta(body, body_meta),
                "aesthetic": _merge_meta(aesthetic, aesthetic_meta),
                "pose": _merge_meta(pose, pose_meta),
                "negative": _merge_meta(nullifier, negative_meta),
            }
        }

        # Generate token report
        token_items = [
            ("👑 Quality Queen", quality),
            ("🎭 Scene Seductress", scene),
            ("✨ Glamour Goddess", glamour),
            ("💃 Body Bard", body),
            ("💋 Aesthetic Alchemist", aesthetic),
            ("🤩 Pose Priestess", pose),
            ("🚫 Negativity Nullifier", nullifier)
        ]
        
        token_report_text = self._make_token_report(clip, token_items, token_report)

        # Optional token savings suffix when processor active
        if optimize_prompt and token_report:
            def _only_text(val):
                # Always return a string
                if isinstance(val, (list, tuple)) and len(val) == 2 and isinstance(val[1], dict):
                    t = val[0]
                    return t if isinstance(t, str) else ""
                return val if isinstance(val, str) else ""
            post_segments = {
                "quality": _only_text(quality), "scene": _only_text(scene), "glamour": _only_text(glamour),
                "body": _only_text(body), "aesthetic": _only_text(aesthetic), "pose": _only_text(pose),
                "negative": _only_text(nullifier),
            }
            post_counts = {k: _count_tokens(v) for k, v in post_segments.items()}
            savings_lines = ["— Token savings (approx):"]
            total_pre = total_post = 0
            for k in ("quality","scene","glamour","body","aesthetic","pose"):
                a = pre_counts.get(k, 0); b = post_counts.get(k, 0)
                total_pre += a; total_post += b
                if a or b:
                    savings_lines.append(f"{k}: {a} → {b} (-{max(a-b,0)})")
            savings_lines.append(f"total: {total_pre} → {total_post} (-{max(total_pre-total_post,0)})")
            token_report_text = token_report_text + "\n\n" + "\n".join(savings_lines)

        # New return order matches updated RETURN_NAMES
        return (positive_combined, negative_combined, token_report_text, character_output, pos_text, combined_negative)

NODE_CLASS_MAPPINGS = {
    "EncodingEnchantress": EncodingEnchantress,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EncodingEnchantress": "🧬 Encoding Enchantress",
}