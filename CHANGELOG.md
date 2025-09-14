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
- **Uniform Overrides**: All Violet Tools nodes now support `character_data` + `character_apply` pattern for persona-driven population without overwriting explicit user inputs.

### Technical

- Automatic file rewrite after migration ensures consistent on-disk structure (adds missing sections, renames `nullifier` → `negative`).
- Stable schema shape maintained: `data.{quality, scene, glamour, body, aesthetic, pose, negative}`.

### Notes

- Migration is silent by design (no warnings, no failures) to keep workflows uninterrupted.
- Future minor versions can introduce schema_version stamping if needed; current approach leverages `violet_tools_version`.

### Upgrade Guidance

- Update the extension directory; first load of each existing persona will normalize it automatically.
- No manual intervention required.

## [1.1.0] - 2025-09-06

### Added (Pose System Revamp)

- **Pose Priestess**: Restructured to support separate general and spicy pose categories
- New spicy pose collection with 20+ adult/erotic poses using gender-neutral language
- Renamed pose fields: `pose_1` → `general_pose`, `pose_2` → `spicy_pose`
- Enhanced pose variety with comprehensive coverage of poses and arm gestures

### Changed (Pose Data Structure)

- Updated poses.yaml structure to nest poses under `general_poses` and `spicy_poses` objects
- Improved pose descriptions and removed redundant entries
- Updated documentation to reflect new pose categorization

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
