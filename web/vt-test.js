// Simple test script to verify ComfyUI is loading our web extensions
console.log('🧪 [VT-TEST] Script loading started...');

try {
    console.log('🧪 [VT-TEST] Setting up window properties...');
    window.vtTestLoaded = true;
    
    window.vtTest = function() {
        console.log('✅ [VT-TEST] Function called successfully!');
        return 'Extension loading confirmed';
    };
    
    console.log('🧪 [VT-TEST] Script loaded successfully!');
    console.log('🧪 [VT-TEST] Available: window.vtTest()');
} catch (error) {
    console.error('❌ [VT-TEST] Error during script loading:', error);
}