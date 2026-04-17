(function (global) {
    global.UI = global.UI || {};
    global.UI.__legacyBundle = true;

    if (!global.__FLASHY_LEGACY_UI_WARNED__) {
        console.warn(
            '[Flashy] frontend/js/ui.js is a legacy compatibility shim. ' +
            'Use the modular UI bundles in /js/ui/*.js instead.'
        );
        global.__FLASHY_LEGACY_UI_WARNED__ = true;
    }
})(window);
