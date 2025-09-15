# Changelog

All notable changes to ComfyUI Violet Tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.3] - 2025-09-14

### ✨ New Features

- **Token Report System**: Added comprehensive token usage analysis to Encoding Enchantress
  - Optional `token_report` boolean input to enable detailed token counting
  - New `tokens` STRING output with formatted per-node token breakdown
  - Shows token usage per 77-token chunk for each Violet Tools prompt node
  - SDXL support: Merges 'g' and 'l' streams using max-per-chunk strategy
  - Handles multi-chunk prompts with clear chunk indexing (chunk 0, chunk 1, etc.)
  - Skips empty prompts to keep reports clean and focused
  - Proper error handling with fallback messages for CLIP connection issues

### 🎯 Technical Details

- Tokenization analysis without redundant encoding for performance
- Node-specific labeling with emoji icons for easy identification
- Graceful handling of weighted syntax and emphasis in prompts
- Memory-efficient implementation with single-pass tokenization

## [1.3.2] - 2025-09-14

### 🏗️ Organizational

- **Node Structure**: Moved all nodes to `nodes/` directory for better organization
- **Category Organization**: Split nodes into logical UI categories:
  - `Violet Tools 💅/Prompt`: Quality Queen, Scene Seductress, Glamour Goddess, Body Bard, Aesthetic Alchemist, Pose Priestess, Negativity Nullifier
  - `Violet Tools 💅/Character`: Character Creator, Character Cache, Encoding Enchantress
- **File Naming**: Renamed persona files to match class names:
  - `persona_preserver.py` → `character_creator.py`
  - `persona_patcher.py` → `character_cache.py`

### 🎯 Improved

- **Node Names**: Refined naming for better semantic clarity:
  - "Persona Preserver" → "💖 Character Creator"
  - "Persona Patcher" → "🗃️ Character Cache"
- **Auto-Refresh**: Character Cache now automatically refreshes without manual toggle
- **Parameter Consistency**: Standardized all nodes to use `character` parameter name

### 📝 Documentation

- Updated README.md with new file structure and terminology
- Revised Quick Start guide to reflect Character Creator/Cache workflow
- Updated file structure documentation

## [1.3.1] - 2025-09-14

### 🎯 Improved

- **Persona System UX**: Streamlined persona workflow with single character input/output
- **Character Profiles**: Removed truncation limits for full character data visibility
- **Simplified Workflow**: Persona Preserver now connects directly to Encoding Enchantress character output
- **Better Naming**: Renamed inputs/outputs for clarity (character_data → character, character_name → name)

### 🔧 Fixed

- **UTF-8 Encoding**: Added proper encoding declarations for Windows compatibility
- **Directory Paths**: Characters now save to ComfyUI's output directory for easy access
- **Node Registration**: Resolved encoding issues preventing persona nodes from loading

### 📝 Technical

- Updated version references across all components
- Improved error handling and status messages
- Enhanced character profile display in Persona Patcher

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
