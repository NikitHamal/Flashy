const AstroUI = {
    selectedId: null,

    init() {
        this.listEl = document.getElementById('kundali-list');
        this.searchEl = document.getElementById('kundali-search');
        this.emptyView = document.getElementById('astro-empty');
        this.detailView = document.getElementById('astro-detail');
        this.detailName = document.getElementById('detail-name');
        this.detailMeta = document.getElementById('detail-meta');

        this.birthDetails = document.getElementById('birth-details');
        this.chartSnapshot = document.getElementById('chart-snapshot');
        this.predictionSnapshot = document.getElementById('prediction-snapshot');
        this.planetsTable = document.getElementById('planets-table');
        this.housesTable = document.getElementById('houses-table');
        this.dashasTable = document.getElementById('dashas-table');
        this.notesInput = document.getElementById('kundali-notes');

        this.bindEvents();
        this.render();
    },

    bindEvents() {
        this.searchEl?.addEventListener('input', () => this.render());
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        this.notesInput?.addEventListener('input', () => this.handleNotesUpdate());
    },

    switchTab(tabId) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `tab-${tabId}`);
        });
    },

    render() {
        const kundalis = AstroStorage.load();
        const query = (this.searchEl?.value || '').toLowerCase();
        const filtered = kundalis.filter(k => k.profile?.name?.toLowerCase().includes(query));

        this.listEl.innerHTML = '';
        if (filtered.length === 0) {
            this.listEl.innerHTML = '<div class="empty-list">No kundalis found.</div>';
        } else {
            filtered.forEach(kundali => {
                const item = document.createElement('button');
                item.className = `kundali-card ${kundali.id === this.selectedId ? 'active' : ''}`;
                item.innerHTML = `
                    <div>
                        <strong>${kundali.profile?.name || 'Unnamed'}</strong>
                        <span>${kundali.profile?.gender || 'unspecified'}</span>
                    </div>
                    <p>${this.formatBirth(kundali)}</p>
                `;
                item.addEventListener('click', () => this.selectKundali(kundali.id));
                this.listEl.appendChild(item);
            });
        }

        if (!kundalis.length || !this.selectedId) {
            this.emptyView.classList.remove('hidden');
            this.detailView.classList.add('hidden');
        } else {
            this.emptyView.classList.add('hidden');
            this.detailView.classList.remove('hidden');
            this.renderDetail();
        }
    },

    selectKundali(kundaliId) {
        this.selectedId = kundaliId;
        history.replaceState({}, '', `?kundali=${kundaliId}`);
        this.render();
    },

    renderDetail() {
        const kundalis = AstroStorage.load();
        const kundali = kundalis.find(item => item.id === this.selectedId);
        if (!kundali) return;

        const profile = kundali.profile || {};
        this.detailName.textContent = profile.name || 'Unnamed Kundali';
        this.detailMeta.textContent = `${profile.gender || 'unspecified'} · ${this.formatBirth(kundali)}`;

        this.renderList(this.birthDetails, {
            'Birth Date': profile.birth?.date || '—',
            'Birth Time': profile.birth?.time || '—',
            'Birth Place': profile.location?.place || '—',
            'Latitude': profile.location?.lat || '—',
            'Longitude': profile.location?.lon || '—',
            'Timezone': profile.timezone || '—'
        });

        this.renderList(this.chartSnapshot, {
            'Lagna': kundali.chart?.lagna?.sign || '—',
            'Rashi': kundali.chart?.rashi?.sign || '—',
            'Navamsa': kundali.chart?.navamsa?.sign || '—',
            'Key Yogas': (kundali.chart?.yogas || []).slice(0, 3).join(', ') || '—'
        });

        this.renderList(this.predictionSnapshot, kundali.predictions || { "Summary": '—' });

        this.planetsTable.innerHTML = this.renderTable(kundali.chart?.planets || {}, 'Planet');
        this.housesTable.innerHTML = this.renderTable(kundali.chart?.houses || {}, 'House');
        this.dashasTable.innerHTML = this.renderTable(kundali.chart?.dashas || {}, 'Dasha');
        this.notesInput.value = kundali.notes || '';
    },

    renderList(container, data) {
        container.innerHTML = '';
        Object.entries(data || {}).forEach(([label, value]) => {
            const row = document.createElement('div');
            row.className = 'detail-row';
            row.innerHTML = `<span>${label}</span><strong>${value || '—'}</strong>`;
            container.appendChild(row);
        });
    },

    renderTable(data, labelHeader) {
        const entries = Object.entries(data || {});
        if (entries.length === 0) {
            return '<div class="empty-table">No data yet.</div>';
        }
        return `
            <div class="table">
                <div class="table-row table-head">
                    <span>${labelHeader}</span>
                    <span>Details</span>
                </div>
                ${entries
                    .map(([key, value]) => `
                        <div class="table-row">
                            <span>${key}</span>
                            <span>${typeof value === 'object' ? JSON.stringify(value) : value}</span>
                        </div>
                    `)
                    .join('')}
            </div>
        `;
    },

    handleNotesUpdate() {
        if (!this.selectedId) return;
        const updated = AstroStorage.update(this.selectedId, { notes: this.notesInput.value });
        if (updated) {
            AstroApp.syncKundalis();
        }
    },

    formatBirth(kundali) {
        const birth = kundali.profile?.birth || {};
        const date = birth.date || '';
        const time = birth.time || '';
        return [date, time].filter(Boolean).join(' · ') || 'Birth data missing';
    }
};
