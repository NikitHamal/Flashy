async function setupModelSelector() {
    const selectorButton = document.getElementById('btn-model-selector');
    const modelMenu = document.getElementById('model-dropdown-menu');

    if (!selectorButton || !modelMenu) return;

    selectorButton.addEventListener('click', (event) => {
        event.stopPropagation();
        modelMenu.classList.toggle('hidden');
    });

    await refreshModels();
}

async function refreshModels() {
    try {
        const config = await API.getConfig();
        const activeProvider = config.active_provider;
        const cacheKey = `models_${activeProvider}`;
        const cached = localStorage.getItem(cacheKey);

        if (cached && activeProvider !== 'chat2api') {
            cachedModels = JSON.parse(cached);
            renderModelDropdown();
        }

        cachedModels = await API.getModels();
        localStorage.setItem(cacheKey, JSON.stringify(cachedModels));
        renderModelDropdown();

        if (UI.updateFeatureVisibility) {
            UI.updateFeatureVisibility(activeProvider);
        }

        if (activeProvider === 'qwen') {
            document.getElementById('current-model-name').textContent = 'Qwen AI';
            return;
        }

        const activeModelId = config.model;
        const activeModel = cachedModels.find((model) => model.id === activeModelId);
        document.getElementById('current-model-name').textContent = activeModel ? activeModel.name : (activeModelId || 'Select Model');
    } catch (error) {
        console.error('Failed to refresh models', error);
    }
}

function renderModelDropdown() {
    const modelMenu = document.getElementById('model-dropdown-menu');
    if (!modelMenu) return;

    if (cachedModels.length === 0) {
        modelMenu.innerHTML = '<div class="dropdown-item">No models available</div>';
        return;
    }

    modelMenu.innerHTML = cachedModels.map((model) => `
        <div class="dropdown-item" data-id="${model.id}" data-name="${model.name}">
            <div class="item-info">
                <span class="item-title">${model.name}</span>
                <span class="item-meta">${model.id}</span>
            </div>
        </div>
    `).join('');

    modelMenu.querySelectorAll('.dropdown-item').forEach((item) => {
        item.addEventListener('click', async () => {
            await selectModel(item.getAttribute('data-id'), item.getAttribute('data-name'));
        });
    });
}

async function selectModel(id, name) {
    try {
        const config = await API.getConfig();
        config.model = id;
        await API.saveConfig(config);

        if (config.active_provider === 'qwen') {
            document.getElementById('current-model-name').textContent = 'Qwen AI';
        } else {
            document.getElementById('current-model-name').textContent = name;
        }

        document.getElementById('model-dropdown-menu').classList.add('hidden');
        console.log(`Model selected: ${name} (${id})`);
    } catch (error) {
        alert(`Failed to save model selection: ${error.message}`);
    }
}
