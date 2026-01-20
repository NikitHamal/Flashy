import { calculateKundali } from "./vedic_calculator.js";
import { loadKundalis, saveKundalis, loadActiveId, saveActiveId, upsertKundali } from "./storage.js";
import { renderKundaliList, renderDetail } from "./ui.js";
import { AstroChat } from "./chat.js";

const state = {
    kundalis: [],
    activeId: null
};

function getActiveKundali() {
    return state.kundalis.find((k) => k.id === state.activeId);
}

function updateUI() {
    renderKundaliList(state.kundalis, state.activeId);
    renderDetail(getActiveKundali());
}

function saveState() {
    saveKundalis(state.kundalis);
    saveActiveId(state.activeId);
}

function computeChart(profile) {
    const chart = calculateKundali(profile);
    return { ...profile, chart: { ...chart, summary: chart.summary } };
}

function setActive(id) {
    state.activeId = id;
    saveState();
    updateUI();
}

function openModal(kundali = null) {
    const modal = document.getElementById("kundali-modal");
    modal.classList.remove("hidden");
    document.getElementById("kundali-modal-title").textContent = kundali ? "Edit Kundali" : "Create Kundali";
    document.getElementById("kundali-name").value = kundali?.name || "";
    document.getElementById("kundali-gender").value = kundali?.gender || "";
    document.getElementById("kundali-date").value = kundali?.birthDate || "";
    document.getElementById("kundali-time").value = kundali?.birthTime || "";
    document.getElementById("kundali-place").value = kundali?.birthPlace || "";
    document.getElementById("kundali-lat").value = kundali?.latitude || "";
    document.getElementById("kundali-lng").value = kundali?.longitude || "";
    document.getElementById("kundali-tz").value = kundali?.timezone || "";
    modal.dataset.editId = kundali?.id || "";
}

function closeModal() {
    const modal = document.getElementById("kundali-modal");
    modal.classList.add("hidden");
    modal.dataset.editId = "";
}

function getFormData() {
    return {
        name: document.getElementById("kundali-name").value.trim(),
        gender: document.getElementById("kundali-gender").value,
        birthDate: document.getElementById("kundali-date").value,
        birthTime: document.getElementById("kundali-time").value,
        birthPlace: document.getElementById("kundali-place").value.trim(),
        latitude: Number(document.getElementById("kundali-lat").value),
        longitude: Number(document.getElementById("kundali-lng").value),
        timezone: Number(document.getElementById("kundali-tz").value)
    };
}

function validateProfile(profile) {
    const required = ["name", "gender", "birthDate", "birthTime", "birthPlace", "latitude", "longitude", "timezone"];
    const missing = required.filter((key) => !profile[key] && profile[key] !== 0);
    return missing;
}

function addDemoProfile() {
    const demo = {
        id: "kundali_demo",
        name: "Demo Native",
        gender: "Male",
        birthDate: "1996-08-05",
        birthTime: "14:35",
        birthPlace: "Mumbai, India",
        latitude: 19.076,
        longitude: 72.8777,
        timezone: 5.5
    };
    const computed = computeChart(demo);
    state.kundalis = upsertKundali(state.kundalis, computed);
    state.activeId = computed.id;
    saveState();
    updateUI();
}

function setupEventHandlers() {
    document.getElementById("btn-new-kundali").addEventListener("click", () => openModal());
    document.getElementById("btn-empty-create").addEventListener("click", () => openModal());
    document.getElementById("btn-main-create").addEventListener("click", () => openModal());
    document.getElementById("btn-main-demo").addEventListener("click", () => addDemoProfile());
    document.getElementById("btn-close-modal").addEventListener("click", closeModal);
    document.getElementById("btn-cancel-kundali").addEventListener("click", closeModal);
    document.getElementById("btn-save-kundali").addEventListener("click", () => {
        const profile = getFormData();
        const missing = validateProfile(profile);
        if (missing.length) {
            alert(`Missing: ${missing.join(", ")}`);
            return;
        }
        const modal = document.getElementById("kundali-modal");
        const editId = modal.dataset.editId;
        const record = editId ? { ...profile, id: editId } : { ...profile, id: `kundali_${Date.now()}` };
        const computed = computeChart(record);
        state.kundalis = upsertKundali(state.kundalis, computed);
        state.activeId = computed.id;
        saveState();
        updateUI();
        closeModal();
    });

    document.getElementById("kundali-list").addEventListener("click", (event) => {
        const item = event.target.closest(".kundali-item");
        if (item) setActive(item.dataset.id);
    });

    document.getElementById("btn-edit-kundali").addEventListener("click", () => {
        const active = getActiveKundali();
        if (active) openModal(active);
    });

    document.getElementById("btn-delete-kundali").addEventListener("click", () => {
        const active = getActiveKundali();
        if (!active) return;
        if (!confirm("Delete this kundali?")) return;
        state.kundalis = state.kundalis.filter((k) => k.id !== active.id);
        state.activeId = state.kundalis[0]?.id || null;
        saveState();
        updateUI();
    });
}

function hydrateFromStorage() {
    state.kundalis = loadKundalis();
    state.activeId = loadActiveId();
    if (!state.kundalis.length) {
        state.activeId = null;
    } else if (!state.activeId || !state.kundalis.find((k) => k.id === state.activeId)) {
        state.activeId = state.kundalis[0].id;
    }
    updateUI();
}

function handleChatUpdates(update) {
    if (!update) return;
    if (Array.isArray(update.kundalis)) {
        state.kundalis = update.kundalis.map((k) => k.chart ? k : computeChart(k));
    }
    if (update.active_id) state.activeId = update.active_id;
    saveState();
    updateUI();
}

function initChat() {
    const chat = new AstroChat({
        sessionId: `astro_${Date.now()}`,
        getContext: () => ({ kundalis: state.kundalis, activeId: state.activeId }),
        onUpdate: handleChatUpdates
    });
    chat.init();
}

document.addEventListener("DOMContentLoaded", () => {
    hydrateFromStorage();
    setupEventHandlers();
    initChat();
});
