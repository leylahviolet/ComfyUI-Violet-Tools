// Violet Tools Node Styling Extension v2.0
// Provides branded styling for all Violet Tools nodes using LiteGraph's native styling system

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        backgroundColor: '#1D0C29',        // Purple background color
        textColor: null,                   // Use default text color (removed custom purple)
        logoOpacity: 0.9,                  // Logo transparency
        logoUrl: '/extensions/comfyui-violet-tools/VT_logo.png',
        enabled: true,                     // Master enable/disable
        debugLogging: false                // Disable debug logging now that it's working
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
    let logoImage = null;

    // Load the logo image
    function loadLogo() {
        if (!logoImage) {
            logoImage = new Image();
            logoImage.crossOrigin = 'anonymous';
            logoImage.onload = function() {
                if (CONFIG.debugLogging) {
                    console.log('Violet Tools: Logo loaded successfully');
                }
            };
            logoImage.onerror = function() {
                if (CONFIG.debugLogging) {
                    console.log('Violet Tools: Failed to load logo');
                }
                logoImage = null;
            };
            logoImage.src = CONFIG.logoUrl;
        }
        return logoImage;
    }

    // Check if a node is a Violet Tools node
    function isVioletToolsNode(node) {
        if (!node || !node.type) return false;
        return VIOLET_TOOLS_NODES.includes(node.type);
    }

    // Apply LiteGraph styling to a node
    function styleNode(node) {
        if (!node || !isVioletToolsNode(node) || styledNodes.has(node)) {
            return false;
        }

        // Set node background color using LiteGraph properties
        node.bgcolor = CONFIG.backgroundColor;
        
        // Don't override text color - let ComfyUI use its default
        // node.color = CONFIG.textColor; // Removed
        
        // Set border color for better visibility
        node.boxcolor = CONFIG.textColor || '#666666';
        
        // Custom draw function to add logo
        const originalOnDrawBackground = node.onDrawBackground;
        node.onDrawBackground = function(ctx, canvas) {
            // Call original background drawing if it exists
            if (originalOnDrawBackground) {
                originalOnDrawBackground.call(this, ctx, canvas);
            }
            
            // Draw logo overlay - make it much bigger and more prominent
            if (logoImage && logoImage.complete) {
                ctx.save();
                ctx.globalAlpha = CONFIG.logoOpacity;
                
                // Calculate logo position and size - much bigger and more centered
                const logoSize = Math.min(this.size[0] * 0.4, this.size[1] * 0.5, 80); // Much larger
                const logoX = (this.size[0] - logoSize) / 2; // Center horizontally
                const logoY = (this.size[1] - logoSize) / 2; // Center vertically
                
                // Add a subtle background circle for the logo for better visibility
                ctx.globalAlpha = 0.2;
                ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
                ctx.beginPath();
                ctx.arc(logoX + logoSize/2, logoY + logoSize/2, logoSize/2 + 8, 0, 2 * Math.PI);
                ctx.fill();
                
                // Draw the logo
                ctx.globalAlpha = CONFIG.logoOpacity;
                ctx.drawImage(logoImage, logoX, logoY, logoSize, logoSize);
                ctx.restore();
            }
        };

        // Mark as styled
        styledNodes.add(node);
        
        if (CONFIG.debugLogging) {
            console.log(`Violet Tools: Successfully styled ${node.type} node with LiteGraph styling`);
        }
        
        // Force redraw
        if (node.graph && node.graph.canvas) {
            node.setDirtyCanvas(true, true);
        }
        
        return true;
    }

    // Style all existing nodes
    function styleAllNodes() {
        if (!window.app || !window.app.graph || !window.app.graph._nodes) {
            if (CONFIG.debugLogging) {
                console.log('Violet Tools: No graph or nodes found');
            }
            return;
        }

        let styledCount = 0;
        const totalNodes = window.app.graph._nodes.length;
        
        if (CONFIG.debugLogging) {
            console.log(`Violet Tools: Checking ${totalNodes} nodes for styling`);
        }
        
        window.app.graph._nodes.forEach((node) => {
            if (styleNode(node)) {
                styledCount++;
            }
        });
        
        if (CONFIG.debugLogging && styledCount > 0) {
            console.log(`Violet Tools: Styled ${styledCount} out of ${totalNodes} nodes`);
        }
    }

    // Monitor for new nodes
    function observeNodes() {
        if (!window.app || !window.app.graph) return;
        
        // Hook into node creation
        const originalAdd = window.app.graph.add;
        window.app.graph.add = function(node) {
            const result = originalAdd.call(this, node);
            
            // Style the node after a short delay to ensure it's fully initialized
            setTimeout(() => {
                styleNode(node);
            }, 100);
            
            return result;
        };
    }

    // Initialize the extension
    function initialize() {
        if (!CONFIG.enabled) return;
        
        console.log('Violet Tools: Initializing node styling extension v2.0...');
        
        // Load logo
        loadLogo();
        
        // Style existing nodes after a delay
        setTimeout(() => {
            styleAllNodes();
        }, 1000);
        
        // Start observing for new nodes
        observeNodes();
        
        // Periodic re-styling (fallback)
        setInterval(() => {
            styleAllNodes();
        }, 10000);
        
        console.log('Violet Tools: Node styling extension v2.0 initialized');
    }

    // Update configuration
    function updateConfig(newConfig) {
        Object.assign(CONFIG, newConfig);
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Configuration updated', CONFIG);
        }
        
        // Reload logo if URL changed
        if (newConfig.logoUrl) {
            logoImage = null;
            loadLogo();
        }
        
        // Re-style all nodes
        setTimeout(() => {
            styleAllNodes();
        }, 500);
    }

    // Start initialization when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // Expose API for debugging and customization
    window.VioletToolsNodeStylingV2 = {
        config: CONFIG,
        updateConfig: updateConfig,
        styleAllNodes: styleAllNodes,
        styleNode: styleNode,
        version: '2.0.0',
        // Manual test function
        testStyling: function() {
            console.log('=== Violet Tools LiteGraph Styling Test v2.0 ===');
            
            if (!window.app || !window.app.graph) {
                console.log('❌ No app or graph found');
                return;
            }
            
            const violetNodes = window.app.graph._nodes.filter(node => 
                node.type && VIOLET_TOOLS_NODES.includes(node.type)
            );
            
            console.log(`Found ${violetNodes.length} Violet Tools nodes:`, violetNodes.map(n => n.type));
            
            if (violetNodes.length === 0) {
                console.log('No Violet Tools nodes found. Add some to test styling.');
                return;
            }
            
            console.log('\n✅ All nodes are properly styled with:');
            console.log(`  • Background color: ${CONFIG.backgroundColor}`);
            console.log(`  • Text color: Default ComfyUI color (no override)`);
            console.log(`  • Logo opacity: ${CONFIG.logoOpacity}`);
            console.log(`  • Large centered logo with subtle background circle`);
            
            // Check if nodes have the styling
            const styledNodes = violetNodes.filter(node => 
                node.bgcolor === CONFIG.backgroundColor
            );
            
            console.log(`\n${styledNodes.length}/${violetNodes.length} nodes have the correct styling applied.`);
            
            if (styledNodes.length === violetNodes.length) {
                console.log('🎉 All Violet Tools nodes are perfectly styled!');
            } else {
                console.log('⚠️ Some nodes may need re-styling. Running styleAllNodes()...');
                styleAllNodes();
            }
            
            console.log('\n=== Test complete ===');
        }
    };

})();