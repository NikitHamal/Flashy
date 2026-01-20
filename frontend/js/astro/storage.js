const STORAGE_KEY = "flashy_astro_kundalis";
const ACTIVE_KEY = "flashy_astro_active";

export function loadKundalis() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    try {
        return JSON.parse(raw);
    } catch {
        return [];
    }
}

export function saveKundalis(kundalis) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(kundalis));
}

export function loadActiveId() {
    return localStorage.getItem(ACTIVE_KEY);
}

export function saveActiveId(id) {
    if (id) {
        localStorage.setItem(ACTIVE_KEY, id);
    } else {
        localStorage.removeItem(ACTIVE_KEY);
    }
}

export function upsertKundali(kundalis, profile) {
    const index = kundalis.findIndex((k) => k.id === profile.id);
    if (index === -1) {
        kundalis.push(profile);
    } else {
        kundalis[index] = profile;
    }
    return kundalis;
}
