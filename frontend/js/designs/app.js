document.addEventListener('DOMContentLoaded', () => {
    const canvas = window.DesignCanvas.initCanvas('design-canvas', 1080, 1080);
    window.DesignUI.initUI();

    canvas.on('object:added', () => window.DesignHistory.capture());
    canvas.on('object:modified', () => window.DesignHistory.capture());
    canvas.on('object:removed', () => window.DesignHistory.capture());

    window.DesignUI.refreshPages();
    window.DesignUI.refreshLayers();
    window.DesignHistory.capture();
    window.DesignCanvas.fitToScreen();

    if (window.DesignState.pages.length === 0) {
        window.DesignUI.setTool('select');
        const initialPageId = window.DesignUtils.uid('page');
        window.DesignState.pages.push({ id: initialPageId, name: 'Page 1', json: canvas.toJSON(['id']) });
        window.DesignState.currentPageId = initialPageId;
        window.DesignUI.refreshPages();
    }

    window.addEventListener('resize', () => {
        window.DesignCanvas.fitToScreen();
    });
});
