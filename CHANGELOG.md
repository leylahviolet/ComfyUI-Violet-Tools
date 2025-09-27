# Changelog

## [Unreleased]

No unreleased changes.

## [2.1.0] - 2025-09-26

### 🔮 Oracle's Override (Refined)

- Simplified to a single output: `override`.
- New `chain` input lets you prepend text to the manual override; both `chain` and `override` are joined with ", " and support wildcards using `{a|b|c}` syntax (resolved repeatedly until stable).
- Output is `null` unless `override_prompts` is true. When true, the combined string is emitted and used as the full positive prompt.
- VT styling applied to the node for consistent visuals.

### 🧬 Encoding Enchantress Integration

- Accepts a single optional `override` input. If the value is not null (empty string allowed), it is used as the entire positive prompt, skipping mode grouping. If null, normal prompt assembly proceeds.
- Token report includes the override section when used.

### � Prompt Optimization (Essence Algorithm)

- New optional `optimize_prompt` toggle in 🧬 Encoding Enchantress compresses redundant tags and canonicalizes aliases to reduce total token count — improving effective attention on what matters.
- Purely algorithmic (no LLM). Uses curated allowlists, alias maps, and feature metadata bundled under `node_resources/`.
- Safe heuristics: preserves unknowns, applies conservative fuzzy matching with a retention guard, and adds back originals if a reduction would over-trim.
- Scope: optimizes positive segments only (quality, scene, glamour, body, aesthetic, pose). Negatives are left unchanged. Disabled automatically when 🔮 Oracle's Override is used.
- Reporting: when `token_report` is enabled, a "🪙 Token Savings" section is appended showing per-segment and total before→after token counts.

### �🧹 Cleanup (Legacy Removal)

- Fully removed legacy character nodes from the repository: `Character Creator` and `Character Cache`.
- Backend character module is wireless-only now: removed prompt-time UI sync code; kept REST endpoints for Curator (GET/POST/DELETE `/violet/character`).

## [2.0.0] - 2025-09-26

### ✨ Wireless Character Flow

- Merged Character Creator + Character Cache into a single, wireless-only 💖 Character Curator node.
- Removed all character wiring and apply toggles from prompt nodes; Curator handles save/load via UI only.
- Frontend buttons on Curator: Load Character to All, Save Character, Delete Character.
- Backend endpoints: GET/POST/DELETE /violet/character. GET now supports list mode via `?list=1` and also returns a name list when no `name` is provided.

### 💄 UX — Autocomplete/Browse Names

- Added a Browse Names overlay for the Curator’s `save_character` field:
  - Click “Browse Names” to open a searchable overlay of saved character names.
  - Type to filter and click to select a name to prefill for safe overwrite.
  - Fully wireless — no canvas wiring required.

### 🧰 Internals

- Web: `vt-node-styling.js` injects Curator buttons and overlay UI.
- Server: `lib/character_sync.py` adds name listing (`_list_character_names`) and bumps saved payload `violet_tools_version` to `2.0.0`.
- Kept all existing string type identifiers and return orders stable for compatibility.

## [1.5.0] - 2025-09-26

### ✨ Improvements (1.5.0)

- Unified output bundling from all prompt nodes: each node now emits a single value that includes both the rendered text and its structured selections (dropdown choices, fem/masc toggles, strengths, extra). This keeps the UI clean—no extra ports—while enabling robust character persistence.
- Encoding Enchantress now transparently unwraps bundled inputs and merges structured fields into the character JSON next to the existing "text" entry for each domain.
- Added wildcard parsing to every node’s "extra" field with label hint "extra, wildcards". Supports {a|b|c} syntax and resolves once per run.

### 🐛 Fixes (1.5.0)

- Resolved warning in Aesthetic Alchemist when inputs were set to None by updating `IS_CHANGED(**_kwargs)` to accept keyword args.

### 🔧 Internal (1.5.0)

- Kept all public names, return orders, and categories stable to avoid breaking saved workflows. The bundling is an additive internal contract; plain strings still work for backward compatibility.

All notable changes to ComfyUI Violet Tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2025-09-15

### 💄 Style

- **Color Chips Lean Refactor**: Trimmed `vt-colorchips.js` by removing deprecated emoji rendering, legacy popup chip grid, search + tooltip UI, unused sanitation pass, DOM inspection helpers, and redundant enhancement tracking.
- **Node Styling Scope Refined**: Reverted experimental widget row + multiline background skinning. Retained only core node branding (background color + Encoding Enchantress logo). Prevents draw stack interference and keeps ComfyUI widget visuals standard.

### 🔧 Internal (Chips)

- Simplified config surface (only `enabled`, `popupEnhancement`, `debugLogging`).
- Maintained inline dropdown color chip decoration and canvas foreground chip rendering (no workflow impact).
- Reduced script size (−430+ LOC) for faster parse and lower maintenance overhead.

### ✨ Improvements

- **Color Chips Refinement**: Consolidated to a single production `vt-colorchips.js` file; removed legacy `-debug` and `-simple` variants.
- **Visual Alignment**: Added precise offset layout for inline color chips in node widgets; improved dropdown chip prefixes.
- **Logo Positioning**: Encoding Enchantress logo top-aligned and sizing stabilized.
- **Output Reorder**: `Encoding Enchantress` outputs now ordered as `positive, negative, tokens, character, pos, neg` with `pos_text/neg_text` renamed externally to `pos/neg`.
- **Skin Tone Palette Update**: Adjusted olive, golden, amber, mahogany, cocoa, ebony, dark ebony hex values; removed obsolete `light ebony` shade.

### 🧹 Cleanup

- Removed verbose console debugging from color chip extension.
- Deleted unused `vt-colorchips-debug.js` and `vt-colorchips-simple.js`.

### 🔧 Internal

- Minor refactors for maintainability; no breaking API changes.

## [1.3.5] - 2025-09-14

### 🔧 Fixed

- **Critical Path Issue**: Fixed YAML file path resolution for nodes moved to `nodes/` directory
  - Corrected `feature_lists` path resolution in all node files
  - Added proper parent directory navigation (`os.path.dirname` called twice)
  - Resolves `FileNotFoundError` on ComfyUI startup that prevented extension loading
  - Affects all nodes: Quality Queen, Glamour Goddess, Body Bard, Aesthetic Alchemist, Pose Priestess, Scene Seductress, Negativity Nullifier, Encoding Enchantress

### 📋 Notes

- This is a critical hotfix for v1.3.4 that ensures proper loading of YAML configuration files
- All color chips functionality from v1.3.4 remains intact and functional

## [1.3.4] - 2025-09-14

### 🎨 New Features

- **Color Chips UI Enhancement**: Revolutionary visual color selection interface
  - Visual color swatches (20×20px) replace tedious dropdown navigation
  - 18 color fields enhanced across Glamour Goddess and Body Bard nodes
  - 60+ colors per field with complete spectrum coverage and light/dark variants
  - Instant search functionality - type to filter colors by name
  - Smart tooltips showing color names and precise hex values
  - One-click selection instantly updates dropdown values
  - Zero breaking changes - existing workflows continue working perfectly

### 🎯 Enhanced Nodes

- **Glamour Goddess** (11 color fields): hair_color, highlight_color, dip_dye_color, eye_color, eyeliner_color, blush_color, eyeshadow_color, lipstick_color, brow_color, fingernail_color, toenail_color
- **Body Bard** (4 color fields): skin_tone, areola_shade, pubic_hair_color, armpit_hair_color

### 🔧 Technical Implementation

- **Web Extension System**: Added `WEB_DIRECTORY` export for JavaScript extension loading
- **Color Palette Data**: Comprehensive `palette.json` with 1000+ color-to-hex mappings
- **Smart Color Mapping**: Intelligent hex value assignments (e.g., "light red" = `#FF6666`, "dark red" = `#CC0000`)
- **Performance Optimized**: Only loads for Violet Tools nodes with color fields
- **Browser Integration**: Seamless ComfyUI widget system integration with hover animations

### 🎨 User Experience

- **Visual Feedback**: See exactly what "cyan-teal" or "rose-red" looks like before selection
- **Faster Workflow**: No more scrolling through 60+ dropdown options
- **Color Coordination**: Easily match hair highlights to eye colors visually
- **Search & Filter**: Find colors quickly with partial name matching
- **Responsive Design**: Adapts to different screen sizes and node layouts

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

### 🎯 Improved (Persona System)

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

### 🔧 Fixed (Persona System)

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
