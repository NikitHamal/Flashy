document.addEventListener('DOMContentLoaded', async () => {
    await refreshState();

    if (window.QwenTerminal) {
        window.qwenTermInstance = new QwenTerminal();
    }

    if (UI.initQwenFeatures) {
        UI.initQwenFeatures();
    }

    setupShellEventListeners();
    setupComposerEventListeners();
    setupWebSocketHandlers();
    initResizers();
    await handleRouting();
});

window.addEventListener('popstate', () => {
    handleRouting();
});
