/**
 * Violet Tools Node Styling Extension
 * Applies distinctive purple branding and logo background to all Violet Tools nodes
 * For use with ComfyUI to create recognizable, branded node appearance
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        backgroundColor: '#1D0C29',        // Purple background color
        textColor: '#D780F6',              // Light purple text color
        logoOpacity: 0.8,                  // Logo transparency (0.0 - 1.0)
        logoUrl: '/extensions/comfyui-violet-tools/VT_logo.png',
        enabled: true,                     // Master enable/disable
        debugLogging: false                // Disable debug console logging (was too spammy)
    };

    // List of all Violet Tools node class names
    const VIOLET_TOOLS_NODES = [
        'GlamourGoddess',
        'BodyBard', 
        'AestheticAlchemist',
        'QualityQueen',
        'SceneSeductress',
        'PosePriestess',
        'EncodingEnchantress',
        'NegativityNullifier',
        'CharacterCreator',
        'CharacterCache'
    ];

    // Track styled nodes to avoid duplicate styling
    const styledNodes = new WeakSet();

    // CSS styles for Violet Tools nodes
    const getNodeStyles = () => `
        /* Violet Tools Node Background Styling */
        .violet-tools-node {
            background-color: ${CONFIG.backgroundColor} !important;
            background-image: url('${CONFIG.logoUrl}') !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-size: auto 100% !important;
            overflow: hidden !important;
            position: relative !important;
        }
        
        /* Logo overlay with configurable opacity */
        .violet-tools-node::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background-image: url('${CONFIG.logoUrl}') !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-size: auto 100% !important;
            opacity: ${CONFIG.logoOpacity} !important;
            pointer-events: none !important;
            z-index: 0 !important;
        }
        
        /* Text color styling for better contrast */
        .violet-tools-node .comfy-title,
        .violet-tools-node .comfy-node-title,
        .violet-tools-node .node-title,
        .violet-tools-node .litegraph-node-title,
        .violet-tools-node .title,
        .violet-tools-node span,
        .violet-tools-node label,
        .violet-tools-node .widget-label {
            color: ${CONFIG.textColor} !important;
            position: relative !important;
            z-index: 1 !important;
        }
        
        /* Ensure widgets and content stay above background */
        .violet-tools-node .widget,
        .violet-tools-node .comfy-widget,
        .violet-tools-node .widget-container,
        .violet-tools-node input,
        .violet-tools-node select,
        .violet-tools-node textarea,
        .violet-tools-node button {
            position: relative !important;
            z-index: 1 !important;
        }
        
        /* Input/widget styling for better visibility */
        .violet-tools-node input,
        .violet-tools-node select,
        .violet-tools-node textarea {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(215, 128, 246, 0.3) !important;
            color: #FFFFFF !important;
        }
        
        /* Button styling */
        .violet-tools-node button {
            background-color: rgba(215, 128, 246, 0.2) !important;
            border: 1px solid rgba(215, 128, 246, 0.5) !important;
            color: ${CONFIG.textColor} !important;
        }
        
        .violet-tools-node button:hover {
            background-color: rgba(215, 128, 246, 0.3) !important;
            border-color: ${CONFIG.textColor} !important;
        }
    `;

    // Inject CSS styles
    function injectStyles() {
        const styleId = 'vt-node-styling';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = getNodeStyles();
        document.head.appendChild(style);
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Node styling CSS injected');
        }
    }

    // Check if a node is a Violet Tools node
    function isVioletToolsNode(node) {
        if (!node || !node.type) return false;
        
        const nodeType = node.type;
        const isVioletTools = VIOLET_TOOLS_NODES.includes(nodeType);
        
        // Only log when we find a Violet Tools node, not for every node
        if (CONFIG.debugLogging && isVioletTools) {
            console.log(`Violet Tools: Found ${nodeType} node for styling`);
        }
        
        return isVioletTools;
    }

    // Apply styling to a single node
    function styleNode(node) {
        if (!node || !isVioletToolsNode(node) || styledNodes.has(node)) {
            if (CONFIG.debugLogging && node && isVioletToolsNode(node) && styledNodes.has(node)) {
                console.log(`Violet Tools: Node ${node.type} already styled, skipping`);
            }
            return false;
        }
        
        // Find the DOM element for this node
        const nodeElement = findNodeElement(node);
        if (!nodeElement) {
            if (CONFIG.debugLogging) {
                console.log(`Violet Tools: Could not find DOM element for ${node.type} node`);
            }
            return false;
        }
        
        // Apply the styling class
        nodeElement.classList.add('violet-tools-node');
        
        // Mark as styled
        styledNodes.add(node);
        
        if (CONFIG.debugLogging) {
            console.log(`Violet Tools: Successfully styled ${node.type} node`, nodeElement);
        }
        
        return true;
    }

    // Find the DOM element for a given node
    function findNodeElement(node) {
        if (CONFIG.debugLogging) {
            console.log(`Violet Tools: Looking for DOM element for node:`, node);
            console.log(`Node properties:`, {
                element: node.element,
                domNode: node.domNode, 
                node: node.node,
                id: node.id,
                title: node.title
            });
        }
        
        // Try different methods to find the node's DOM element
        if (node.element) {
            if (CONFIG.debugLogging) console.log('Found via node.element');
            return node.element;
        }
        if (node.domNode) {
            if (CONFIG.debugLogging) console.log('Found via node.domNode');
            return node.domNode;
        }
        if (node.node) {
            if (CONFIG.debugLogging) console.log('Found via node.node');
            return node.node;
        }
        
        // Fallback: search by node ID or other identifiers
        if (node.id !== undefined) {
            const candidate = document.querySelector(`[data-node-id="${node.id}"]`);
            if (candidate) {
                if (CONFIG.debugLogging) console.log(`Found via data-node-id="${node.id}"`);
                return candidate;
            }
        }
        
        // Try to find by title or other attributes
        if (node.title) {
            const candidates = document.querySelectorAll('.comfy-node, .litegraph-node');
            for (const candidate of candidates) {
                const titleElement = candidate.querySelector('.comfy-node-header, .litegraph-title');
                if (titleElement && titleElement.textContent === node.title) {
                    if (CONFIG.debugLogging) console.log(`Found via title match: "${node.title}"`);
                    return candidate;
                }
            }
        }
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Could not find DOM element for node');
        }
        
        return null;
    }

    // Style all existing nodes
    function styleAllNodes() {
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Attempting to style all nodes...');
            console.log('Window app:', window.app);
            console.log('App graph:', window.app?.graph);
            console.log('Graph nodes:', window.app?.graph?._nodes);
        }
        
        if (!window.app || !window.app.graph || !window.app.graph._nodes) {
            if (CONFIG.debugLogging) {
                console.log('Violet Tools: No nodes found in app.graph._nodes, trying alternative approaches...');
            }
            
            // Try alternative node access methods
            let nodes = null;
            if (window.app?.graph?.nodes) {
                nodes = window.app.graph.nodes;
            } else if (window.app?.graph?._nodes_by_id) {
                nodes = Object.values(window.app.graph._nodes_by_id);
            }
            
            if (nodes) {
                if (CONFIG.debugLogging) {
                    console.log(`Violet Tools: Found ${nodes.length} nodes via alternative method`);
                }
                
                let styledCount = 0;
                nodes.forEach(node => {
                    if (styleNode(node)) {
                        styledCount++;
                    }
                });
                
                if (CONFIG.debugLogging) {
                    console.log(`Violet Tools: Styled ${styledCount} nodes`);
                }
                return;
            }
            
            if (CONFIG.debugLogging) {
                console.log('Violet Tools: No nodes found via any method');
            }
            return;
        }
        
        let styledCount = 0;
        const totalNodes = window.app.graph._nodes.length;
        
        if (CONFIG.debugLogging) {
            console.log(`Violet Tools: Found ${totalNodes} total nodes`);
        }
        
        window.app.graph._nodes.forEach((node, index) => {
            if (CONFIG.debugLogging && index < 3) { // Log first 3 nodes for debugging
                console.log(`Node ${index}:`, node.type, node);
            }
            
            if (styleNode(node)) {
                styledCount++;
            }
        });
        
        if (CONFIG.debugLogging) {
            console.log(`Violet Tools: Styled ${styledCount} out of ${totalNodes} nodes`);
        }
    }

    // Monitor for new nodes
    function observeNodes() {
        // Hook into LiteGraph node creation if available
        if (window.LiteGraph && window.LiteGraph.LGraphNode) {
            const originalOnAdded = window.LiteGraph.LGraphNode.prototype.onAdded;
            window.LiteGraph.LGraphNode.prototype.onAdded = function(graph) {
                const result = originalOnAdded ? originalOnAdded.call(this, graph) : undefined;
                
                // Small delay to ensure DOM is ready
                setTimeout(() => {
                    styleNode(this);
                }, 100);
                
                return result;
            };
        }
        
        // Also monitor DOM changes as a fallback
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if this looks like a ComfyUI node
                        if (node.classList && (node.classList.contains('comfy-node') || node.classList.contains('litegraph-node'))) {
                            // Try to find associated graph node and style it
                            setTimeout(() => styleAllNodes(), 50);
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Update configuration
    function updateConfig(newConfig) {
        Object.assign(CONFIG, newConfig);
        
        // Re-inject styles with new configuration
        const existingStyle = document.getElementById('vt-node-styling');
        if (existingStyle) {
            existingStyle.remove();
        }
        injectStyles();
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Configuration updated', CONFIG);
        }
    }

    // Initialize the extension
    function initialize() {
        if (!CONFIG.enabled) return;
        
        console.log('Violet Tools: Initializing node styling extension...');
        
        // Inject CSS styles
        injectStyles();
        
        // Style existing nodes
        setTimeout(() => {
            styleAllNodes();
        }, 1000);
        
        // Start observing for new nodes
        observeNodes();
        
        // Periodic re-styling (fallback) - reduced frequency
        setInterval(() => {
            styleAllNodes();
        }, 10000); // Changed from 5 seconds to 10 seconds
        
        console.log('Violet Tools: Node styling extension initialized');
    }

    // Start initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // Expose configuration for debugging and customization
    window.VioletToolsNodeStyling = {
        config: CONFIG,
        updateConfig: updateConfig,
        styleAllNodes: styleAllNodes,
        styleNode: styleNode,
        version: '1.0.0'
    };

})();