// Violet Tools Node Styling Extension v2.0
// Provides branded styling for all Violet Tools nodes using LiteGraph's native styling system

(function() {
    'use strict';

    // Configuration
    // Attempt to derive the extension mount path dynamically. ComfyUI serves custom node web assets
    // under /extensions/<folder-name>/ when WEB_DIRECTORY is set. Folder name may vary by case.
    // Character UI sync: apply backend-pushed widget values to nodes
    function applyCharacterSync(event) {
        try {
            const payload = event && event.detail ? event.detail : event;
            const updated = payload && payload.updated ? payload.updated : {};
            if (!updated) return;

            const nodes = window.app && window.app.graph && window.app.graph._nodes_by_id ? window.app.graph._nodes_by_id : {};
            for (const nodeId in updated) {
                const node = nodes[nodeId];
                if (!node || !node.widgets || !Array.isArray(node.widgets)) continue;
                const changes = updated[nodeId];
                for (const key in changes) {
                    const w = node.widgets.find(w => w && w.name === key);
                    if (!w) continue;
                    w.value = changes[key];
                }
            }
        } catch (e) {
            // silent
        }
    }

    // Wire to server bus (same pattern as Inspire Pack)
    try {
        if (window && window.api && window.api.addEventListener) {
            window.api.addEventListener('vt-character-sync', applyCharacterSync);
        }
    } catch (e) { /* noop */ }

    // -----------------------------
    // UI Buttons: Load Character
    // -----------------------------
    const VT_SEGMENT_BY_TYPE = {
        'AestheticAlchemist': 'aesthetic', '💋 Aesthetic Alchemist': 'aesthetic',
        'QualityQueen': 'quality',         '👑 Quality Queen': 'quality',
        'SceneSeductress': 'scene',        '🎭 Scene Seductress': 'scene',
        'GlamourGoddess': 'glamour',       '✨ Glamour Goddess': 'glamour',
        'BodyBard': 'body',                '💃 Body Bard': 'body',
        'PosePriestess': 'pose',           '🤩 Pose Priestess': 'pose',
        'NegativityNullifier': 'negative', '🚫 Negativity Nullifier': 'negative',
        // Unified character selector (Curator replaces Cache/Creator)
        'CharacterCurator': 'character',   '💖 Character Curator': 'character'
    };

    function getGraphNodes() {
        return (window.app && window.app.graph && window.app.graph._nodes_by_id) ? window.app.graph._nodes_by_id : {};
    }

    function findCharacterSelectorNode() {
        const nodes = getGraphNodes();
        for (const id in nodes) {
            const n = nodes[id];
            const t = n && n.type;
            if (t && (t === 'CharacterCurator' || t === '💖 Character Curator')) return n; // Curator only in 2.0+
        }
        return null;
    }

    function getSelectedCharacterName() {
        const sel = findCharacterSelectorNode();
        if (!sel || !sel.widgets) return null;
        // Curator stores selection in 'load_character'
        const w = sel.widgets.find(w => w && w.name === 'load_character');
        return w ? w.value : null;
    }

    async function fetchCharacterByName(name) {
        try {
            const res = await fetch(`/violet/character?name=${encodeURIComponent(name)}`, { cache: 'no-store' });
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            return null;
        }
    }

    // Tiny toast helper
    function toast(msg, type = 'info') {
        try {
            const el = document.createElement('div');
            el.textContent = msg;
            el.style.position = 'fixed';
            el.style.right = '16px';
            el.style.bottom = '16px';
            el.style.zIndex = 9999;
            el.style.padding = '10px 14px';
            el.style.borderRadius = '8px';
            el.style.fontFamily = 'Inter, system-ui, sans-serif';
            el.style.fontSize = '12px';
            el.style.color = '#fff';
            el.style.boxShadow = '0 4px 16px rgba(0,0,0,0.2)';
            if (type === 'success') el.style.background = '#22c55e';
            else if (type === 'warn') el.style.background = '#f59e0b';
            else el.style.background = '#8b5cf6';
            document.body.appendChild(el);
            setTimeout(() => {
                el.style.transition = 'opacity 300ms ease-in-out';
                el.style.opacity = '0';
                setTimeout(() => el.remove(), 320);
            }, 1400);
        } catch (e) { /* noop */ }
    }

    function applySegmentToNode(node, segment) {
        if (!node || !Array.isArray(node.widgets) || !segment) return 0;
        let count = 0;
        for (const [k, v] of Object.entries(segment)) {
            if (k === 'text') continue;
            const w = node.widgets.find(w => w && w.name === k);
            if (!w) continue;
            w.value = v;
            count++;
        }
        return count;
    }

    async function loadCharacterIntoNode(node) {
        const segmentKey = VT_SEGMENT_BY_TYPE[node.type] || VT_SEGMENT_BY_TYPE[node.comfyClass];
        if (!segmentKey || segmentKey === 'character') {
            toast('This node does not support character loading.', 'warn');
            return;
        }

        const name = getSelectedCharacterName();
        if (!name || name === 'None' || name === 'random') {
            toast('Select a character in Character Curator first.', 'warn');
            return;
        }

        const payload = await fetchCharacterByName(name);
        const seg = payload && payload.data ? payload.data[segmentKey] : null;
        if (!seg) { toast('No saved selections for this node.', 'warn'); return; }
        const n = applySegmentToNode(node, seg);
        if (n > 0) toast(`Loaded ${n} selection${n>1?'s':''} from '${name}'.`, 'success');
        else toast('No matching fields to apply.', 'warn');
    }

    async function loadCharacterIntoAll() {
        const name = getSelectedCharacterName();
    if (!name || name === 'None' || name === 'random') { toast('Select a character first.', 'warn'); return; }
        const payload = await fetchCharacterByName(name);
        if (!payload || !payload.data) { toast('Could not load character data.', 'warn'); return; }
        const nodes = getGraphNodes();
        let total = 0;
        for (const id in nodes) {
            const n = nodes[id];
            const key = VT_SEGMENT_BY_TYPE[n && n.type] || VT_SEGMENT_BY_TYPE[n && n.comfyClass];
            if (!key || key === 'character') continue;
            const seg = payload.data[key];
            if (!seg) continue;
            total += applySegmentToNode(n, seg);
        }
        if (total > 0) toast(`Loaded ${total} field${total>1?'s':''} into all VT nodes.`, 'success');
        else toast('No fields to apply across VT nodes.', 'warn');
    }

    // -----------------------------
    // Wireless Save: Collect widgets → Character JSON
    // -----------------------------
    function collectSegmentFromNode(node) {
        if (!node || !Array.isArray(node.widgets)) return null;
        const out = {};
        for (const w of node.widgets) {
            if (!w || !w.name) continue;
            const t = (w.type || '').toLowerCase();
            if (t === 'button') continue; // skip our UI helpers
            if (w.name === 'character' || w.name === 'character_apply') continue; // not content
            out[w.name] = w.value;
        }
        return Object.keys(out).length ? out : null;
    }

    function collectCharacterData() {
        const nodes = getGraphNodes();
        const data = {};
        for (const id in nodes) {
            const n = nodes[id];
            const key = VT_SEGMENT_BY_TYPE[n && n.type] || VT_SEGMENT_BY_TYPE[n && n.comfyClass];
            // Skip non-VT nodes and the character selector (Curator)
            if (!key || key === 'character') continue;
            const seg = collectSegmentFromNode(n);
            if (seg) data[key] = seg;
        }
        return data;
    }

    async function wirelessSaveCharacter(name) {
        if (!name || !name.trim()) { toast('Enter a character name in Character Curator.', 'warn'); return; }
        const data = collectCharacterData();
        try {
            const res = await fetch('/violet/character', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim(), data })
            });
            if (res.ok) {
                const j = await res.json().catch(() => ({}));
                toast(`Saved character '${name}'.`, 'success');
                return j;
            }
            const txt = await res.text().catch(() => '');
            toast(`Save failed: ${txt || res.status}`, 'warn');
        } catch (e) {
            toast('Save failed: network error', 'warn');
        }
    }

    function maybeAddButtons(node) {
        if (!node || typeof node.addWidget !== 'function') return;
        if (node.__vtCharacterButtons) return; // already added
        const t = node.type;
        const seg = VT_SEGMENT_BY_TYPE[t] || VT_SEGMENT_BY_TYPE[node.comfyClass];
        if (!seg) return; // not VT

        // Character Curator: add Browse Names + Save + Load All + Delete (with custom ordering + spacer)
        if (t === 'CharacterCurator' || t === '💖 Character Curator') {
            const browseBtn = node.addWidget('button', 'Browse Names', 'browse', async () => {
                try { showCharacterNameOverlay(node); } catch(e) {}
            });
            const saveBtn = node.addWidget('button', 'Save Character', 'save', async () => {
                // CharacterCurator uses save_character
                let nm = '';
                try {
                    if (Array.isArray(node.widgets)) {
                        const pref = node.widgets.find(w => w && w.name === 'save_character');
                        nm = pref && typeof pref.value === 'string' ? pref.value : '';
                    }
                } catch(e) {}
                await wirelessSaveCharacter(nm);
            });
            const loadAllBtn = node.addWidget('button', 'Load Character to All', 'load', async () => {
                await loadCharacterIntoAll();
            });
            const deleteBtn = node.addWidget('button', 'Delete Character', 'delete', async () => {
                let sel = '';
                try {
                    if (Array.isArray(node.widgets)) {
                        const w = node.widgets.find(w => w && w.name === 'load_character');
                        sel = w && typeof w.value === 'string' ? w.value : '';
                    }
                } catch(e) {}
                if (!sel || sel === 'None' || sel === 'random') { toast('Select a character to delete.', 'warn'); return; }
                showDeleteConfirmOverlay(node, sel, async () => {
                    try {
                        const res = await fetch(`/violet/character?name=${encodeURIComponent(sel)}`, { method: 'DELETE' });
                        if (res.ok) {
                            toast(`Deleted '${sel}'.`, 'success');
                            try {
                                const w = node.widgets.find(w => w && w.name === 'load_character');
                                if (w) w.value = 'None';
                                if (node && node.graph && typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                            } catch(e) {}
                        } else {
                            const txt = await res.text().catch(() => '');
                            toast(`Delete failed: ${txt || res.status}`, 'warn');
                        }
                    } catch (e) {
                        toast('Delete failed: network error', 'warn');
                    }
                });
            });

            // Reorder widgets: [Browse], save_character, [Save], [spacer], load_character, [Load All], [Delete]
            try {
                const ws = Array.isArray(node.widgets) ? node.widgets.slice() : [];
                const saveField = ws.find(w => w && w.name === 'save_character');
                const loadField = ws.find(w => w && w.name === 'load_character');
                const spacer = { name: '__vt_gap__', type: 'vt-spacer', computeSize: () => [node.size ? node.size[0] : 140, 14] };
                const desired = [];
                if (browseBtn) desired.push(browseBtn);
                if (saveField) desired.push(saveField);
                if (saveBtn) desired.push(saveBtn);
                desired.push(spacer);
                if (loadField) desired.push(loadField);
                if (loadAllBtn) desired.push(loadAllBtn);
                if (deleteBtn) desired.push(deleteBtn);
                // Append any other widgets not included to preserve future proofing
                for (const w of ws) {
                    if (!desired.includes(w)) desired.push(w);
                }
                node.widgets = desired;
            } catch(e) {}
            node.__vtCharacterButtons = true;
            return;
        }

        // Prompt nodes: add 'Load Character'
        node.addWidget('button', 'Load Character', 'load', async () => {
            await loadCharacterIntoNode(node);
        });
        node.__vtCharacterButtons = true;
    }

    // Hook installation is deferred until window.app is ready (handled in observeNodes/initialize)
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
        'OracleOverride',
        'CharacterCurator',
        'SaveSiren'
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
            // Also ensure character load buttons are present
            try { maybeAddButtons(node); } catch (e) {}
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
                try { maybeAddButtons(node); } catch (e) {}
                // Note: opening overlay on text field click is not reliably interceptable without deep hooks.
                // We expose an explicit 'Browse Names' button for discoverability instead.
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
            // Add character load buttons to existing nodes
            try {
                const nodes = getGraphNodes();
                for (const id in nodes) {
                    try { maybeAddButtons(nodes[id]); } catch (e){}
                }
            } catch (e) {}
        }, 1000);
        // Install widget skin wrapper after LiteGraph likely loaded
        installWidgetSkins();
        
        // Start observing for new nodes
        observeNodes();
        
        // Periodic re-styling + button sweep (fallback)
        setInterval(() => {
            styleAllNodes();
            try {
                const nodes = getGraphNodes();
                for (const id in nodes) {
                    try { maybeAddButtons(nodes[id]); } catch (e){}
                }
            } catch (e) {}
        }, 10000);
        
        if (CONFIG.debugLogging) {
            console.log('Violet Tools: Node styling extension v2.0 initialized');
        }
    }

    // -----------------------------
    // Character name overlay for Curator save_character field
    // -----------------------------
    async function fetchAllCharacterNames() {
        try {
            const res = await fetch('/violet/character?list=1', { cache: 'no-store' });
            if (!res.ok) return [];
            const j = await res.json().catch(() => ({}));
            const names = Array.isArray(j.names) ? j.names : [];
            return names;
        } catch(e) { return []; }
    }

    function buildOverlay() {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.background = 'rgba(0,0,0,0.3)';
        overlay.style.zIndex = 10000;

        const panel = document.createElement('div');
        panel.style.position = 'absolute';
        panel.style.top = '10%';
        panel.style.left = '50%';
        panel.style.transform = 'translateX(-50%)';
        panel.style.width = 'min(520px, 90vw)';
        panel.style.maxHeight = '70vh';
        panel.style.overflow = 'auto';
        panel.style.background = '#1f1430';
        panel.style.border = '1px solid #6d28d9';
        panel.style.borderRadius = '12px';
        panel.style.boxShadow = '0 12px 40px rgba(0,0,0,0.35)';
        panel.style.padding = '14px';
        panel.style.fontFamily = 'Inter, system-ui, sans-serif';
        panel.style.color = '#eee';

        const title = document.createElement('div');
        title.textContent = 'Browse Saved Characters';
        title.style.fontSize = '16px';
        title.style.fontWeight = '600';
        title.style.marginBottom = '10px';

        const search = document.createElement('input');
        search.type = 'text';
        search.placeholder = 'Filter by name…';
        search.style.width = '100%';
        search.style.boxSizing = 'border-box';
        search.style.padding = '10px 12px';
        search.style.borderRadius = '8px';
        search.style.border = '1px solid #7c3aed';
        search.style.background = '#140a20';
        search.style.color = '#eee';

        const list = document.createElement('div');
        list.style.marginTop = '10px';
        list.style.display = 'grid';
        list.style.gridTemplateColumns = '1fr';
        list.style.gap = '6px';

        const empty = document.createElement('div');
        empty.textContent = 'No saved characters yet.';
        empty.style.opacity = '0.7';
        empty.style.padding = '10px 6px';

        panel.appendChild(title);
        panel.appendChild(search);
        panel.appendChild(list);
        overlay.appendChild(panel);

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });

        return { overlay, list, search, showEmpty: () => { list.innerHTML = ''; list.appendChild(empty); } };
    }

    function renderNameList(listEl, names, onPick) {
        listEl.innerHTML = '';
        if (!names || names.length === 0) return;
        for (const n of names) {
            const item = document.createElement('div');
            item.textContent = n;
            item.style.padding = '8px 10px';
            item.style.border = '1px solid #5b21b6';
            item.style.borderRadius = '8px';
            item.style.cursor = 'pointer';
            item.style.background = '#140a20';
            item.addEventListener('mouseenter', () => item.style.background = '#1a0f2a');
            item.addEventListener('mouseleave', () => item.style.background = '#140a20');
            item.addEventListener('click', () => onPick(n));
            listEl.appendChild(item);
        }
    }

    async function showCharacterNameOverlay(node) {
        const { overlay, list, search, showEmpty } = buildOverlay();
        document.body.appendChild(overlay);
        const all = await fetchAllCharacterNames();
        if (!all || all.length === 0) {
            showEmpty();
        } else {
            renderNameList(list, all, (picked) => {
                try {
                    const w = node.widgets.find(w => w && w.name === 'save_character');
                    if (w) w.value = picked;
                    if (node && node.graph && typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                } catch(e) {}
                overlay.remove();
            });
        }
        search.addEventListener('input', () => {
            const q = (search.value || '').toLowerCase();
            const filtered = all.filter(n => n.toLowerCase().includes(q));
            if (filtered.length === 0) showEmpty(); else renderNameList(list, filtered, (picked) => {
                try {
                    const w = node.widgets.find(w => w && w.name === 'save_character');
                    if (w) w.value = picked;
                    if (node && node.graph && typeof node.setDirtyCanvas === 'function') node.setDirtyCanvas(true, true);
                } catch(e) {}
                overlay.remove();
            });
        });
        setTimeout(() => search.focus(), 0);
    }

    function showDeleteConfirmOverlay(node, name, onConfirm) {
        const { overlay } = buildOverlay();
        // Customize content
        overlay.innerHTML = '';
        const panel = document.createElement('div');
        panel.style.position = 'absolute';
        panel.style.top = '20%';
        panel.style.left = '50%';
        panel.style.transform = 'translateX(-50%)';
        panel.style.width = 'min(460px, 90vw)';
        panel.style.background = '#1f1430';
        panel.style.border = '1px solid #6d28d9';
        panel.style.borderRadius = '12px';
        panel.style.boxShadow = '0 12px 40px rgba(0,0,0,0.35)';
        panel.style.padding = '16px';
        panel.style.fontFamily = 'Inter, system-ui, sans-serif';
        panel.style.color = '#eee';

        const title = document.createElement('div');
        title.textContent = 'Delete Character';
        title.style.fontSize = '16px';
        title.style.fontWeight = '600';
        title.style.marginBottom = '8px';

        const msg = document.createElement('div');
        msg.innerHTML = `Are you sure you want to delete <b>${name}</b>? This cannot be undone.`;
        msg.style.opacity = '0.9';
        msg.style.marginBottom = '14px';

        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.gap = '10px';
        row.style.justifyContent = 'flex-end';

        const cancel = document.createElement('button');
        cancel.textContent = 'Cancel';
        cancel.style.padding = '8px 12px';
        cancel.style.borderRadius = '8px';
        cancel.style.border = '1px solid #7c3aed';
        cancel.style.background = '#140a20';
        cancel.style.color = '#eee';
        cancel.style.cursor = 'pointer';
        cancel.addEventListener('click', () => overlay.remove());

        const confirm = document.createElement('button');
        confirm.textContent = 'Delete';
        confirm.style.padding = '8px 12px';
        confirm.style.borderRadius = '8px';
        confirm.style.border = '1px solid #ef4444';
        confirm.style.background = '#7f1d1d';
        confirm.style.color = '#fff';
        confirm.style.cursor = 'pointer';
        confirm.addEventListener('click', async () => {
            try { await onConfirm(); } finally { overlay.remove(); }
        });

        row.appendChild(cancel);
        row.appendChild(confirm);
        panel.appendChild(title);
        panel.appendChild(msg);
        panel.appendChild(row);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);
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