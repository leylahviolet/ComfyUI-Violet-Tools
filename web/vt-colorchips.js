/**
 * Violet Tools Color Chips Extension
 * Adds visual color swatches next to color dropdown widgets in ComfyUI
 * For use with Violet Tools nodes that have color selection fields
 */


(function() {
    'use strict';


    // Configuration
    const CONFIG = {
        chipSize: 20,           // Size of color chip in pixels
        chipsPerRow: 10,        // Number of chips per row
        maxRows: 6,             // Maximum rows to show before scrolling
        enabled: true,          // Master enable/disable
        showTooltips: true,     // Show color name tooltips
        animationDuration: 200, // Animation duration in ms
        popupEnhancement: true, // Re-enabled with stricter filtering
        debugLogging: false     // Silence non-essential logs by default
    };

    // Color palette data - will be populated from palette.json
    let colorPalette = null;
    
    // Track which widgets have been enhanced
    const enhancedWidgets = new WeakSet();
    
    // CSS styles for color chips
    const chipStyles = `
        .vt-color-chips {
            display: flex !important;
            flex-wrap: wrap;
            gap: 3px;
            margin-top: 6px;
            max-height: ${CONFIG.chipSize * CONFIG.maxRows + (CONFIG.maxRows - 1) * 3}px;
            overflow-y: auto;
            padding: 6px;
            background: rgba(0,0,0,0.3) !important;
            border-radius: 6px;
            border: 2px solid #555 !important;
            position: relative !important;
            z-index: 1000 !important;
        }
        
        .vt-color-chip {
            width: ${CONFIG.chipSize}px !important;
            height: ${CONFIG.chipSize}px !important;
            border: 2px solid #666 !important;
            border-radius: 4px;
            cursor: pointer;
            transition: transform ${CONFIG.animationDuration}ms ease, box-shadow ${CONFIG.animationDuration}ms ease;
            box-sizing: border-box;
            position: relative !important;
            z-index: 1001 !important;
        }
        
        .vt-color-chip:hover {
            transform: scale(1.3) !important;
            box-shadow: 0 4px 12px rgba(255,255,255,0.4) !important;
            border-color: #fff !important;
            z-index: 1002 !important;
            position: relative !important;
        }
        
        .vt-color-chip.selected {
            border: 3px solid #fff !important;
            box-shadow: 0 0 0 2px #333 !important;
        }
        
        .vt-chip-tooltip {
            position: absolute;
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            white-space: nowrap;
            transform: translateX(-50%);
            margin-top: 4px;
        }
        
        .vt-chip-search {
            width: 100%;
            padding: 4px 8px;
            margin-bottom: 4px;
            border: 1px solid #333;
            border-radius: 3px;
            background: rgba(0,0,0,0.2);
            color: white;
            font-size: 12px;
        }
        
        .vt-chip-search::placeholder {
            color: #888;
        }

        /* Inline dropdown entry chip */
        .vt-inline-color-chip {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 1px solid #444;
            border-radius: 2px;
            margin-right: 6px;
            box-sizing: border-box;
            vertical-align: middle;
        }
        .vt-inline-color-row {
            display: flex;
            align-items: center;
            gap: 6px;
        }
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
            const response = await fetch('/extensions/comfyui-violet-tools/palette.json');
            if (response.ok) {
                colorPalette = await response.json();
                if (CONFIG.debugLogging) {
                    console.log('Violet Tools: Color palette loaded successfully');
                }
                buildFlatColorMap();
                return;
            }
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

    // Check if a widget should have color chips
    function shouldEnhanceWidget(widget, node) {
        if (!widget || !node || !colorPalette) return false;
        if (enhancedWidgets.has(widget)) return false;
        if (widget.type !== 'combo') return false;
        
        // Check if this is a Violet Tools node using node.type instead of constructor.name
        const nodeType = node.type;
        if (!nodeType || !nodeType.match(/^(GlamourGoddess|BodyBard|AestheticAlchemist|QualityQueen|SceneSeductress|PosePriestess|EncodingEnchantress|NegativityNullifier|CharacterCreator|CharacterCache)$/)) {
            return false;
        }
        
        // Check if widget name matches a color field
        const widgetName = widget.name;
        return widgetName && Object.keys(colorPalette.colorFields).includes(widgetName);
    }

    // Get color options for a specific field
    function getColorsForField(fieldName) {
        if (!colorPalette || !colorPalette.colorFields[fieldName]) return [];
        return colorPalette.colorFields[fieldName];
    }

    // Create color chip element
    function createColorChip(colorName, hexColor, isSelected = false) {
        const chip = document.createElement('div');
        chip.className = 'vt-color-chip' + (isSelected ? ' selected' : '');
        chip.style.backgroundColor = hexColor;
        chip.dataset.colorName = colorName;
        chip.dataset.hexColor = hexColor;
        
        // Add tooltip if enabled
        if (CONFIG.showTooltips) {
            chip.addEventListener('mouseenter', showTooltip);
            chip.addEventListener('mouseleave', hideTooltip);
        }
        
        return chip;
    }

    // Show tooltip
    function showTooltip(event) {
        const chip = event.target;
        const colorName = chip.dataset.colorName;
        const hexColor = chip.dataset.hexColor;
        
        const tooltip = document.createElement('div');
        tooltip.className = 'vt-chip-tooltip';
        tooltip.textContent = `${colorName} (${hexColor})`;
        
        const rect = chip.getBoundingClientRect();
        tooltip.style.left = rect.left + rect.width / 2 + 'px';
        tooltip.style.top = rect.bottom + 'px';
        
        document.body.appendChild(tooltip);
        chip._tooltip = tooltip;
    }

    // Hide tooltip
    function hideTooltip(event) {
        const chip = event.target;
        if (chip._tooltip) {
            chip._tooltip.remove();
            chip._tooltip = null;
        }
    }

    // Create search input
    function createSearchInput(container, chips) {
        const search = document.createElement('input');
        search.className = 'vt-chip-search';
        search.type = 'text';
        search.placeholder = 'Search colors...';
        
        search.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            chips.forEach(chip => {
                const colorName = chip.dataset.colorName.toLowerCase();
                const match = colorName.includes(query);
                chip.style.display = match ? 'block' : 'none';
            });
        });
        
        return search;
    }

    // Update selected chip
    function updateSelectedChip(container, selectedValue) {
        const chips = container.querySelectorAll('.vt-color-chip');
        chips.forEach(chip => {
            chip.classList.toggle('selected', chip.dataset.colorName === selectedValue);
        });
    }

    // Create color chip container
    function createColorChipContainer(widget, fieldName) {
        const colors = getColorsForField(fieldName);
        if (!colors || Object.keys(colors).length === 0) return null;
        
        const container = document.createElement('div');
        container.className = 'vt-color-container';
        
        // Create chips container
        const chipsContainer = document.createElement('div');
        chipsContainer.className = 'vt-color-chips';
        
        // Create chips
        const chips = [];
        for (const [colorName, hexColor] of Object.entries(colors)) {
            const chip = createColorChip(colorName, hexColor);
            chip.addEventListener('click', function() {
                widget.value = colorName;
                if (widget.callback) {
                    widget.callback(colorName);
                }
                updateSelectedChip(container, colorName);
            });
            chipsContainer.appendChild(chip);
            chips.push(chip);
        }
        
        // Create search input
        const searchInput = createSearchInput(container, chips);
        container.appendChild(searchInput);
        container.appendChild(chipsContainer);
        
        // Update initial selection
        updateSelectedChip(container, widget.value);
        
        return container;
    }

    // Enhance a widget with color chips in dropdown options
    function enhanceWidget(widget, node) {
        if (!shouldEnhanceWidget(widget, node)) return false;
        
        const fieldName = widget.name;
        const colors = colorPalette.colorFields[fieldName];
        if (!colors) return false;


        // Store the colors for later use
        widget._colorChips = colors;
        // DO NOT mutate widget.options.values (breaks selection / hides widget)
        // Instead we'll enhance the popup DOM list when it opens via MutationObserver.
        // Placeholder flag so we only attach one popup enhancer per widget.
        widget._vtPopupEnhanced = false;

        // Ensure any previous widget-level override is removed (stability)
        if (widget._vtOriginalDraw) {
            widget.draw = widget._vtOriginalDraw;
            delete widget._vtOriginalDraw;
        }

        
        return true;
    }
    
    // Get a color chip character/emoji based on hex color
    function getColorChip(hexColor) {
        // Convert hex to RGB for better color analysis
        const hex = hexColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        // Simple color mapping based on RGB values
        if (r > 200 && g < 100 && b < 100) return '🟥'; // Red
        if (r > 200 && g > 150 && b < 100) return '🟧'; // Orange
        if (r > 200 && g > 200 && b < 100) return '🟨'; // Yellow
        if (r < 100 && g > 150 && b < 100) return '🟩'; // Green
        if (r < 100 && g < 100 && b > 150) return '🟦'; // Blue
        if (r > 100 && g < 100 && b > 150) return '🟪'; // Purple/Violet
        if (r < 80 && g < 80 && b < 80) return '⬛'; // Black/Dark
        if (r > 200 && g > 200 && b > 200) return '⬜'; // White/Light
        
        // For browns and other colors
        if (r > g && r > b && g > 100) return '🟫'; // Brown
        
        // Default to a neutral square
        return '�';
    }

    // Enhanced node processing
    function enhanceNode(node) {
        if (!node || !node.widgets) return;

        let enhancedCount = 0;

        // Sanitize any legacy emoji-prefixed values (migration safeguard)
        node.widgets.forEach(w => {
            if (w?.options?.values && Array.isArray(w.options.values)) {
                const cleaned = w.options.values.map(v => typeof v === 'string' ? v.replace(/^[\u{1F7E5}-\u{1F7EB}⬛⬜🟫🔳]\s*/u, '').trim() : v);
                if (cleaned.some((c,i)=>c!==w.options.values[i])) {
                    w.options.values = cleaned;
                    if (CONFIG.debugLogging) {
                        console.log('[VT] Sanitized legacy emoji values for widget', w.name);
                    }
                }
            }
        });

        node.widgets.forEach(widget => { if (enhanceWidget(widget, node)) enhancedCount++; });

        if (enhancedCount > 0) {
            if (CONFIG.debugLogging) {
                console.log(`Violet Tools: Enhanced ${enhancedCount} color widgets in ${node.constructor?.name || 'unknown'} node`);
            }
        }
        
        // Install single foreground drawer (after widgets so chips overlay & visible)
        if (!node._vtColorChipsDrawInstalled) {
            const originalFG = node.onDrawForeground;
            node.onDrawForeground = function(ctx) {
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
                        } catch {}
                        if (!h || h < 10) h = (window.LiteGraph && LiteGraph.NODE_WIDGET_HEIGHT) || 20;
                        if (w._colorChips && w.value && w._colorChips[w.value]) {
                            const color = w._colorChips[w.value];
                            const chipSize = Math.min(h - 6, 14);
                            const arrowReserve = 14; // approximate triangle area
                            // Base position (right-aligned inside widget row)
                            let chipX = this.size[0] - arrowReserve - chipSize;
                            let chipY = y + (h - chipSize) / 2;
                            // Apply requested stylistic offsets: move right by 80% width, up by 50% height
                            chipX += chipSize * 0.8;
                            chipY -= chipSize * 0.5;
                            // Prevent drawing too far beyond node (allow slight overflow for style)
                            const maxRight = this.size[0] - 2;
                            if (chipX + chipSize > maxRight) chipX = maxRight - chipSize;
                            if (chipY < y - chipSize * 0.6) chipY = y - chipSize * 0.6; // soft clamp
                            ctx.fillStyle = color;
                            ctx.fillRect(chipX, chipY, chipSize, chipSize);
                            ctx.strokeStyle = '#222';
                            ctx.lineWidth = 1;
                            ctx.strokeRect(chipX, chipY, chipSize, chipSize);
                        }
                        y += h + spacing;
                    }
                } catch(e) { /* swallow */ }
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
        const potential = Array.from(rootNode.querySelectorAll('div, span, li')).filter(el => !el.firstElementChild && (el.textContent||'').trim().length > 0 && (el.textContent||'').length < 40);
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
                const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
                const luminance = 0.299*r + 0.587*g + 0.114*b;
                chip.style.borderColor = luminance > 200 ? '#666' : '#222';
            } catch {}
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
            window.LiteGraph.LGraphNode.prototype.configure = function(data) {
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
        testChips: function() {
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
                node.type && node.type.match(/^(GlamourGoddess|BodyBard|AestheticAlchemist|QualityQueen|SceneSeductress|PosePriestess|EncodingEnchantress|NegativityNullifier|CharacterCreator|CharacterCache)$/)
            );
            
            console.log(`Found ${violetNodes.length} Violet Tools nodes:`, violetNodes.map(n => n.type));
            
            if (violetNodes.length === 0) {
                console.log('❌ No Violet Tools nodes found. Add some to test color chips.');
                return;
            }
            
            // Check widgets on each node
            let totalWidgets = 0;
            let colorWidgets = 0;
            let enhancedWidgets = 0;
            
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
                                console.log(`    ✅ Should enhance this widget`);
                                
                                // Try to enhance it
                                try {
                                    enhanceWidget(widget, node);
                                    enhancedWidgets++;
                                    console.log(`    ✅ Enhancement applied`);
                                } catch (error) {
                                    console.log(`    ❌ Enhancement failed:`, error);
                                }
                            } else {
                                console.log(`    ⚠️ Widget not marked for enhancement`);
                            }
                        }
                    });
                }
            });
            
            console.log(`\n=== Summary ===`);
            console.log(`Total widgets: ${totalWidgets}`);
            console.log(`Color field widgets: ${colorWidgets}`);
            console.log(`Enhanced widgets: ${enhancedWidgets}`);
            console.log(`Available color fields:`, Object.keys(colorPalette.colorFields));
            
            if (enhancedWidgets > 0) {
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
        window.VioletTools.enableDebug = function() {
            try {
                if (window.VioletToolsColorChips) {
                    window.VioletToolsColorChips.config.debugLogging = true;
                }
                if (window.VioletToolsNodeStylingV2) {
                    window.VioletToolsNodeStylingV2.config.debugLogging = true;
                }
                console.log('Violet Tools: Debug logging ENABLED');
            } catch(e) {}
        };
    }
    if (!window.VioletTools.disableDebug) {
        window.VioletTools.disableDebug = function() {
            try {
                if (window.VioletToolsColorChips) {
                    window.VioletToolsColorChips.config.debugLogging = false;
                }
                if (window.VioletToolsNodeStylingV2) {
                    window.VioletToolsNodeStylingV2.config.debugLogging = false;
                }
                console.log('Violet Tools: Debug logging DISABLED');
            } catch(e) {}
        };
    }
    
    // Simple check function to verify extension is loaded
    window.vtColorChipsLoaded = function() {
        console.log('✅ Violet Tools Color Chips extension is loaded and ready!');
        console.log('Available functions: testChips()');
        return true;
    };
    
    // Debug function to inspect DOM structure
    window.vtInspectDOM = function() {
        console.log('=== DOM Structure Inspection ===');
        
        // Look for any elements that might be nodes
        const allElements = document.querySelectorAll('*');
        const potentialNodes = [];
        
        console.log(`Total DOM elements: ${allElements.length}`);
        
        // Look for elements with various node-related classes/attributes
        const nodeSelectors = [
            '.comfy-node',
            '.litegraph-node', 
            '[data-node-id]',
            '[id*="node"]',
            '.node',
            '[class*="node"]',
            '[class*="litegraph"]',
            '[class*="comfy"]'
        ];
        
        nodeSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                console.log(`Found ${elements.length} elements with selector: ${selector}`);
                elements.forEach((el, i) => {
                    if (i < 3) { // Show first 3 examples
                        console.log(`  Element ${i+1}:`, el);
                        console.log(`    - Classes: ${el.className}`);
                        console.log(`    - ID: ${el.id}`);
                        console.log(`    - Data attributes:`, Object.keys(el.dataset));
                    }
                });
            }
        });
        
        // Look specifically for select elements
        const selects = document.querySelectorAll('select');
        console.log(`\nFound ${selects.length} select elements:`);
        selects.forEach((sel, i) => {
            if (i < 5) { // Show first 5
                console.log(`  Select ${i+1}:`, sel);
                console.log(`    - Parent classes: ${sel.parentElement ? sel.parentElement.className : 'none'}`);
                console.log(`    - Options count: ${sel.options.length}`);
                if (sel.options.length > 0) {
                    console.log(`    - First few options:`, Array.from(sel.options).slice(0, 3).map(opt => opt.value));
                }
            }
        });
        
        return { totalElements: allElements.length, selects: selects.length };
    };
    
    // Debug function to check if chips are in the DOM
    window.vtCheckChipsInDOM = function() {
        const chipContainers = document.querySelectorAll('.vt-color-chips');
        const chipElements = document.querySelectorAll('.vt-color-chip');
        console.log('=== DOM Chip Check ===');
        console.log(`Found ${chipContainers.length} chip containers in DOM`);
        console.log(`Found ${chipElements.length} individual chips in DOM`);
        
        chipContainers.forEach((container, i) => {
            console.log(`Container ${i+1}:`, container);
            console.log(`  - Visible: ${container.offsetWidth > 0 && container.offsetHeight > 0}`);
            console.log(`  - Style: ${container.style.cssText || 'none'}`);
            console.log(`  - Computed style display: ${getComputedStyle(container).display}`);
        });
        
        return { containers: chipContainers.length, chips: chipElements.length };
    };
    
    // Silenced debug banner after stabilization

})();