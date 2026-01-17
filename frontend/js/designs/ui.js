(function () {
    const state = window.DesignState;
    const utils = window.DesignUtils;

    function initUI() {
        bindToolButtons();
        bindTopbar();
        bindPanels();
        bindProperties();
        bindAssets();
        bindPages();
        bindExport();
        bindChat();
        updateZoom();
        updateStatus();
    }

    function bindToolButtons() {
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tool = btn.dataset.tool;
                setTool(tool);
            });
        });
        setTool('select');
    }

    function setTool(tool) {
        state.currentTool = tool;
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === tool);
        });
        updateStatus(`Tool: ${tool}`);
    }

    function bindTopbar() {
        document.getElementById('btn-undo').addEventListener('click', () => window.DesignHistory.undo());
        document.getElementById('btn-redo').addEventListener('click', () => window.DesignHistory.redo());
        document.getElementById('btn-zoom-in').addEventListener('click', () => window.DesignCanvas.setZoom(state.zoom + 0.1));
        document.getElementById('btn-zoom-out').addEventListener('click', () => window.DesignCanvas.setZoom(state.zoom - 0.1));
        document.getElementById('btn-fit').addEventListener('click', () => window.DesignCanvas.fitToScreen());

        document.getElementById('canvas-preset').addEventListener('change', (e) => {
            const value = e.target.value;
            if (value === 'custom') {
                const width = parseInt(prompt('Canvas width (px)', '1200'), 10);
                const height = parseInt(prompt('Canvas height (px)', '800'), 10);
                if (width && height) {
                    window.DesignCanvas.setCanvasSize(width, height);
                }
                return;
            }
            const [w, h] = value.split('x').map(Number);
            window.DesignCanvas.setCanvasSize(w, h);
        });
    }

    function bindPanels() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.panel-pane').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                const pane = document.getElementById(`panel-${btn.dataset.tab}`);
                if (pane) pane.classList.add('active');
            });
        });
    }

    function bindProperties() {
        const fill = document.getElementById('prop-fill');
        const stroke = document.getElementById('prop-stroke');
        const strokeWidth = document.getElementById('prop-stroke-width');
        const opacity = document.getElementById('prop-opacity');
        const radius = document.getElementById('prop-radius');
        const text = document.getElementById('prop-text');
        const font = document.getElementById('prop-font');
        const fontSize = document.getElementById('prop-font-size');

        const applyProps = () => {
            const obj = state.canvas.getActiveObject();
            if (!obj) return;
            const props = {
                fill: fill.value,
                stroke: stroke.value,
                strokeWidth: parseFloat(strokeWidth.value) || 0,
                opacity: parseFloat(opacity.value) || 1,
                radius: parseFloat(radius.value) || 0,
                text: text.value,
                fontFamily: font.value,
                fontSize: parseInt(fontSize.value, 10) || 42
            };
            window.DesignCanvas.applyObjectProperties(obj, props);
        };

        [fill, stroke, strokeWidth, opacity, radius, text, font, fontSize].forEach(input => {
            input.addEventListener('input', applyProps);
        });

        document.querySelectorAll('.segmented button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.segmented button').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const obj = state.canvas.getActiveObject();
                if (obj && obj.type === 'i-text') {
                    obj.set({ textAlign: btn.dataset.align });
                    state.canvas.renderAll();
                    window.DesignHistory.capture();
                }
            });
        });
    }

    function bindAssets() {
        const drop = document.querySelector('.assets-drop');
        const upload = document.getElementById('asset-upload');

        drop.addEventListener('click', () => upload.click());
        drop.addEventListener('dragover', (e) => {
            e.preventDefault();
            drop.style.borderColor = 'rgba(53, 242, 181, 0.5)';
        });
        drop.addEventListener('dragleave', () => {
            drop.style.borderColor = 'rgba(255,255,255,0.2)';
        });
        drop.addEventListener('drop', (e) => {
            e.preventDefault();
            drop.style.borderColor = 'rgba(255,255,255,0.2)';
            handleAssetFiles(e.dataTransfer.files);
        });

        upload.addEventListener('change', (e) => {
            handleAssetFiles(e.target.files);
            e.target.value = '';
        });
    }

    function handleAssetFiles(files) {
        if (!files || files.length === 0) return;
        Array.from(files).forEach(file => {
            if (!file.type.startsWith('image/')) return;
            const reader = new FileReader();
            reader.onload = () => {
                state.assets.push({ id: utils.uid('asset'), src: reader.result });
                refreshAssets();
                window.DesignCanvas.addImageFromFile(file);
            };
            reader.readAsDataURL(file);
        });
    }

    function refreshAssets() {
        const grid = document.getElementById('assets-grid');
        if (!grid) return;
        grid.innerHTML = '';
        state.assets.forEach(asset => {
            const div = document.createElement('div');
            div.className = 'asset-thumb';
            div.innerHTML = `<img src="${asset.src}" alt="asset">`;
            div.addEventListener('click', () => {
                fabric.Image.fromURL(asset.src, (img) => {
                    img.set({ left: 120, top: 120, scaleX: 0.6, scaleY: 0.6 });
                    state.canvas.add(img);
                    state.canvas.renderAll();
                    window.DesignHistory.capture();
                });
            });
            grid.appendChild(div);
        });
    }

    function bindPages() {
        document.getElementById('btn-new-page').addEventListener('click', () => addPage());
        document.getElementById('btn-duplicate-page').addEventListener('click', () => duplicatePage());
    }

    function addPage() {
        const id = utils.uid('page');
        const name = `Page ${state.pages.length + 1}`;
        state.pages.push({ id, name, json: null });
        switchPage(id);
    }

    function duplicatePage() {
        const current = state.pages.find(p => p.id === state.currentPageId);
        if (!current) return;
        const id = utils.uid('page');
        const name = `${current.name} Copy`;
        const json = state.canvas ? state.canvas.toJSON(['id']) : current.json;
        state.pages.push({ id, name, json });
        switchPage(id);
    }

    function switchPage(id) {
        const page = state.pages.find(p => p.id === id);
        if (!page || !state.canvas) return;
        const current = state.pages.find(p => p.id === state.currentPageId);
        if (current) {
            current.json = state.canvas.toJSON(['id']);
        }
        state.currentPageId = id;
        if (page.json) {
            state.canvas.loadFromJSON(page.json, () => {
                state.canvas.renderAll();
                refreshPages();
                refreshLayers();
            });
        } else {
            state.canvas.clear();
            state.canvas.setBackgroundColor('#ffffff', state.canvas.renderAll.bind(state.canvas));
            refreshPages();
        }
    }

    function refreshPages() {
        const list = document.getElementById('pages-list');
        if (!list) return;
        list.innerHTML = '';
        state.pages.forEach(page => {
            const item = document.createElement('div');
            item.className = `page-item ${page.id === state.currentPageId ? 'active' : ''}`;
            item.innerHTML = `<span>${page.name}</span><span>${state.canvas ? state.canvas.getObjects().length : 0}</span>`;
            item.addEventListener('click', () => switchPage(page.id));
            list.appendChild(item);
        });
    }

    function bindExport() {
        const modal = document.getElementById('export-modal');
        document.getElementById('btn-export').addEventListener('click', () => modal.classList.remove('hidden'));
        document.getElementById('btn-close-export').addEventListener('click', () => modal.classList.add('hidden'));

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.add('hidden');
        });

        document.querySelectorAll('.export-card').forEach(card => {
            card.addEventListener('click', async () => {
                const format = card.dataset.format;
                const scale = parseInt(document.getElementById('export-scale').value, 10);
                const bg = document.getElementById('export-bg').value;
                await window.DesignExport.exportDesign(format, scale, bg);
                modal.classList.add('hidden');
            });
        });

        document.getElementById('btn-send-to-agent').addEventListener('click', () => {
            window.DesignChat.sendCanvasToAgent();
        });
    }

    function bindChat() {
        const input = document.getElementById('design-chat-input');
        const send = document.getElementById('btn-chat-send');
        const attach = document.getElementById('btn-chat-attach');
        const fileInput = document.getElementById('design-file-input');
        const newChat = document.getElementById('btn-new-chat');

        send.addEventListener('click', () => {
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            input.style.height = 'auto';
            window.DesignChat.sendMessage(text);
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send.click();
            }
        });

        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = `${input.scrollHeight}px`;
        });

        attach.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                const files = Array.from(fileInput.files);
                window.DesignChat.sendMessage('Here are reference assets for the current design.', files);
                fileInput.value = '';
            }
        });

        newChat.addEventListener('click', () => {
            document.getElementById('design-chat-history').innerHTML = '';
            state.sessionId = `design_${Date.now()}`;
            updateStatus('New chat session');
        });

        document.querySelectorAll('.chip').forEach(chip => {
            chip.addEventListener('click', () => {
                input.value = chip.dataset.prompt;
                input.focus();
            });
        });
    }

    function syncSelection() {
        const obj = state.canvas.getActiveObject();
        if (!obj) {
            document.getElementById('status-selection').textContent = 'No selection';
            return;
        }
        document.getElementById('status-selection').textContent = `${obj.type} selected`;

        if (obj.fill) document.getElementById('prop-fill').value = obj.fill;
        if (obj.stroke) document.getElementById('prop-stroke').value = obj.stroke;
        document.getElementById('prop-stroke-width').value = obj.strokeWidth || 0;
        document.getElementById('prop-opacity').value = obj.opacity ?? 1;
        document.getElementById('prop-radius').value = obj.rx || 0;

        if (obj.type === 'i-text') {
            document.getElementById('prop-text').value = obj.text || '';
            document.getElementById('prop-font').value = obj.fontFamily || 'Space Grotesk';
            document.getElementById('prop-font-size').value = obj.fontSize || 42;
        }
        refreshLayers();
    }

    function refreshLayers() {
        const list = document.getElementById('layers-list');
        if (!list || !state.canvas) return;
        list.innerHTML = '';
        const objects = state.canvas.getObjects();
        objects.forEach(obj => {
            if (!obj.id) obj.id = utils.uid('layer');
            const item = document.createElement('div');
            item.className = `layer-item ${state.canvas.getActiveObject() === obj ? 'active' : ''}`;
            item.innerHTML = `<span>${obj.type}</span><span>${obj.visible ? 'Visible' : 'Hidden'}</span>`;
            item.addEventListener('click', () => {
                state.canvas.setActiveObject(obj);
                state.canvas.renderAll();
                syncSelection();
            });
            list.appendChild(item);
        });
    }

    function updateStatus(message = 'Ready') {
        const status = document.getElementById('status-message');
        if (status) status.textContent = message;
        if (state.canvas) {
            document.getElementById('status-size').textContent = `${state.canvas.width} x ${state.canvas.height}`;
        }
    }

    function updateZoom() {
        document.getElementById('zoom-value').textContent = `${Math.round(state.zoom * 100)}%`;
    }

    window.DesignUI = {
        initUI,
        setTool,
        updateStatus,
        updateZoom,
        syncSelection,
        refreshLayers,
        refreshPages
    };
})();
