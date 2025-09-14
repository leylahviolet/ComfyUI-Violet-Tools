# -*- coding: utf-8 -*-
from .quality_queen import QualityQueen
from .scene_seductress import SceneSeductress
from .body_bard import BodyBard
from .glamour_goddess import GlamourGoddess
from .aesthetic_alchemist import AestheticAlchemist
from .pose_priestess import PosePriestess
from .encoding_enchantress import EncodingEnchantress
from .negativity_nullifier import NegativityNullifier
from .persona_preserver import CharacterCreator
from .persona_patcher import CharacterCache

NODE_CLASS_MAPPINGS = {
    "EncodingEnchantress": EncodingEnchantress,
    "QualityQueen": QualityQueen,
    "SceneSeductress": SceneSeductress,
    "BodyBard": BodyBard,
    "GlamourGoddess": GlamourGoddess,
    "AestheticAlchemist": AestheticAlchemist,
    "PosePriestess": PosePriestess,
    "NegativityNullifier": NegativityNullifier,
    "CharacterCreator": CharacterCreator,
    "CharacterCache": CharacterCache
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EncodingEnchantress": "🧬 Encoding Enchantress",
    "QualityQueen": "👑 Quality Queen",
    "SceneSeductress": "🎭 Scene Seductress",
    "BodyBard": "💃 Body Bard",
    "GlamourGoddess": "✨ Glamour Goddess",
    "AestheticAlchemist": "💋 Aesthetic Alchemist",
    "PosePriestess": "🤩 Pose Priestess",
    "NegativityNullifier": "🚫 Negativity Nullifier",
    "CharacterCreator": "💖 Character Creator",
    "CharacterCache": "�️ Character Cache"
}