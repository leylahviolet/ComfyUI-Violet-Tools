from persona_patcher import PersonaPatcher
from quality_queen import QualityQueen
from scene_seductress import SceneSeductress
from glamour_goddess import GlamourGoddess
from body_bard import BodyBard
from aesthetic_alchemist import AestheticAlchemist
from pose_priestess import PosePriestess
from negativity_nullifier import NegativityNullifier

"""Simple dry-run test (no CLIP encoding) to verify character_data overrides.
Run with: python test_persona_flow.py <character_name>
"""
import sys

if len(sys.argv) < 2:
    print("Usage: python test_persona_flow.py <character_name>")
    sys.exit(1)

character = sys.argv[1]
pp = PersonaPatcher()
character_data, name, status = pp.patch(character, False)
print(status)
if not character_data:
    sys.exit(1)

# Instantiate nodes
qq = QualityQueen()
ss = SceneSeductress()
gg = GlamourGoddess()
bb = BodyBard()
aa = AestheticAlchemist()
ppose = PosePriestess()
neg = NegativityNullifier()

# Invoke each with character_apply
quality, = qq.generate(include_boilerplate=True, style="Random", extra="", character_data=character_data, character_apply=True)
scene, = ss.generate(framing="Random", framing_strength=1.0, angle="Random", angle_strength=1.0,
                     emotion="Random", emotion_strength=1.0, time_of_day="Random", time_of_day_strength=1.0,
                     environment="Random", environment_strength=1.0, lighting="Random", lighting_strength=1.0,
                     extra="", character_data=character_data, character_apply=True)

# Build kwargs for glamour features from YAML keys stored in character
# We just call with Unspecified defaults; overrides will apply
kwargs_glam = {k: "Unspecified" for k in gg.FEATURES.keys()}
kwargs_glam['extra'] = ""
glamour, = gg.invoke(character_data=character_data, character_apply=True, **kwargs_glam)

kwargs_body = {k: "Unspecified" for k in bb.FEATURES.keys()}
kwargs_body['extra'] = ""
body, = bb.compose(character_data=character_data, character_apply=True, **kwargs_body)

aesthetic, = aa.infuse(aesthetic_1="Random", aesthetic_2="Random", aesthetic_1_strength=1.0, aesthetic_2_strength=1.0,
                       extra="", character_data=character_data, character_apply=True)
pose, = ppose.generate(general_pose="Random", general_pose_strength=1.0, arm_gesture="Random", arm_gesture_strength=1.0,
                       extra="", character_data=character_data, character_apply=True)
nullifier, = neg.purify(include_boilerplate=True, extra="", character_data=character_data, character_apply=True)

print("\n--- RESULTING PROMPT SEGMENTS ---")
print("QUALITY:", quality)
print("SCENE:", scene)
print("GLAMOUR:", glamour)
print("BODY:", body)
print("AESTHETIC:", aesthetic)
print("POSE:", pose)
print("NEGATIVE:", nullifier)
