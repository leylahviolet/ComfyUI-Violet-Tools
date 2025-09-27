/**
 * Violet Tools Color Chips (Lean)
 * Purpose: Inline color visualization inside combo dropdown lists + node foreground chip.
 * Removed: legacy popup chip grid, emoji experiments, heavy debug DOM inspectors, unused sanitation.
 */

(function () {
    'use strict';

    // Minimal configuration (only what the remaining features need)
    const CONFIG = {
        enabled: true,
        popupEnhancement: true, // keep inline chip in option popup
        debugLogging: false
    };

    // Derive base path for this extension's served assets similar to vt-node-styling
    function deriveBasePath() {
        if (window.VioletToolsBasePath) return window.VioletToolsBasePath; // manual override
        try {
            const scripts = Array.from(document.getElementsByTagName('script'));
            let hit = scripts.find(s => /vt-colorchips\.js/i.test(s.src)) || scripts.find(s => /vt-node-styling\.js/i.test(s.src));
            if (hit && hit.src) {
                const m = hit.src.match(/\/extensions\/[^/]+\//i);
                if (m) return m[0].endsWith('/') ? m[0] : m[0] + '/';
            }
        } catch (e) { }
        return '/extensions/comfyui-violet-tools/';
    }
    const BASE_PATH = deriveBasePath();

    // Color palette data (populated from palette.json)
    let colorPalette = null;

    // Lean CSS: only inline popup chips (node foreground chip is canvas-drawn)
    const chipStyles = `
        .vt-inline-color-chip { display:inline-block; width:12px; height:12px; border:1px solid #444; border-radius:2px; margin-right:6px; box-sizing:border-box; vertical-align:middle; }
        .vt-inline-color-row { display:flex; align-items:center; gap:6px; }
    `;

    // Inject CSS styles
    function injectStyles() {
        const styleId = 'vt-color-chips-styles';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = chipStyles;
        document.head.appendChild(style);
    }

    // Load color palette data
    async function loadColorPalette() {
        try {
            // Simplified palette loading - try the most likely path first
            const baseRaw = BASE_PATH.replace(/\/$/, '');
            const folder = baseRaw.split('/').pop();
            const root = baseRaw.slice(0, baseRaw.length - folder.length);
            const variants = [folder, folder.toLowerCase(), folder.toUpperCase()];
            const tried = [];
            for (const v of Array.from(new Set(variants))) {
                const url = `${root}${v}/palette.json`;
                tried.push(url);
                try {
                    const response = await fetch(url, { cache: 'no-cache' });
                    if (response.ok) {
                        colorPalette = await response.json();
                        if (CONFIG.debugLogging) console.log('Violet Tools: Palette loaded at', url);
                        buildFlatColorMap();
                        return;
                    }
                } catch (inner) {
                    if (CONFIG.debugLogging) console.log('Violet Tools: Palette fetch failed at', url, inner);
                }
            }
            if (CONFIG.debugLogging) console.warn('Violet Tools: All palette paths failed', tried);
        } catch (error) {
            console.warn('Violet Tools: Failed to load color palette:', error);
        }

        // Fallback palette if loading fails
        colorPalette = {
            colorFields: {
                "base_color": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"],
                "color": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"],
                "accent_color": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
            }
        };
        console.log('Violet Tools: Using fallback color palette');
        buildFlatColorMap();
    }

    // Flat name->hex map for quick lookup across all fields (some color sets use objects vs arrays)
    let flatColorMap = {};
    function buildFlatColorMap() {
        flatColorMap = {};
        if (!colorPalette || !colorPalette.colorFields) return;
        for (const [field, collection] of Object.entries(colorPalette.colorFields)) {
            if (Array.isArray(collection)) {
                // if array, we can't infer names; skip (palette likely incomplete)
                continue;
            }
            for (const [name, hex] of Object.entries(collection)) {
                if (typeof hex === 'string') flatColorMap[name] = hex;
            }
        }
        if (CONFIG.debugLogging) {
            console.log(`[VT] Built flat color map with ${Object.keys(flatColorMap).length} entries`);
        }
    }

    // Check if a widget should have a foreground chip (idempotent – no tracking needed)
    function shouldEnhanceWidget(widget, node) {
        if (!widget || !node || !colorPalette) return false;
        if (widget.type !== 'combo') return false;
        const nodeType = node.type;
    if (!nodeType || !nodeType.match(/^(GlamourGoddess|BodyBard|AestheticAlchemist|QualityQueen|SceneSeductress|PosePriestess|EncodingEnchantress|NegativityNullifier)$/)) return false;
        return widget.name && Object.keys(colorPalette.colorFields).includes(widget.name);
    }

    // Removed legacy popup chip grid + tooltips + search (not used in current UX)

    // Enhance widget by caching color map for foreground painter
    function enhanceWidget(widget, node) {
        if (!shouldEnhanceWidget(widget, node)) return false;

        const fieldName = widget.name;
        const colors = colorPalette.colorFields[fieldName];
        if (!colors) return false;
        widget._colorChips = colors; // used by onDrawForeground
        return true;
    }
    // Removed deprecated emoji chip generator

    // Enhanced node processing
    function enhanceNode(node) {
        if (!node || !node.widgets) return;

        node.widgets.forEach(widget => enhanceWidget(widget, node));

        // Install single foreground drawer (after widgets so chips overlay & visible)
        if (!node._vtColorChipsDrawInstalled) {
            const originalFG = node.onDrawForeground;
            node.onDrawForeground = function (ctx) {
                if (originalFG) originalFG.call(this, ctx);
                try {
                    if (!this.widgets) return;
                    const titleH = (window.LiteGraph && LiteGraph.NODE_TITLE_HEIGHT) || 30;
                    const spacing = 4;
                    let y = (this.widgets_start_y !== undefined ? this.widgets_start_y : (titleH + spacing));
                    for (let i = 0; i < this.widgets.length; i++) {
                        const w = this.widgets[i];
                        let h;
                        try {
                            if (w.computeSize) {
                                const sz = w.computeSize(this.size[0]);
                                h = Array.isArray(sz) ? sz[1] : sz;
                            }
                        } catch { }
                        if (!h || h < 10) h = (window.LiteGraph && LiteGraph.NODE_WIDGET_HEIGHT) || 20;
                        if (w._colorChips && w.value && w._colorChips[w.value]) {
                            const color = w._colorChips[w.value];
                            const chipSize = Math.min(h - 4, 16);
                            const arrowReserve = 14; // approximate triangle area
                            // Base position (right-aligned inside widget row)
                            let chipX = this.size[0] - arrowReserve - chipSize;
                            let chipY = y + (h - chipSize) / 2;
                            // Apply requested stylistic offsets: move right by 75% width, up by 50% height
                            chipX += chipSize * 0.6;
                            chipY -= chipSize * 0.5;
                            // Prevent drawing too far beyond node (allow slight overflow for style)
                            const maxRight = this.size[0] - 2;
                            if (chipX + chipSize > maxRight) chipX = maxRight - chipSize;
                            if (chipY < y - chipSize * 0.6) chipY = y - chipSize * 0.6; // soft clamp
                            ctx.fillStyle = color;
                            ctx.fillRect(chipX, chipY, chipSize, chipSize);
                            ctx.strokeStyle = '#666';
                            ctx.lineWidth = 1;
                            ctx.strokeRect(chipX, chipY, chipSize, chipSize);
                        }
                        y += h + spacing;
                    }
                } catch (e) { /* swallow */ }
            };
            node._vtColorChipsDrawInstalled = true;
            node.setDirtyCanvas(true, true);
        }
    }

    // Decorate option popup entries with inline color chips
    function decoratePopupIfColorList(rootNode) {
        if (!CONFIG.popupEnhancement) return;
        if (!flatColorMap || Object.keys(flatColorMap).length === 0) return;
        // Only proceed if this rootNode looks like a LiteGraph combo list (has an input filter OR many short text children)
        if (!rootNode.querySelector || rootNode._vtPopupScanned) return;
        const hasFilter = rootNode.querySelector('input');
        if (!hasFilter && (!rootNode.className || !/litegraph|graph|combo|popup/i.test(rootNode.className))) return;
        rootNode._vtPopupScanned = true;
        // Collect potential option nodes: leaf div/span elements with text only
        const potential = Array.from(rootNode.querySelectorAll('div, span, li')).filter(el => !el.firstElementChild && (el.textContent || '').trim().length > 0 && (el.textContent || '').length < 40);
        potential.forEach(el => {
            if (el._vtColorized) return; // already processed
            // Match text content to a known color name (exact match ignoring case)
            const rawText = (el.textContent || '').trim();
            const key = Object.keys(flatColorMap).find(k => k.toLowerCase() === rawText.toLowerCase());
            if (!key) return;
            const hex = flatColorMap[key];
            if (!hex) return;
            // Skip if we already have a chip inside
            if (el.querySelector('.vt-inline-color-chip')) {
                el._vtColorized = true;
                return;
            }
            // Wrap content
            const chip = document.createElement('span');
            chip.className = 'vt-inline-color-chip';
            chip.style.background = hex;
            // Adjust contrast border for very light colors
            try {
                const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
                const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
                chip.style.borderColor = luminance > 200 ? '#666' : '#222';
            } catch { }
            // Create flex container if not already
            const container = document.createElement('span');
            container.className = 'vt-inline-color-row';
            const label = document.createElement('span');
            label.textContent = rawText;
            container.appendChild(chip);
            container.appendChild(label);
            // Clear existing text and insert
            while (el.firstChild) el.removeChild(el.firstChild);
            el.appendChild(container);
            el._vtColorized = true;
        });
    }

    // Observe node creation and optionally popup opening
    function observeNodes() {
        if (observeNodes._installed) return;
        observeNodes._installed = true;
        // Hook node configure to enhance widgets after creation
        if (window.LiteGraph && window.LiteGraph.LGraphNode) {
            const originalConfigure = window.LiteGraph.LGraphNode.prototype.configure;
            window.LiteGraph.LGraphNode.prototype.configure = function (data) {
                const res = originalConfigure.call(this, data);
                setTimeout(() => enhanceNode(this), 50);
                return res;
            };
        }
        // Minimal mutation observer only if popup enhancement active
        if (CONFIG.popupEnhancement) {
            const mo = new MutationObserver(muts => {
                for (const m of muts) {
                    for (const n of m.addedNodes) {
                        if (n.nodeType === 1) decoratePopupIfColorList(n);
                    }
                }
            });
            mo.observe(document.body, { childList: true, subtree: true });
        }
    }

    // Initialize the extension
    async function initialize() {

        // Inject CSS
        injectStyles();

        // Load color palette
        await loadColorPalette();

        if (!colorPalette) {
            console.warn('Violet Tools: Color chips disabled - palette not loaded');
            return;
        }

        // Start observing for nodes
        observeNodes();

    }

    // Start initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // Expose configuration for debugging
    window.VioletToolsColorChips = {
        config: CONFIG,
        palette: () => colorPalette,
        enhance: enhanceNode,
        version: '1.0.0',
        // Test function for debugging color chips
        testChips: function () {
            console.log('=== Violet Tools Color Chips Test ===');

            // Check if palette loaded
            if (!colorPalette) {
                console.log('❌ Color palette not loaded');
                return;
            }

            console.log('✅ Color palette loaded:', Object.keys(colorPalette.colorFields).length, 'color fields');

            // Check for Violet Tools nodes
            if (!window.app || !window.app.graph || !window.app.graph._nodes) {
                console.log('❌ No graph or nodes found');
                return;
            }

            const violetNodes = window.app.graph._nodes.filter(node =>
                node.type && node.type.match(/^(GlamourGoddess|BodyBard|AestheticAlchemist|QualityQueen|SceneSeductress|PosePriestess|EncodingEnchantress|NegativityNullifier)$/)
            );

            console.log(`Found ${violetNodes.length} Violet Tools nodes:`, violetNodes.map(n => n.type));

            if (violetNodes.length === 0) {
                console.log('❌ No Violet Tools nodes found. Add some to test color chips.');
                return;
            }

            // Check widgets on each node
            let totalWidgets = 0, colorWidgets = 0, enhancedApplied = 0;

            violetNodes.forEach((node, index) => {
                console.log(`\n--- Node ${index + 1}: ${node.type} ---`);
                console.log('Node widgets:', node.widgets?.length || 0);

                if (node.widgets) {
                    node.widgets.forEach((widget, widgetIndex) => {
                        totalWidgets++;
                        console.log(`  Widget ${widgetIndex}: ${widget.name} (type: ${widget.type})`);

                        if (widget.type === 'combo' && Object.keys(colorPalette.colorFields).includes(widget.name)) {
                            colorWidgets++;
                            console.log(`    ✅ Color field found: ${widget.name}`);

                            if (shouldEnhanceWidget(widget, node)) {
                                try { if (enhanceWidget(widget, node)) { enhancedApplied++; console.log('    ✅ Enhancement applied'); } }
                                catch (error) { console.log('    ❌ Enhancement failed:', error); }
                            } else { console.log('    ⚠️ Not eligible for enhancement'); }
                        }
                    });
                }
            });

            console.log(`\n=== Summary ===`);
            console.log(`Total widgets: ${totalWidgets}`);
            console.log(`Color field widgets: ${colorWidgets}`);
            console.log(`Enhanced widgets: ${enhancedApplied}`);
            console.log(`Available color fields:`, Object.keys(colorPalette.colorFields));

            if (enhancedApplied > 0) {
                console.log('🎉 Color chips should be visible on enhanced widgets!');
            } else {
                console.log('⚠️ No widgets were enhanced. Check if widgets match color field names.');
            }
        }
    };

    // Expose test function to global window for debugging (after object is defined)
    window.testChips = window.VioletToolsColorChips.testChips;

    // Ensure shared VioletTools namespace + attach debug helpers if not already added by other modules
    window.VioletTools = window.VioletTools || {};
    if (!window.VioletTools.enableDebug) {
        window.VioletTools.enableDebug = function () {
            try {
                if (window.VioletToolsColorChips) {
                    window.VioletToolsColorChips.config.debugLogging = true;
                }
                if (window.VioletToolsNodeStylingV2) {
                    window.VioletToolsNodeStylingV2.config.debugLogging = true;
                }
                console.log('Violet Tools: Debug logging ENABLED');
            } catch (e) { }
        };
    }
    if (!window.VioletTools.disableDebug) {
        window.VioletTools.disableDebug = function () {
            try {
                if (window.VioletToolsColorChips) {
                    window.VioletToolsColorChips.config.debugLogging = false;
                }
                if (window.VioletToolsNodeStylingV2) {
                    window.VioletToolsNodeStylingV2.config.debugLogging = false;
                }
                console.log('Violet Tools: Debug logging DISABLED');
            } catch (e) { }
        };
    }

    // Removed heavy DOM inspection helpers & load banner (lean surface)

})();