const AstroApp = {
    sessionId: `astro_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,

    init() {
        this.cacheElements();
        AstroUI.init();
        AstroChat.init();
        this.bindEvents();
        this.handleInitialRoute();
        this.syncKundalis();
    },

    cacheElements() {
        this.modal = document.getElementById('kundali-modal');
        this.nameInput = document.getElementById('form-name');
        this.genderInput = document.getElementById('form-gender');
        this.dateInput = document.getElementById('form-date');
        this.timeInput = document.getElementById('form-time');
        this.placeInput = document.getElementById('form-place');
        this.latInput = document.getElementById('form-lat');
        this.lonInput = document.getElementById('form-lon');
        this.tzInput = document.getElementById('form-tz');
    },

    bindEvents() {
        document.getElementById('btn-new-kundali')?.addEventListener('click', () => this.openModal());
        document.getElementById('btn-empty-create')?.addEventListener('click', () => this.openModal());
        document.getElementById('btn-empty-ai')?.addEventListener('click', () => {
            document.getElementById('astro-input').focus();
        });
        document.getElementById('btn-close-modal')?.addEventListener('click', () => this.closeModal());
        document.getElementById('btn-save-kundali')?.addEventListener('click', () => this.saveKundali());
        document.getElementById('btn-delete-kundali')?.addEventListener('click', () => this.deleteKundali());
        document.getElementById('btn-edit-kundali')?.addEventListener('click', () => this.openModal(true));
    },

    handleInitialRoute() {
        const params = new URLSearchParams(window.location.search);
        const kundaliId = params.get('kundali');
        if (kundaliId) {
            AstroUI.selectedId = kundaliId;
            AstroUI.render();
        }
    },

    openModal(editExisting = false) {
        this.isEditing = editExisting;
        this.modal.classList.remove('hidden');
        if (editExisting && AstroUI.selectedId) {
            const kundali = AstroStorage.load().find(item => item.id === AstroUI.selectedId);
            if (kundali) {
                this.nameInput.value = kundali.profile?.name || '';
                this.genderInput.value = kundali.profile?.gender || 'unspecified';
                this.dateInput.value = kundali.profile?.birth?.date || '';
                this.timeInput.value = kundali.profile?.birth?.time || '';
                this.placeInput.value = kundali.profile?.location?.place || '';
                this.latInput.value = kundali.profile?.location?.lat || '';
                this.lonInput.value = kundali.profile?.location?.lon || '';
                this.tzInput.value = kundali.profile?.timezone || '';
            }
        } else {
            this.nameInput.value = '';
            this.genderInput.value = 'unspecified';
            this.dateInput.value = '';
            this.timeInput.value = '';
            this.placeInput.value = '';
            this.latInput.value = '';
            this.lonInput.value = '';
            this.tzInput.value = '';
        }
    },

    closeModal() {
        this.isEditing = false;
        this.modal.classList.add('hidden');
    },

    saveKundali() {
        const profile = {
            name: this.nameInput.value.trim(),
            gender: this.genderInput.value,
            birth: {
                date: this.dateInput.value,
                time: this.timeInput.value
            },
            location: {
                place: this.placeInput.value.trim(),
                lat: this.latInput.value,
                lon: this.lonInput.value
            },
            timezone: this.tzInput.value.trim()
        };

        if (this.isEditing && AstroUI.selectedId) {
            AstroStorage.update(AstroUI.selectedId, { profile });
        } else {
            const kundali = AstroStorage.create(profile);
            AstroUI.selectedId = kundali.id;
        }

        this.closeModal();
        AstroUI.render();
        this.syncKundalis();
    },

    deleteKundali() {
        if (!AstroUI.selectedId) return;
        AstroStorage.remove(AstroUI.selectedId);
        AstroUI.selectedId = null;
        AstroUI.render();
        this.syncKundalis();
    },

    async syncKundalis() {
        try {
            await fetch('/astro/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    kundalis_state: AstroStorage.load()
                })
            });
        } catch (error) {
            console.error('[AstroApp] Sync failed', error);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    AstroApp.init();
});
