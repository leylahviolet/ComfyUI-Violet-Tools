// Simple test script to verify ComfyUI is loading our web extensions
console.log('🧪 Violet Tools test script loaded!');
window.vtTestLoaded = true;
window.vtTest = function() {
    console.log('✅ Violet Tools web extension loading is working!');
    return 'Extension loading confirmed';
};