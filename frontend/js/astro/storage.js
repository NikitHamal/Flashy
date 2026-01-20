const AstroStorage = {
    key: 'flashy_astro_kundalis',

    load() {
        try {
            const raw = localStorage.getItem(this.key);
            return raw ? JSON.parse(raw) : [];
        } catch (error) {
            console.error('[AstroStorage] Failed to load', error);
            return [];
        }
    },

    save(kundalis) {
        localStorage.setItem(this.key, JSON.stringify(kundalis));
    },

    create(profile) {
        const kundalis = this.load();
        const now = new Date().toISOString();
        const kundali = {
            id: `kundali_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            profile: {
                name: profile.name || 'Unnamed',
                gender: profile.gender || 'unspecified',
                birth: profile.birth || {},
                location: profile.location || {},
                timezone: profile.timezone || '',
                notes: profile.notes || ''
            },
            chart: {
                lagna: {},
                rashi: {},
                navamsa: {},
                planets: {},
                houses: {},
                dashas: {},
                ashtakavarga: {},
                yogas: []
            },
            predictions: {},
            notes: '',
            createdAt: now,
            updatedAt: now
        };
        kundalis.unshift(kundali);
        this.save(kundalis);
        return kundali;
    },

    update(kundaliId, updates) {
        const kundalis = this.load();
        const target = kundalis.find(item => item.id === kundaliId);
        if (!target) return null;
        this.deepUpdate(target, updates);
        target.updatedAt = new Date().toISOString();
        this.save(kundalis);
        return target;
    },

    remove(kundaliId) {
        const kundalis = this.load().filter(item => item.id !== kundaliId);
        this.save(kundalis);
        return kundalis;
    },

    setAll(kundalis) {
        this.save(kundalis || []);
    },

    deepUpdate(target, updates) {
        Object.entries(updates || {}).forEach(([key, value]) => {
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                if (!target[key] || typeof target[key] !== 'object') {
                    target[key] = {};
                }
                this.deepUpdate(target[key], value);
            } else {
                target[key] = value;
            }
        });
    }
};
