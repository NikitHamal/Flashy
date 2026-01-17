(function () {
    const state = window.DesignState;
    const utils = window.DesignUtils;

    async function exportDesign(format, scale, background) {
        if (!state.canvas) return null;
        const prevBg = state.canvas.backgroundColor;
        if (background === 'white') {
            state.canvas.setBackgroundColor('#ffffff', state.canvas.renderAll.bind(state.canvas));
        }
        if (background === 'transparent') {
            state.canvas.setBackgroundColor(null, state.canvas.renderAll.bind(state.canvas));
        }

        if (format === 'json') {
            const json = JSON.stringify(state.canvas.toJSON(['id']), null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            utils.downloadBlob(blob, 'flashy-design.json');
            state.canvas.setBackgroundColor(prevBg, state.canvas.renderAll.bind(state.canvas));
            return null;
        }

        if (format === 'svg') {
            const svg = state.canvas.toSVG();
            const blob = new Blob([svg], { type: 'image/svg+xml' });
            utils.downloadBlob(blob, 'flashy-design.svg');
            state.canvas.setBackgroundColor(prevBg, state.canvas.renderAll.bind(state.canvas));
            return null;
        }

        const dataUrl = state.canvas.toDataURL({
            format: format,
            multiplier: scale
        });
        const blob = await (await fetch(dataUrl)).blob();
        utils.downloadBlob(blob, `flashy-design.${format}`);
        state.canvas.setBackgroundColor(prevBg, state.canvas.renderAll.bind(state.canvas));
        return blob;
    }

    async function exportCanvasBlob(scale = 2) {
        if (!state.canvas) return null;
        const dataUrl = state.canvas.toDataURL({ format: 'png', multiplier: scale });
        return await (await fetch(dataUrl)).blob();
    }

    window.DesignExport = {
        exportDesign,
        exportCanvasBlob
    };
})();
