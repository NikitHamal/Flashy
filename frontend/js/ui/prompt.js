// Prompt Composer Logic
Object.assign(UI, {
    addUploadedFiles(files) {
        Array.from(files).forEach((file) => {
            this.uploadedFiles.push(file);
        });
        this.renderUploadedFiles();
    },

    removeUploadedFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.renderUploadedFiles();
    },

    clearUploadedFiles() {
        this.uploadedFiles = [];
        this.renderUploadedFiles();
    },

    renderUploadedFiles() {
        if (!this.elements.uploadPreviewsContainer) return;
        if (this.uploadedFiles.length === 0) {
            this.elements.uploadPreviewsContainer.classList.add('hidden');
            return;
        }

        this.elements.uploadPreviewsContainer.classList.remove('hidden');
        this.elements.uploadPreviewsContainer.innerHTML = '';

        this.uploadedFiles.forEach((file, index) => {
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item';

            if (file.type.startsWith('image/')) {
                const image = document.createElement('img');
                image.src = URL.createObjectURL(file);
                previewItem.appendChild(image);
            } else {
                const icon = document.createElement('span');
                icon.className = 'material-symbols-outlined file-icon';
                icon.textContent = 'description';
                previewItem.appendChild(icon);
            }

            const removeButton = document.createElement('div');
            removeButton.className = 'remove-btn';
            removeButton.innerHTML = '<span class="material-symbols-outlined" style="font-size: 14px;">close</span>';
            removeButton.onclick = () => this.removeUploadedFile(index);

            const nameLabel = document.createElement('div');
            nameLabel.className = 'file-name';
            nameLabel.textContent = file.name;

            previewItem.appendChild(removeButton);
            previewItem.appendChild(nameLabel);
            this.elements.uploadPreviewsContainer.appendChild(previewItem);
        });
    },

    addTaggedFile(file) {
        if (this.taggedFiles.find((item) => item.path === file.path)) return;
        this.taggedFiles.push(file);
        this.renderTaggedFiles();
    },

    removeTaggedFile(path) {
        this.taggedFiles = this.taggedFiles.filter((item) => item.path !== path);
        this.renderTaggedFiles();
    },

    clearTaggedFiles() {
        this.taggedFiles = [];
        this.renderTaggedFiles();
    },

    renderTaggedFiles() {
        if (!this.elements.taggedFilesContainer) return;
        if (this.taggedFiles.length === 0) {
            this.elements.taggedFilesContainer.classList.add('hidden');
            return;
        }

        this.elements.taggedFilesContainer.classList.remove('hidden');
        this.elements.taggedFilesContainer.innerHTML = '';

        this.taggedFiles.forEach((file) => {
            const chip = document.createElement('div');
            chip.className = 'file-chip';
            chip.innerHTML = `
                <span class="material-symbols-outlined">description</span>
                <span>${file.name}</span>
                <span class="material-symbols-outlined remove-btn">close</span>
            `;
            chip.querySelector('.remove-btn').onclick = () => this.removeTaggedFile(file.path);
            this.elements.taggedFilesContainer.appendChild(chip);
        });
    },

    showMentionPopup(files, onSelect) {
        if (!this.elements.mentionPopup) return;

        this.elements.mentionPopup.classList.remove('hidden');
        this.elements.mentionPopup.innerHTML = '';

        if (files.length === 0) {
            this.elements.mentionPopup.innerHTML = '<div class="mention-item">No files found</div>';
            return;
        }

        files.forEach((file, index) => {
            const item = document.createElement('div');
            item.className = 'mention-item';
            if (index === 0) item.classList.add('active');
            item.innerHTML = `
                <span class="material-symbols-outlined icon">description</span>
                <span class="name">${file.name}</span>
                <span class="path">${file.path}</span>
            `;
            item.onclick = (event) => {
                event.stopPropagation();
                onSelect(file);
                this.hideMentionPopup();
            };
            this.elements.mentionPopup.appendChild(item);
        });
    },

    hideMentionPopup() {
        if (this.elements.mentionPopup) {
            this.elements.mentionPopup.classList.add('hidden');
        }
    },

    navigateMention(direction) {
        if (!this.elements.mentionPopup || this.elements.mentionPopup.classList.contains('hidden')) return;

        const items = Array.from(this.elements.mentionPopup.querySelectorAll('.mention-item'));
        if (items.length === 0) return;

        let activeIndex = items.findIndex((item) => item.classList.contains('active'));
        if (activeIndex === -1) {
            activeIndex = 0;
        } else {
            items[activeIndex].classList.remove('active');
            activeIndex = direction === 'up'
                ? (activeIndex - 1 + items.length) % items.length
                : (activeIndex + 1) % items.length;
        }

        const nextItem = items[activeIndex];
        nextItem.classList.add('active');
        nextItem.scrollIntoView({ block: 'nearest' });
    },

    initInputAutoResize() {
        if (!this.elements.chatInput) return;
        this.elements.chatInput.addEventListener('input', () => {
            this.elements.chatInput.style.height = 'auto';
            this.elements.chatInput.style.height = `${this.elements.chatInput.scrollHeight}px`;
            if (this.isWorking) return;
            this.elements.sendBtn.classList.toggle('active', this.elements.chatInput.value.trim().length > 0);
        });
    },

    initQwenFeatures() {
        const { qwenSearchBtn, qwenResearchBtn, qwenThinkingSelect, qwenFeaturesInline } = this.elements;
        if (!qwenFeaturesInline) return;

        this.qwenState = {
            search: false,
            research: false,
            thinkingMode: 'Auto'
        };

        if (qwenSearchBtn) {
            qwenSearchBtn.onclick = () => {
                this.qwenState.search = !this.qwenState.search;
                qwenSearchBtn.classList.toggle('active', this.qwenState.search);
                if (this.qwenState.search && this.qwenState.research && qwenResearchBtn) {
                    this.qwenState.research = false;
                    qwenResearchBtn.classList.remove('active');
                }
            };
        }

        if (qwenResearchBtn) {
            qwenResearchBtn.onclick = () => {
                this.qwenState.research = !this.qwenState.research;
                qwenResearchBtn.classList.toggle('active', this.qwenState.research);
                if (this.qwenState.research && this.qwenState.search && qwenSearchBtn) {
                    this.qwenState.search = false;
                    qwenSearchBtn.classList.remove('active');
                }
            };
        }

        if (qwenThinkingSelect) {
            qwenThinkingSelect.onchange = (event) => {
                this.qwenState.thinkingMode = event.target.value;
            };
        }
    },

    updateFeatureVisibility(provider) {
        if (this.elements.qwenFeaturesInline) {
            this.elements.qwenFeaturesInline.classList.toggle('hidden', provider !== 'qwen');
        }
    },

    getQwenParams() {
        if (!this.qwenState) return {};

        let chat_type = 't2t';
        if (this.qwenState.search) chat_type = 'search';
        if (this.qwenState.research) chat_type = 'deep_research';

        return {
            chat_type,
            thinking_enabled: this.qwenState.thinkingMode !== 'Disabled',
            thinking_mode: this.qwenState.thinkingMode === 'Disabled' ? 'Auto' : this.qwenState.thinkingMode
        };
    }
});
