/**
 * Violet Tools Color Chips Extension
 * Adds visual color swatches next to color dropdown widgets in ComfyUI
 * For use with Violet Tools nodes that have color selection fields
 */

console.log('🚀 [VT-COLORCHIPS] Script execution started...');

(function() {
    'use strict';

    console.log('🚀 [VT-COLORCHIPS] Inside IIFE...');

    // Configuration
    const CONFIG = {
        chipSize: 20,           // Size of color chip in pixels
        chipsPerRow: 10,        // Number of chips per row
        maxRows: 6,             // Maximum rows to show before scrolling
        enabled: true,          // Master enable/disable
        showTooltips: true,     // Show color name tooltips
        animationDuration: 200  // Animation duration in ms
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
                console.log('Violet Tools: Color palette loaded successfully');
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

        console.log(`[DEBUG] Enhancing widget ${fieldName} with dropdown color chips...`);

        // Store the colors for later use
        widget._colorChips = colors;

        // Override the widget's option display
        const originalOptionsValues = widget.options?.values;
        if (originalOptionsValues) {
            // Create enhanced options with color chips
            widget.options.values = originalOptionsValues.map(optionValue => {
                const hexColor = colors[optionValue];
                if (hexColor) {
                    // Add color chip emoji/unicode block based on color
                    const colorChip = getColorChip(hexColor);
                    return `${colorChip} ${optionValue}`;
                }
                return optionValue; // No color for this option
            });
        }

        // Override the display of the selected value
        const originalDraw = widget.draw;
        widget.draw = function(ctx, node, widget_width, y, H) {
            // Call original widget draw
            if (originalDraw) {
                originalDraw.call(this, ctx, node, widget_width, y, H);
            }
            
            // Draw color chip next to selected value
            const currentColor = colors[this.value];
            if (currentColor) {
                // Draw a small color square next to the value
                const chipSize = 12;
                const chipX = widget_width - chipSize - 25; // Position near the right edge
                const chipY = y + (H - chipSize) / 2; // Center vertically
                
                ctx.fillStyle = currentColor;
                ctx.fillRect(chipX, chipY, chipSize, chipSize);
                
                ctx.strokeStyle = '#666';
                ctx.lineWidth = 1;
                ctx.strokeRect(chipX, chipY, chipSize, chipSize);
            }
        };

        // Mark as enhanced
        enhancedWidgets.add(widget);
        console.log(`[DEBUG] Widget ${fieldName} enhanced with dropdown color chips`);
        
        return true;
    }
    
    // Get a color chip character/emoji based on hex color
    function getColorChip(hexColor) {
        // Convert hex to rough color categories and return appropriate emoji
        const color = hexColor.toLowerCase();
        
        // Simple color mapping - you can make this more sophisticated
        if (color.includes('red') || color.startsWith('#f') || color.startsWith('#e')) return '🟥';
        if (color.includes('orange') || color.startsWith('#ff8') || color.startsWith('#ff6')) return '🟧';
        if (color.includes('yellow') || color.startsWith('#ff') || color.startsWith('#fe')) return '🟨';
        if (color.includes('green') || color.startsWith('#0') || color.startsWith('#1')) return '🟩';
        if (color.includes('blue') || color.startsWith('#00') || color.startsWith('#0')) return '🟦';
        if (color.includes('purple') || color.startsWith('#8') || color.startsWith('#9')) return '🟪';
        if (color.includes('black') || color.startsWith('#000') || color.startsWith('#111')) return '⬛';
        if (color.includes('white') || color.startsWith('#fff') || color.startsWith('#eee')) return '⬜';
        
        // Default to a neutral square
        return '🟫';
    }

    // Enhanced node processing
    function enhanceNode(node) {
        if (!node || !node.widgets) return;
        
        let enhancedCount = 0;
        
        node.widgets.forEach(widget => {
            if (enhanceWidget(widget, node)) {
                enhancedCount++;
            }
        });
        
        if (enhancedCount > 0) {
            console.log(`Violet Tools: Enhanced ${enhancedCount} color widgets in ${node.constructor?.name || 'unknown'} node`);
        }
    }
    
    // Monitor for new nodes
    function observeNodes() {
        // Hook into ComfyUI's node creation
        if (window.LiteGraph && window.LiteGraph.LGraphNode) {
            const originalConfigure = window.LiteGraph.LGraphNode.prototype.configure;
            window.LiteGraph.LGraphNode.prototype.configure = function(data) {
                const result = originalConfigure.call(this, data);
                
                // Small delay to ensure widgets are fully initialized
                setTimeout(() => {
                    enhanceNode(this);
                }, 100);
                
                return result;
            };
        }
        
        // Also monitor DOM changes for widgets
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if this looks like a ComfyUI widget
                        const selects = node.querySelectorAll('select');
                        selects.forEach(select => {
                            // Try to find the associated widget and enhance it
                            // This is a fallback for cases where the node hook doesn't work
                        });
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Initialize the extension
    async function initialize() {
        console.log('Violet Tools: Initializing color chips extension...');
        
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
        
        console.log('Violet Tools: Color chips extension initialized successfully');
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
    
    console.log('🎨 Violet Tools Color Chips extension loaded');

})();