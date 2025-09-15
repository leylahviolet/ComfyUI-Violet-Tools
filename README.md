# ComfyUI Violet Tools 💅

[![Version](https://img.shields.io/badge/version-1.4.0-8A2BE2?style=for-the-badge&logoColor=white)](CHANGELOG.md)

A collection of aesthetic-focused custom nodes for ComfyUI that enhance AI image generation with sophisticated style and prompt management capabilities. These nodes provide curated aesthetic options, quality controls, persona-preserving workflows, and prompt enhancement tools designed for creating high-quality, stylistically consistent AI-generated images.

## Features

### 🧬 Encoding Enchantress

Advanced text encoding and prompt processing node for enhanced prompt interpretation with comprehensive token analysis:

- Four encoding modes: closeup, portrait, smooth blend, and compete combine
- Individual strength controls for different prompt elements
- Character system integration for direct prompt injection
- **Token Report System**: Detailed analysis of token usage per Violet Tools node
  - Shows 77-token chunk breakdown for each prompt component
  - SDXL support with merged stream analysis
  - Optional reporting to avoid performance impact when disabled

### 👑 Quality Queen

Generates quality prompts with boilerplate tags and customizable style options. Includes:

- Boilerplate quality tags for consistent high-quality outputs
- Multiple predefined style options
- Custom text integration

### 💃 Body Bard

Specialized node for body feature and pose description generation with detailed anatomical and postural options.

### ✨ Glamour Goddess

Hair and makeup styling node that creates detailed aesthetic descriptions:

- Modular hair styling options
- Comprehensive makeup choices
- Randomization and manual selection modes

### 💋 Aesthetic Alchemist

Style blending system that combines multiple aesthetic approaches:

- 20+ curated aesthetic styles (Gothic Glam, Cyberpunk, Cottagecore, Y2K, etc.)
- Weighted blending of multiple aesthetics
- Strength control for fine-tuning style intensity

### 🤩 Pose Priestess

Pose and positioning control node with separate categories for different content types:

- **General Poses**: Wide variety of artistic and portrait poses
- **Spicy Poses**: Adult/erotic poses for mature content creation
- Arm gesture combinations for enhanced expressiveness
- Weighted blending with strength controls
- Random selection from each category

### 🚫 Negativity Nullifier

Negative prompt management system with smart defaults and customizable exclusions.

### 🪪 Character System (NEW in 1.3.x)

Save, re-load, and apply consistent character traits across workflows:

- 💖 Character Creator saves structured character data (auto-versioned JSON)
- 🗃️ Character Cache loads, randomly selects characters with auto-refresh
- Silent schema migration keeps old character files up to date
- All major Violet nodes accept `character` to override style/body/pose/aesthetic fields
- Encoding Enchantress can passthrough merged character-driven prompt segments
- Deterministic when selecting specific characters; optional randomness when exploring

See Quick Start below for a minimal character workflow.

## 🎨 Color Chips UI Enhancement (Updated in 1.4.0)

Revolutionary visual color selection interface that transforms tedious dropdown navigation into an intuitive, visual experience:

- **Visual Color Swatches**: See exactly what "cyan-teal" or "rose-red" looks like with 20×20px color chips
- **18 Color Fields Enhanced**: All hair colors, makeup colors, eye colors, nail colors, and skin tones
- **60+ Colors Per Field**: Complete spectrum coverage with light/dark variants
- **Instant Search**: Type to filter colors by name (search "teal", "red", "dark", etc.)
- **Smart Tooltips**: Hover to see color names and hex values
- **One-Click Selection**: Click any color chip to instantly set the dropdown value
- **Zero Breaking Changes**: Existing workflows continue working perfectly
- **Performance Optimized**: Only loads for Violet Tools nodes with color fields

**Supported Color Fields:**

- **Glamour Goddess**: hair_color, highlight_color, dip_dye_color, eye_color, eyeliner_color, blush_color, eyeshadow_color, lipstick_color, brow_color, fingernail_color, toenail_color
- **Body Bard**: skin_tone, areola_shade, pubic_hair_color, armpit_hair_color

The color chips automatically appear below color dropdown widgets in supported nodes (now with streamlined single JS implementation), providing immediate visual feedback and dramatically faster color selection. No more scrolling through 60+ options to find the perfect shade!

## Supported Aesthetic Styles

The Aesthetic Alchemist includes carefully curated definitions for:

- **Alt Fashion** - Eclectic, bold, and expressive alternative styles
- **Athleisure** - Sporty chic and comfortable athletic wear
- **Cottagecore** - Pastoral, vintage, and nature-inspired aesthetics
- **Cyberpunk** - Futuristic neon and dystopian tech aesthetics
- **Dark Academia** - Scholarly, vintage, and intellectually rich vibes
- **E-girl** - Bold makeup, vibrant colors, and edgy digital culture
- **Fairycore** - Whimsical, magical, and nature-inspired elements
- **Gothic Glam** - Dark luxury with dramatic and mysterious elements
- **Grunge** - Rebellious, distressed, and urban decay aesthetics
- **Nu-Goth** - Modern gothic with urban and alternative influences
- **Y2K** - Nostalgic early 2000s fashion and metallic accents
- And many more...

## Installation

1. Clone this repository into your ComfyUI custom nodes directory:

1. Clone the repository into your ComfyUI custom_nodes directory:

   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/leylahkrell/ComfyUI-Violet-Tools.git
   ```

1. Restart ComfyUI to load the new nodes.
1. The nodes will appear in the "Violet Tools 💅" category in your node menu.

## Usage

## ⚡ Character Workflow Quick Start (1.3.x)

1. Add `💖 Character Creator` downstream of your configured Violet nodes (e.g. Aesthetic Alchemist, Body Bard, Glamour Goddess, Pose Priestess, Quality Queen). Connect Encoding Enchantress's character output and provide a character name. Run once to save.
2. A JSON character file is created (auto-versioned with `violet_tools_version`).
3. Add `🗃️ Character Cache` to a new or existing workflow. Select a saved character from the dropdown (auto-refreshes) or use "random" to explore.
4. Connect `Character Cache`'s `CHARACTER_DATA` output into any Violet nodes that support character overrides (all major style/pose/body/quality/aesthetic nodes, plus Encoding Enchantress).
5. Set each node's `character_apply` (or equivalent toggle) to enable override merging.
6. Generate: character traits merge with your current parameters. Update character fields manually or regenerate partial nodes; rerun Character Creator to update.
7. Old character files load seamlessly—silent migration normalizes them automatically.

Tip: Use multiple Character Creator runs (different character names) to build a reusable cast. Use random character selection in Character Cache for varied inspiration.

## 🎨 Example Workflow

### Quick Start

1. **Download the workflow**: [Violet Tools Basic Workflow](examples/workflows/violet-tools-basic-workflow.png)
2. **Drag and drop** the PNG file directly into ComfyUI to load the complete workflow
3. **Alternative**: Import the [JSON file](examples/workflows/violet-tools-basic-workflow.json) manually

### Encoding Enchantress Mode Comparison

| Mode | Best For | Sample Output |
|------|----------|---------------|
| **Smooth Blend** *(Default)* | Cohesive artistic styles, beginner-friendly | ![Smooth Blend](examples/sample-outputs/smooth-blend-mode-sample.png) |
| **Closeup** | Face-focused portraits, beauty shots | ![Closeup](examples/sample-outputs/closeup-mode-sample.png) |
| **Portrait** | Dynamic portraits, upper body shots | ![Portrait](examples/sample-outputs/portrait-mode-sample.png) |
| **Compete Combine** | Full body art, experimental results | ![Compete Combine](examples/sample-outputs/compete-combine-mode-sample.png) |

Note: All samples generated with identical prompts; only mode changed.

### Basic Workflow

1. Add any or all Violet Tools nodes to your ComfyUI workflow
2. Configure the desired aesthetic, quality, or style parameters
3. Connect the outputs to the 🧬 Encoding Enchantress conditioning node
4. Positive and negative conditioned outputs are generated for sampling

### Aesthetic Blending

The Aesthetic Alchemist allows you to blend multiple aesthetic styles:

- Select two different aesthetic styles
- Adjust strength values (0.0 to 2.0) for each style
- Use "Random" for surprise combinations
- Add custom text for additional prompt control

### Quality Enhancement

Quality Queen provides consistent quality improvements:

- Toggle boilerplate quality tags on/off
- Select from predefined style enhancements
- Add custom quality descriptors

## File Structure

```text
ComfyUI-Violet-Tools/
├── __init__.py                # Node registration and mappings
├── nodes/                     # All node implementations
│   ├── aesthetic_alchemist.py # Style blending and aesthetic control
│   ├── body_bard.py           # Body features and anatomical descriptions
│   ├── character_cache.py     # Character loading and management
│   ├── character_creator.py   # Character saving and preservation
│   ├── encoding_enchantress.py# Advanced text encoding
│   ├── glamour_goddess.py     # Hair and makeup styling
│   ├── negativity_nullifier.py# Negative prompt management
│   ├── pose_priestess.py      # Pose and positioning control
│   ├── quality_queen.py       # Quality enhancement and boilerplate
│   └── scene_seductress.py    # Scene and environment control
└── feature_lists/             # YAML configuration files
    ├── aesthetics.yaml        # Aesthetic style definitions
    ├── body_features.yaml     # Body feature options
    ├── glamour_goddess.yaml   # Hair and makeup options
    ├── negative_defaults.yaml # Default negative prompts
    ├── poses.yaml             # Pose and position options
    ├── qualities.yaml         # Quality tags and styles
    └── scene_seductress.yaml  # Scene and environment options

Character files you create are stored alongside your ComfyUI output directory. They are plain JSON—feel free to version-control curated characters.
```

## Configuration

All aesthetic options, style definitions, and feature lists are stored in YAML files within the `feature_lists/` directory. These can be customized to add new styles, modify existing options, or adjust the available choices for each node.

## Requirements

- ComfyUI
- PyYAML (usually included with ComfyUI)
- Python 3.8+

## Contributing

Contributions are welcome! Feel free to:

- Add new aesthetic styles to the YAML files
- Suggest improvements to existing nodes
- Report bugs or request features
- Submit pull requests with enhancements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[GZees](https://civitai.com/user/GZees)** - Special thanks for creating the exceptional [iLustMix v5.5](https://civitai.com/models/1110783?modelVersionId=1670263) model I used to generate the sample images. GZees' outstanding model produces beautiful, consistent results that perfectly demonstrate the capabilities of Violet Tools. I highly recommend checking out their incredible work and giving their models a try!
- **[klaabu](https://civitai.com/user/klaabu)** - Gratitude for the excellent [Illustrious Realism Slider](https://civitai.com/models/1486904?modelVersionId=1681903) LoRA used in the sample generation. This fantastic tool adds beautiful realism control and enhances the quality of the demonstrations. Their LoRA work is top-notch and worth exploring!
- Built for the ComfyUI community

---

*Part of the Violet Tools ecosystem for enhanced AI creativity* 💜
