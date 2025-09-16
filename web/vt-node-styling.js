// Violet Tools Node Styling Extension v2.0
// Provides branded styling for all Violet Tools nodes using LiteGraph's native styling system

(function() {
    'use strict';

    // Configuration
    // Attempt to derive the extension mount path dynamically. ComfyUI serves custom node web assets
    // under /extensions/<folder-name>/ when WEB_DIRECTORY is set. Folder name may vary by case.
    function deriveBasePath() {
        // Manual override (set before script loads): window.VioletToolsBasePath = '/extensions/YourPath/'
        if (window.VioletToolsBasePath) return window.VioletToolsBasePath;
        try {
            const scripts = Array.from(document.getElementsByTagName('script'));
            const hit = scripts.find(s => /vt-node-styling\.js/i.test(s.src)) || scripts.find(s => /vt-colorchips\.js/i.test(s.src));
            if (hit && hit.src) {
                const m = hit.src.match(/\/extensions\/[^/]+\//i);
                if (m) return m[0].endsWith('/') ? m[0] : m[0] + '/';
            }
        } catch(e) {}
        return '/extensions/comfyui-violet-tools/';
    }

    const BASE_PATH = deriveBasePath();

    function buildLogoCandidates() {
        // Generate case variants for robustness
        const raw = BASE_PATH.replace(/\/$/, '');
        const folder = raw.split('/').pop();
        const root = raw.slice(0, raw.length - folder.length);
        const variants = [folder, folder.toLowerCase(), folder.toUpperCase()];
        const unique = Array.from(new Set(variants));
        return unique.map(v => `${root}${v}/VT_logo.png`);
    }

    const LOGO_CANDIDATES = buildLogoCandidates();

    const CONFIG = {
        backgroundColor: '#1D0C29',        // Purple background color
        textColor: null,                   // Use default text color (removed custom purple)
        logoOpacity: 0.9,                  // Logo transparency
    logoUrl: LOGO_CANDIDATES[0],
        enabled: true,                     // Master enable/disable
        debugLogging: false,               // Disable debug logging now that it's working
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
        if (logoImage) return logoImage;
        let idx = 0;
        function tryNext() {
            if (idx >= LOGO_CANDIDATES.length) {
                if (CONFIG.debugLogging) console.warn('Violet Tools: All logo paths failed', LOGO_CANDIDATES);
                logoImage = null;
                return;
            }
            const url = LOGO_CANDIDATES[idx++];
            logoImage = new Image();
            logoImage.crossOrigin = 'anonymous';
            logoImage.onload = function() {
                CONFIG.logoUrl = url;
                if (CONFIG.debugLogging) console.log('Violet Tools: Logo loaded at', url);
            };
            logoImage.onerror = function() {
                if (CONFIG.debugLogging) console.log('Violet Tools: Logo failed at', url, '— trying next');
                logoImage = null;
                tryNext();
            };
            logoImage.src = url;
        }
        tryNext();
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
        
        // Set a darker color for the title bar (node.color is used for title bar background)
        node.color = '#0F0517'; // Much darker purple for title bar readability
        
        // Set border color for better visibility
        node.boxcolor = '#666666';
        
        // Custom draw function to add logo
        const originalOnDrawBackground = node.onDrawBackground;
        node.onDrawBackground = function(ctx, canvas) {
            // Call original background drawing if it exists
            if (originalOnDrawBackground) {
                originalOnDrawBackground.call(this, ctx, canvas);
            }
            
            // Draw logo only on EncodingEnchantress
            const _type = (this.type || '').toLowerCase();
            if (logoImage && logoImage.complete && _type === 'encodingenchantress') {
                ctx.save();
                ctx.globalAlpha = CONFIG.logoOpacity;
                
                // Fill available height (below title) while preserving aspect ratio
                const padTop = 26;     // leave space for title bar
                const padSide = 8;     // side/bottom padding
                const maxH = Math.max(0, this.size[1] - padTop - padSide);
                const maxW = Math.max(0, this.size[0] - padSide * 2);

                const iw = logoImage.naturalWidth  || logoImage.width  || 1;
                const ih = logoImage.naturalHeight || logoImage.height || 1;
                const aspect = iw / ih;

                // Restore full size: fit as large as possible below title while preserving aspect
                let h = maxH;
                let w = h * aspect;
                if (w > maxW) { w = maxW; h = w / aspect; }

                // Raise the logo upward: anchor nearer the title bar, leaving only minimal padTop
                const logoX = (this.size[0] - w) / 2;
                // Flush to very top (ignore padTop)
                let logoY = 0;

                ctx.globalAlpha = CONFIG.logoOpacity;
                ctx.drawImage(logoImage, logoX, logoY, w, h);
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

    // Install widget style wrapper (idempotent)
    function installWidgetSkins() {
        if (!window.LiteGraph || !LiteGraph.LGraphCanvas) return;
        const proto = LiteGraph.LGraphCanvas.prototype;
        if (proto._vtOriginalDrawNodeWidgets) return; // already wrapped
        proto._vtOriginalDrawNodeWidgets = proto.drawNodeWidgets;
        proto.drawNodeWidgets = function(node, ctx, posY, skipReadOnly) {
            const ws = CONFIG.widgetStyle;
            const eligible = ws && ws.enabled && node && isVioletToolsNode(node);
            if (!eligible) {
                return proto._vtOriginalDrawNodeWidgets.call(this, node, ctx, posY, skipReadOnly);
            }
            // Snapshot original LiteGraph color constants
            const originals = {
                WIDGET_BGCOLOR: LiteGraph.WIDGET_BGCOLOR,
                WIDGET_OUTLINE_COLOR: LiteGraph.WIDGET_OUTLINE_COLOR,
                WIDGET_TEXT_COLOR: LiteGraph.WIDGET_TEXT_COLOR,
                WIDGET_SECONDARY_TEXT_COLOR: LiteGraph.WIDGET_SECONDARY_TEXT_COLOR,
                WIDGET_BORDER_COLOR: LiteGraph.WIDGET_BORDER_COLOR
            };
            // Apply themed values
            LiteGraph.WIDGET_BGCOLOR = ws.bg;
            LiteGraph.WIDGET_BORDER_COLOR = ws.border;
            LiteGraph.WIDGET_OUTLINE_COLOR = ws.outlineHover;
            LiteGraph.WIDGET_TEXT_COLOR = ws.text;
            LiteGraph.WIDGET_SECONDARY_TEXT_COLOR = ws.textSecondary;
            try {
                // If multiline styling enabled, pre-pass to paint backgrounds for qualifying widgets.
                if (ws.multiline && ws.multiline.enabled && node && node.widgets && ctx) {
                    try {
                        // We approximate widget vertical layout similar to LiteGraph's internal logic.
                        const startY = posY;
                        let y = startY;
                        const spacing = 4; // default widget spacing
                        const nodeWidth = node.size ? node.size[0] : 140;
                        for (let i = 0; i < node.widgets.length; i++) {
                            const w = node.widgets[i];
                            let h = 0;
                            try {
                                if (w.computeSize) {
                                    const sz = w.computeSize(nodeWidth);
                                    h = Array.isArray(sz) ? sz[1] : sz;
                                }
                            } catch {}
                            if (!h || h < 20) h = 20; // baseline min
                            // Heuristic: treat very tall widgets (>=50px) or widgets explicitly flagged as multiline
                            const isMultiline = h >= 50 || /text|prompt|multi/i.test(w.name || '') || w.type === 'text' && h > 30;
                            if (isMultiline) {
                                const ml = ws.multiline;
                                const padX = ml.paddingX;
                                const padY = ml.paddingY;
                                const radius = ml.radius;
                                const rectX = 4 + padX * 0.5; // small left inset
                                const rectY = y - 2; // small vertical inset above
                                const rectW = nodeWidth - 8 - padX; // symmetric inset
                                const rectH = h + padY * 2 - 2; // include bottom padding
                                ctx.save();
                                ctx.beginPath();
                                if (radius > 0) {
                                    const r = Math.min(radius, rectH * 0.5, rectW * 0.5);
                                    ctx.moveTo(rectX + r, rectY);
                                    ctx.lineTo(rectX + rectW - r, rectY);
                                    ctx.quadraticCurveTo(rectX + rectW, rectY, rectX + rectW, rectY + r);
                                    ctx.lineTo(rectX + rectW, rectY + rectH - r);
                                    ctx.quadraticCurveTo(rectX + rectW, rectY + rectH, rectX + rectW - r, rectY + rectH);
                                    ctx.lineTo(rectX + r, rectY + rectH);
                                    ctx.quadraticCurveTo(rectX, rectY + rectH, rectX, rectY + rectH - r);
                                    ctx.lineTo(rectX, rectY + r);
                                    ctx.quadraticCurveTo(rectX, rectY, rectX + r, rectY);
                                } else {
                                    ctx.rect(rectX, rectY, rectW, rectH);
                                }
                                ctx.fillStyle = ml.bg;
                                ctx.fill();
                                ctx.lineWidth = 1.5;
                                ctx.strokeStyle = ml.border;
                                ctx.stroke();
                                if (ml.glow) {
                                    ctx.globalCompositeOperation = 'lighter';
                                    ctx.fillStyle = ml.glow;
                                    ctx.fill();
                                    ctx.globalCompositeOperation = 'source-over';
                                }
                                ctx.restore();
                            }
                            y += h + spacing;
                        }
                    } catch(e) { /* ignore drawing errors */ }
                }
                return proto._vtOriginalDrawNodeWidgets.call(this, node, ctx, posY, skipReadOnly);
            } finally {
                // Restore originals so non‑Violet nodes + other extensions remain unaffected
                LiteGraph.WIDGET_BGCOLOR = originals.WIDGET_BGCOLOR;
                LiteGraph.WIDGET_OUTLINE_COLOR = originals.WIDGET_OUTLINE_COLOR;
                LiteGraph.WIDGET_TEXT_COLOR = originals.WIDGET_TEXT_COLOR;
                LiteGraph.WIDGET_SECONDARY_TEXT_COLOR = originals.WIDGET_SECONDARY_TEXT_COLOR;
                LiteGraph.WIDGET_BORDER_COLOR = originals.WIDGET_BORDER_COLOR;
            }
        };
        if (CONFIG.debugLogging) console.log('Violet Tools: Widget skin hook installed');
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
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Initializing node styling extension v2.0...');
        }
        
        // Load logo
        loadLogo();
        
        // Style existing nodes after a delay
        setTimeout(() => {
            styleAllNodes();
        }, 1000);
        // Install widget skin wrapper after LiteGraph likely loaded
        installWidgetSkins();
        
        // Start observing for new nodes
        observeNodes();
        
        // Periodic re-styling (fallback)
        setInterval(() => {
            styleAllNodes();
        }, 10000);
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Node styling extension v2.0 initialized');
        }
    }

    // Update configuration
    function updateConfig(newConfig) {
        // Support nested widgetStyle merge instead of wholesale replace
        if (newConfig.widgetStyle && typeof newConfig.widgetStyle === 'object') {
            Object.assign(CONFIG.widgetStyle, newConfig.widgetStyle);
            delete newConfig.widgetStyle; // prevent overwrite below
        }
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
            installWidgetSkins(); // ensure wrapper present if enabling later
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
            console.log('\nWidget style active:', CONFIG.widgetStyle.enabled, '-> toggle with VioletToolsNodeStylingV2.updateConfig({ widgetStyle: { enabled: true } })');
        }
    };

    // Shared global namespace + debug helpers
    window.VioletTools = window.VioletTools || {};
    if (!window.VioletTools.enableDebug) {
        window.VioletTools.enableDebug = function() {
            try {
                if (window.VioletToolsNodeStylingV2) {
                    window.VioletToolsNodeStylingV2.config.debugLogging = true;
                }
                if (window.VioletToolsColorChips) {
                    window.VioletToolsColorChips.config.debugLogging = true;
                }
                console.log('Violet Tools: Debug logging ENABLED');
            } catch(e) {}
        };
    }
    if (!window.VioletTools.disableDebug) {
        window.VioletTools.disableDebug = function() {
            try {
                if (window.VioletToolsNodeStylingV2) {
                    window.VioletToolsNodeStylingV2.config.debugLogging = false;
                }
                if (window.VioletToolsColorChips) {
                    window.VioletToolsColorChips.config.debugLogging = false;
                }
                console.log('Violet Tools: Debug logging DISABLED');
            } catch(e) {}
        };
    }

})();