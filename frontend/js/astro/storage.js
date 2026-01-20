/**
 * Astro Storage Module
 * 
 * Handles localStorage persistence for kundali profiles
 * and synchronization with the backend.
 */

const AstroStorage = {
    STORAGE_KEY: 'flashy_astro_kundalis',
    SESSION_KEY: 'flashy_astro_session',
    
    /**
     * Initialize storage and generate session ID if needed
     */
    init() {
        if (!this.getSessionId()) {
            const sessionId = `astro_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            localStorage.setItem(this.SESSION_KEY, sessionId);
        }
        
        // Initialize profiles array if not exists
        if (!localStorage.getItem(this.STORAGE_KEY)) {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify([]));
        }
    },
    
    /**
     * Get current session ID
     */
    getSessionId() {
        return localStorage.getItem(this.SESSION_KEY);
    },
    
    /**
     * Get all stored profiles
     */
    getProfiles() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('Error reading profiles:', e);
            return [];
        }
    },
    
    /**
     * Save profiles to localStorage
     */
    saveProfiles(profiles) {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(profiles));
            return true;
        } catch (e) {
            console.error('Error saving profiles:', e);
            return false;
        }
    },
    
    /**
     * Add a new profile
     */
    addProfile(profile) {
        const profiles = this.getProfiles();
        profiles.push(profile);
        return this.saveProfiles(profiles);
    },
    
    /**
     * Get a profile by ID
     */
    getProfile(profileId) {
        const profiles = this.getProfiles();
        return profiles.find(p => p.id === profileId) || null;
    },
    
    /**
     * Update a profile
     */
    updateProfile(profileId, updates) {
        const profiles = this.getProfiles();
        const index = profiles.findIndex(p => p.id === profileId);
        
        if (index === -1) return false;
        
        profiles[index] = { ...profiles[index], ...updates, updated_at: new Date().toISOString() };
        return this.saveProfiles(profiles);
    },
    
    /**
     * Delete a profile
     */
    deleteProfile(profileId) {
        const profiles = this.getProfiles();
        const filtered = profiles.filter(p => p.id !== profileId);
        
        if (filtered.length === profiles.length) return false;
        
        return this.saveProfiles(filtered);
    },
    
    /**
     * Sync profiles from backend response
     */
    syncFromBackend(backendProfiles) {
        if (!Array.isArray(backendProfiles)) return;
        
        // Merge with existing - backend takes priority
        const existing = this.getProfiles();
        const existingIds = new Set(existing.map(p => p.id));
        const newProfiles = [];
        
        for (const bp of backendProfiles) {
            if (existingIds.has(bp.id)) {
                // Update existing
                const idx = existing.findIndex(p => p.id === bp.id);
                existing[idx] = bp;
            } else {
                // Add new
                newProfiles.push(bp);
            }
        }
        
        this.saveProfiles([...existing, ...newProfiles]);
    },
    
    /**
     * Get currently selected profile ID
     */
    getSelectedProfileId() {
        return localStorage.getItem('flashy_astro_selected');
    },
    
    /**
     * Set currently selected profile ID
     */
    setSelectedProfileId(profileId) {
        if (profileId) {
            localStorage.setItem('flashy_astro_selected', profileId);
        } else {
            localStorage.removeItem('flashy_astro_selected');
        }
    },
    
    /**
     * Store chat history
     */
    getChatHistory() {
        try {
            const data = localStorage.getItem('flashy_astro_chat');
            return data ? JSON.parse(data) : [];
        } catch (e) {
            return [];
        }
    },
    
    /**
     * Add message to chat history
     */
    addChatMessage(message) {
        const history = this.getChatHistory();
        history.push({
            ...message,
            timestamp: new Date().toISOString()
        });
        
        // Keep last 100 messages
        const trimmed = history.slice(-100);
        localStorage.setItem('flashy_astro_chat', JSON.stringify(trimmed));
    },
    
    /**
     * Clear chat history
     */
    clearChatHistory() {
        localStorage.removeItem('flashy_astro_chat');
    }
};

// Initialize on load
AstroStorage.init();
