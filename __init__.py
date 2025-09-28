# -*- coding: utf-8 -*-
import os
from .nodes.quality_queen import QualityQueen
from .nodes.scene_seductress import SceneSeductress
from .nodes.body_bard import BodyBard
from .nodes.glamour_goddess import GlamourGoddess
from .nodes.aesthetic_alchemist import AestheticAlchemist
from .nodes.pose_priestess import PosePriestess
from .nodes.encoding_enchantress import EncodingEnchantress
from .nodes.negativity_nullifier import NegativityNullifier
from .nodes.character_curator import CharacterCurator
from .nodes.oracle_override import OracleOverride
from .utility_nodes.save_siren import SaveSiren

# Enable web extensions
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

# Side-effect import: registers /violet/character endpoint and on-prompt handler
try:
    from .node_resources import character_sync  # noqa: F401
except (ImportError, RuntimeError):
    # Non-fatal: if server isn't available in this context, skip silently
    pass

NODE_CLASS_MAPPINGS = {
    "EncodingEnchantress": EncodingEnchantress,
    "QualityQueen": QualityQueen,
    "SceneSeductress": SceneSeductress,
    "BodyBard": BodyBard,
    "GlamourGoddess": GlamourGoddess,
    "AestheticAlchemist": AestheticAlchemist,
    "PosePriestess": PosePriestess,
    "NegativityNullifier": NegativityNullifier,
    "CharacterCurator": CharacterCurator,
    "OracleOverride": OracleOverride,
    "SaveSiren": SaveSiren,
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
    "CharacterCurator": "💖 Character Curator",
    "OracleOverride": "🔮 Oracle's Override",
    "SaveSiren": "🧜‍♀️ Save Siren",
}
