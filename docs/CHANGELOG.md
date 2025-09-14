# Changelog

All notable changes to ComfyUI Violet Tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-09-14

### Added

- **Persona Patcher Enhancements**: Dynamic dropdown of saved characters with `random` selection and manual `refresh` toggle.
- **Silent Schema Migration**: Older character JSONs auto-normalize to current schema (1.3.x) and are transparently rewritten.
- **Character Data Passthrough**: `Encoding Enchantress` can generate prompts directly from `CHARACTER_DATA` when intermediate nodes are omitted.

### Changed

- **Persona Preserver**: Refactored to save-only node (loading fully delegated to Persona Patcher) and version bumped to `violet_tools_version: 1.3.0`.
- **Uniform Overrides**: All Violet Tools nodes now support `character_data` + `character_apply` pattern.

### Technical

- Automatic file rewrite after migration ensures consistent on-disk structure.
- Stable schema: `data.{quality, scene, glamour, body, aesthetic, pose, negative}`.

### Notes

- Silent migration keeps workflows uninterrupted; no warnings emitted.

### Upgrade Guidance

- Just update files; first load of each persona normalizes it.

## [1.1.0] - 2025-09-06

### Added (Color System Expansion)

- **Field-Specific Color Lists**: Complete color options for each makeup/hair field with natural language phrases
- **Comprehensive Color Coverage**: 75+ color options per field from neutrals to full spectrum
- **Natural Language Colors**: Each color includes the field type (e.g., "black hair", "red lipstick", "hazel eyes")
- **Enhanced Field Structure**: Split fields for better control (eyeliner_style + eyeliner_color, etc.)

### Enhanced (Field Coverage)

- **9 Color Fields**: hair_color, highlight_color, dip_dye_color, eye_color, eyeliner_color, blush_color, eyeshadow_color, lipstick_color, brow_color
- **Glamour Goddess Node**: Field-specific color dropdown system with curated options
- **Field Organization**: Better separation between style and color properties
- **Specialized Colors**: Field-specific options like "hazel eyes" available only where appropriate

### Changed (Field Renames)

- **tips_color** → **dip_dye_color** (eliminates confusion with fingernail tips)
- **eyeliner** → **eyeliner_style** + **eyeliner_color** (separate style and color control)
- **blush** → **blush_weight** + **blush_color** (separate intensity and color control)
- **lipstick** → **lipstick_type** + **lipstick_color** (separate finish and color control)
- **brows** → **brows** + **brow_color** (added separate color control)

### Technical Details (Color Engine)

- Angular distance calculation for closest hue detection
- Configurable thresholds for lightness modifiers
- Robust error handling for invalid color inputs
- Natural language output optimized for AI image generation

## [1.0.0] - 2025-09-05

### Added (Initial Release)

- Initial release of ComfyUI Violet Tools
- **Encoding Enchantress**: Advanced text encoding and prompt processing
- **Quality Queen**: Quality prompts with boilerplate tags and style options
- **Body Bard**: Body feature and pose description generation
- **Glamour Goddess**: Hair and makeup styling with modular options
- **Aesthetic Alchemist**: Style blending system with 20+ curated aesthetics
- **Pose Priestess**: Pose and positioning control for character work
- **Negativity Nullifier**: Negative prompt management with smart defaults
- Comprehensive YAML configuration system for all aesthetic options
- MIT License for open source distribution
- Full documentation and examples

### Features (Initial Release)

- 20+ carefully curated aesthetic styles including Gothic Glam, Cyberpunk, Cottagecore, Y2K, and more
- Weighted blending system for combining multiple aesthetics
- Randomization options for creative exploration
- Modular YAML-based configuration for easy customization
- Professional prompt formatting with automatic weighting syntax
- Category organization in ComfyUI under "Violet Tools 💅"

### Supported Aesthetics (Initial Release)

- Alt Fashion, Athleisure, Bimbo, Cottagecore, Cyberpunk
- Dark Academia, Dreamcore, E-girl, Edgy Streetwear, Fairycore
- Gothic Glam, Grunge, Innocent, Mesh & Fishnets, Nu-Goth
- Post-Apocalyptic, Retro Futurism, Rockabilly, Slutty, Stripper, Y2K

### Technical Details (Initial Release)

- Python 3.8+ compatibility
- PyYAML dependency for configuration management
- ComfyUI custom node architecture
- Modular design for easy extension and customization
