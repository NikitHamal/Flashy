/**
 * Astro API Module
 * 
 * Handles all API communication with the Flashy Astro backend.
 */

const AstroAPI = {
    BASE_URL: '/astro',
    
    /**
     * Send a chat message to the Astro AI
     * Returns a reader for streaming response
     */
    async chat(message, sessionId, profiles = []) {
        const response = await fetch(`${this.BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                profiles
            })
        });
        
        if (!response.ok) {
            throw new Error(`Chat request failed: ${response.statusText}`);
        }
        
        return response.body.getReader();
    },
    
    /**
     * Create a new kundali
     */
    async createKundali(data) {
        const response = await fetch(`${this.BASE_URL}/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: AstroStorage.getSessionId(),
                name: data.name,
                birth_date: data.birthDate,
                birth_time: data.birthTime,
                latitude: data.latitude,
                longitude: data.longitude,
                place_name: data.placeName || '',
                timezone: data.timezone || 'UTC',
                gender: data.gender || 'other'
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create kundali');
        }
        
        return response.json();
    },
    
    /**
     * Delete a kundali
     */
    async deleteKundali(profileId) {
        const sessionId = AstroStorage.getSessionId();
        const response = await fetch(`${this.BASE_URL}/kundali/${sessionId}/${profileId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete kundali');
        }
        
        return response.json();
    },
    
    /**
     * Get chart data for a profile
     */
    async getChart(profileId) {
        const sessionId = AstroStorage.getSessionId();
        const response = await fetch(`${this.BASE_URL}/chart/${sessionId}/${profileId}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get chart');
        }
        
        return response.json();
    },
    
    /**
     * Get quick analysis for a profile
     */
    async getAnalysis(profileId) {
        const sessionId = AstroStorage.getSessionId();
        const response = await fetch(`${this.BASE_URL}/analysis/${sessionId}/${profileId}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get analysis');
        }
        
        return response.json();
    },
    
    /**
     * Sync profiles with backend
     */
    async syncProfiles(profiles) {
        const response = await fetch(`${this.BASE_URL}/profiles/sync`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: AstroStorage.getSessionId(),
                profiles
            })
        });
        
        if (!response.ok) {
            console.warn('Failed to sync profiles');
        }
        
        return response.json();
    },
    
    /**
     * Interrupt the current session
     */
    async interrupt() {
        const sessionId = AstroStorage.getSessionId();
        const response = await fetch(`${this.BASE_URL}/interrupt/${sessionId}`, {
            method: 'POST'
        });
        
        return response.ok;
    },
    
    /**
     * Parse NDJSON stream
     */
    async *parseStream(reader) {
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.trim()) {
                    try {
                        yield JSON.parse(line);
                    } catch (e) {
                        console.warn('Failed to parse chunk:', line);
                    }
                }
            }
        }
        
        // Process remaining buffer
        if (buffer.trim()) {
            try {
                yield JSON.parse(buffer);
            } catch (e) {
                console.warn('Failed to parse final chunk:', buffer);
            }
        }
    },
    
    /**
     * Geocode a place name to coordinates
     * Using Nominatim OpenStreetMap API
     */
    async geocode(placeName) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?` +
                `format=json&q=${encodeURIComponent(placeName)}&limit=5`,
                {
                    headers: {
                        'User-Agent': 'FlashyAstro/1.0'
                    }
                }
            );
            
            if (!response.ok) return [];
            
            const results = await response.json();
            return results.map(r => ({
                name: r.display_name,
                lat: parseFloat(r.lat),
                lng: parseFloat(r.lon)
            }));
        } catch (e) {
            console.error('Geocoding error:', e);
            return [];
        }
    }
};
