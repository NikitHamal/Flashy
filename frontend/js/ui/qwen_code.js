/**
 * Qwen-Code UI Module
 * Handles the Qwen-Code free mode interface
 */

const QwenCodeUI = (() => {
    let currentProvider = 'qwen';
    let currentModel = 'qwen3.5-plus';
    let qwenCodeSession = null;
    let isQwenCodeMode = false;
    let providersData = {};

    async function init() {
        setupEventListeners();
        await loadProviders();
    }

    function setupEventListeners() {
        const openBtn = document.getElementById('btn-open-qwen-code');
        if (openBtn) {
            openBtn.addEventListener('click', openQwenCodeModal);
        }

        const modal = document.getElementById('qwen-code-modal');
        if (modal) {
            const closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', closeQwenCodeModal);
            }

            const backdrop = modal.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', closeQwenCodeModal);
            }
        }

        const startBtn = document.getElementById('btn-start-qwen-code');
        if (startBtn) {
            startBtn.addEventListener('click', startQwenCodeSession);
        }
    }

    async function loadProviders() {
        try {
            const response = await fetch('/api/qwen-code/providers');
            const data = await response.json();
            providersData = data.providers;
            renderModels(currentProvider);
        } catch (error) {
            console.error('Failed to load providers:', error);
        }
    }

    function openQwenCodeModal() {
        const modal = document.getElementById('qwen-code-modal');
        if (modal) {
            modal.classList.remove('hidden');
            renderModels(currentProvider);
        }
    }

    function closeQwenCodeModal() {
        const modal = document.getElementById('qwen-code-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    function renderModels(provider) {
        const container = document.getElementById('qwen-code-models');
        if (!container || !providersData[provider]) {
            return;
        }

        const models = providersData[provider].models;
        container.innerHTML = models.map(model => `
            <label class="model-option ${model.id === currentModel ? 'selected' : ''}" data-model="${model.id}">
                <input type="radio" name="model" value="${model.id}" ${model.id === currentModel ? 'checked' : ''}>
                <div class="model-info">
                    <span class="model-name">${model.name}</span>
                    <span class="model-id">${model.id}</span>
                </div>
            </label>
        `).join('');

        container.querySelectorAll('.model-option').forEach(option => {
            option.addEventListener('click', () => {
                container.querySelectorAll('.model-option').forEach(o => o.classList.remove('selected'));
                option.classList.add('selected');
                currentModel = option.dataset.model;
            });
        });
    }

    function setupProviderCards() {
        const cards = document.querySelectorAll('.provider-card');
        cards.forEach(card => {
            card.addEventListener('click', () => {
                cards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                currentProvider = card.dataset.provider;
                renderModels(currentProvider);
            });
        });
    }

    function startQwenCodeSession() {
        const sessionInput = document.getElementById('qwen-code-session');
        qwenCodeSession = sessionInput ? sessionInput.value : null;
        
        isQwenCodeMode = true;
        closeQwenCodeModal();
        
        // Update UI to show Qwen-Code mode
        showQwenCodeModeIndicator();
        
        // Update the model selector to show current selection
        updateModelSelector();
        
        // Show notification
        showNotification(`Qwen-Code mode activated: ${currentProvider} / ${currentModel}`, 'success');
    }

    function showQwenCodeModeIndicator() {
        let indicator = document.getElementById('qwen-code-mode-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'qwen-code-mode-indicator';
            indicator.className = 'qwen-code-mode-indicator';
            indicator.innerHTML = `
                <span class="material-symbols-outlined">smart_toy</span>
                <span id="qwen-code-mode-text">Qwen-Code: ${currentProvider}</span>
                <span class="material-symbols-outlined" style="font-size: 14px; cursor: pointer;" onclick="QwenCodeUI.exitQwenCodeMode()">close</span>
            `;
            
            const actionLeft = document.querySelector('.action-left');
            if (actionLeft) {
                actionLeft.appendChild(indicator);
            }
        } else {
            indicator.classList.remove('hidden');
            document.getElementById('qwen-code-mode-text').textContent = `Qwen-Code: ${currentProvider}`;
        }
    }

    function exitQwenCodeMode() {
        isQwenCodeMode = false;
        const indicator = document.getElementById('qwen-code-mode-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
        showNotification('Exited Qwen-Code mode', 'info');
    }

    function updateModelSelector() {
        const modelNameEl = document.getElementById('current-model-name');
        if (modelNameEl && isQwenCodeMode) {
            modelNameEl.textContent = `Qwen-Code (${currentModel})`;
        }
    }

    function isInQwenCodeMode() {
        return isQwenCodeMode;
    }

    function getQwenCodeConfig() {
        return {
            provider: currentProvider,
            model: currentModel,
            session: qwenCodeSession
        };
    }

    function showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with a proper notification system
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    // Initialize provider cards when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            setupProviderCards();
        }, 100);
    });

    return {
        init,
        openQwenCodeModal,
        closeQwenCodeModal,
        startQwenCodeSession,
        exitQwenCodeMode,
        isInQwenCodeMode,
        getQwenCodeConfig
    };
})();

// Make it globally available
window.QwenCodeUI = QwenCodeUI;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    QwenCodeUI.init();
});