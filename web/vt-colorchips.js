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
        animationDuration: 200  // Animation duration in ms
    };

    // Color palette data - will be populated from palette.json
    let colorPalette = null;
    
    // Track which widgets have been enhanced
    const enhancedWidgets = new WeakSet();
    
    // CSS styles for color chips
    const chipStyles = `
        .vt-color-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 2px;
            margin-top: 4px;
            max-height: ${CONFIG.chipSize * CONFIG.maxRows + (CONFIG.maxRows - 1) * 2}px;
            overflow-y: auto;
            padding: 2px;
            background: rgba(0,0,0,0.1);
            border-radius: 4px;
        }
        
        .vt-color-chip {
            width: ${CONFIG.chipSize}px;
            height: ${CONFIG.chipSize}px;
            border: 1px solid #333;
            border-radius: 3px;
            cursor: pointer;
            transition: transform ${CONFIG.animationDuration}ms ease, box-shadow ${CONFIG.animationDuration}ms ease;
            box-sizing: border-box;
        }
        
        .vt-color-chip:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            border-color: #fff;
            z-index: 10;
            position: relative;
        }
        
        .vt-color-chip.selected {
            border: 2px solid #fff;
            box-shadow: 0 0 0 1px #333;
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
            // Use the correct lowercase extension path that ComfyUI serves
            const response = await fetch('/extensions/comfyui-violet-tools/palette.json');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            colorPalette = await response.json();
            console.log('Violet Tools: Color palette loaded successfully');
        } catch (error) {
            console.warn('Violet Tools: Failed to load color palette:', error);
            colorPalette = null;
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

    // Enhance a widget with color chips
    function enhanceWidget(widget, node) {
        if (!shouldEnhanceWidget(widget, node)) return false;
        
        const fieldName = widget.name;
        const chipContainer = createColorChipContainer(widget, fieldName);
        if (!chipContainer) return false;
        
        // Find the widget element in the DOM
        const widgetElement = widget.element;
        if (!widgetElement || !widgetElement.parentNode) return false;
        
        // Insert chip container after the widget
        widgetElement.parentNode.insertBefore(chipContainer, widgetElement.nextSibling);
        
        // Mark as enhanced
        enhancedWidgets.add(widget);
        
        // Listen for widget value changes to update selection
        const originalCallback = widget.callback;
        widget.callback = function(value) {
            if (originalCallback) originalCallback.call(this, value);
            updateSelectedChip(chipContainer, value);
        };
        
        console.log(`Violet Tools: Enhanced ${fieldName} widget with color chips`);
        return true;
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
        version: '1.0.0'
    };

})();