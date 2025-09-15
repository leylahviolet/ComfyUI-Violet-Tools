/**
 * Violet Tools Color Chips Extension - Debugging Version
 * Testing without async/fetch to isolate syntax errors
 */

console.log('🚀 [VT-COLORCHIPS-DEBUG] Script execution started...');

(function() {
    'use strict';

    console.log('🚀 [VT-COLORCHIPS-DEBUG] Inside IIFE...');

    // Configuration
    const CONFIG = {
        chipSize: 16,
        maxRows: 4,
        animationDuration: 200,
        showTooltips: true,
        enableSearch: false
    };

    console.log('🚀 [VT-COLORCHIPS-DEBUG] Config loaded...');

    // Simple fallback palette without async loading
    let colorPalette = {
        colorFields: {
            "base_color": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"],
            "color": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"],
            "accent_color": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
        }
    };

    console.log('🚀 [VT-COLORCHIPS-DEBUG] Palette loaded...');

    // Simple test function without complex logic
    function testChips() {
        console.log('=== Violet Tools Color Chips Debug Test ===');
        console.log('Extension is working without async loading');
        console.log('Available color fields:', Object.keys(colorPalette.colorFields));
        return true;
    }

    // Expose functions
    window.testChipsDebug = testChips;
    
    window.vtColorChipsDebugLoaded = function() {
        console.log('✅ Debug Violet Tools Color Chips extension is loaded!');
        console.log('Available functions: testChipsDebug()');
        return true;
    };
    
    console.log('🎨 [VT-COLORCHIPS-DEBUG] Extension loaded successfully');

})();