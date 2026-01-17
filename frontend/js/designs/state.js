window.DesignState = {
    sessionId: `design_${Date.now()}`,
    currentTool: 'select',
    canvas: null,
    zoom: 1,
    pages: [],
    currentPageId: null,
    history: {
        undo: [],
        redo: [],
        isRestoring: false
    },
    assets: [],
    isPanning: false,
    panStart: null
};

window.DesignUtils = {
    uid(prefix = 'id') {
        return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
    },
    clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    },
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    }
};
