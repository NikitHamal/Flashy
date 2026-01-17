(function () {
    const state = window.DesignState;

    let captureTimer = null;

    function capture() {
        if (!state.canvas || state.history.isRestoring) return;
        clearTimeout(captureTimer);
        captureTimer = setTimeout(() => {
            const snapshot = state.canvas.toJSON(['id']);
            state.history.undo.push(snapshot);
            if (state.history.undo.length > 50) {
                state.history.undo.shift();
            }
            state.history.redo = [];
            window.DesignUI.updateStatus('Saved');
        }, 120);
    }

    function undo() {
        if (!state.canvas || state.history.undo.length === 0) return;
        const current = state.canvas.toJSON(['id']);
        const prev = state.history.undo.pop();
        state.history.redo.push(current);
        restore(prev);
    }

    function redo() {
        if (!state.canvas || state.history.redo.length === 0) return;
        const current = state.canvas.toJSON(['id']);
        const next = state.history.redo.pop();
        state.history.undo.push(current);
        restore(next);
    }

    function restore(snapshot) {
        state.history.isRestoring = true;
        state.canvas.loadFromJSON(snapshot, () => {
            state.canvas.renderAll();
            state.history.isRestoring = false;
            window.DesignUI.syncSelection();
            window.DesignUI.refreshLayers();
        });
    }

    window.DesignHistory = {
        capture,
        undo,
        redo
    };
})();
