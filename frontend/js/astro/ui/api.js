/**
 * ============================================================================
 * Astro API Module
 * ============================================================================
 *
 * Handles all communication with the Flashy Astro backend service.
 * Uses NDJSON streaming for real-time AI responses.
 *
 * @module astro/ui/api
 */

class AstroAPI {
    constructor() {
        this.baseUrl = '/astro';
        this.sessionId = this._generateSessionId();
        this.activeAbortController = null;
    }

    /**
     * Generate unique session ID for this consultation
     */
    _generateSessionId() {
        return 'astro_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Get current session ID
     */
    getSessionId() {
        return this.sessionId;
    }

    /**
     * Reset session (new consultation context)
     */
    resetSession() {
        this.sessionId = this._generateSessionId();
        return this.sessionId;
    }

    /**
     * Stream consultation response from the Jyotishi AI
     * Uses NDJSON streaming for real-time updates
     *
     * @param {string} message - User's question/message
     * @param {Array} kundalis - Array of stored kundalis from localStorage
     * @param {string} activeKundaliId - Currently active kundali ID
     * @param {Object} callbacks - Event handlers for streaming updates
     * @returns {Promise<void>}
     */
    async streamConsultation(message, kundalis = [], activeKundaliId = null, callbacks = {}) {
        const {
            onThought = () => { },
            onText = () => { },
            onToolCall = () => { },
            onToolResult = () => { },
            onKundaliUpdate = () => { },
            onActiveKundaliUpdate = () => { },
            onError = () => { },
            onComplete = () => { }
        } = callbacks;

        // Cancel any existing request
        this.abort();
        this.activeAbortController = new AbortController();

        try {
            const response = await fetch(`${this.baseUrl}/consult`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/x-ndjson'
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message,
                    kundalis: kundalis,
                    active_kundali_id: activeKundaliId
                }),
                signal: this.activeAbortController.signal
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP error ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (!line.trim()) continue;

                    try {
                        const data = JSON.parse(line);

                        // Handle different event types
                        if (data.thought) {
                            onThought(data.thought);
                        }

                        if (data.text) {
                            onText(data.text);
                        }

                        if (data.tool_call) {
                            onToolCall(data.tool_call);
                        }

                        if (data.tool_result) {
                            onToolResult(data.tool_result);
                        }

                        if (data.kundalis) {
                            onKundaliUpdate(data.kundalis);
                        }

                        if (data.active_kundali) {
                            onActiveKundaliUpdate(data.active_kundali);
                        }

                        if (data.error) {
                            onError(data.error);
                        }

                        if (data.is_final) {
                            onComplete(data);
                        }
                    } catch (parseError) {
                        console.warn('[AstroAPI] Failed to parse line:', line, parseError);
                    }
                }
            }

            // Process any remaining buffer
            if (buffer.trim()) {
                try {
                    const data = JSON.parse(buffer);
                    if (data.is_final) {
                        onComplete(data);
                    }
                } catch (e) {
                    // Ignore incomplete JSON
                }
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('[AstroAPI] Request aborted');
                return;
            }
            onError(error.message);
            throw error;
        } finally {
            this.activeAbortController = null;
        }
    }

    /**
     * Abort the current streaming request
     */
    abort() {
        if (this.activeAbortController) {
            this.activeAbortController.abort();
            this.activeAbortController = null;
        }
    }

    /**
     * Interrupt the current AI session on the server
     */
    async interrupt() {
        this.abort();

        try {
            await fetch(`${this.baseUrl}/interrupt`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
        } catch (error) {
            console.error('[AstroAPI] Failed to interrupt session:', error);
        }
    }

    /**
     * Create a new kundali directly (without AI)
     * Used by the create kundali form
     *
     * @param {Object} birthDetails - Birth details object
     * @returns {Promise<Object>} Created kundali data
     */
    async createKundali(birthDetails) {
        const response = await fetch(`${this.baseUrl}/kundali`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                ...birthDetails
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create kundali');
        }

        return response.json();
    }

    /**
     * Update chart data for a kundali (after frontend calculation)
     *
     * @param {string} kundaliId - Kundali ID
     * @param {Object} chartData - Calculated chart data
     * @returns {Promise<Object>}
     */
    async updateChartData(kundaliId, chartData) {
        const response = await fetch(`${this.baseUrl}/kundali/chart-data`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                kundali_id: kundaliId,
                chart_data: chartData
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update chart data');
        }

        return response.json();
    }

    /**
     * Delete a kundali
     *
     * @param {string} kundaliId - Kundali ID to delete
     * @returns {Promise<Object>}
     */
    async deleteKundali(kundaliId) {
        const response = await fetch(`${this.baseUrl}/kundali/${this.sessionId}/${kundaliId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete kundali');
        }

        return response.json();
    }

    /**
     * Set active kundali for the session
     *
     * @param {string} kundaliId - Kundali ID to set as active
     * @returns {Promise<Object>}
     */
    async setActiveKundali(kundaliId) {
        const response = await fetch(`${this.baseUrl}/active-kundali`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                kundali_id: kundaliId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to set active kundali');
        }

        return response.json();
    }

    /**
     * Sync kundalis from localStorage to server session
     * Called on page load
     *
     * @param {Array} kundalis - Array of kundalis from localStorage
     * @returns {Promise<Object>}
     */
    async syncKundalis(kundalis) {
        const response = await fetch(`${this.baseUrl}/sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                kundalis: kundalis
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to sync kundalis');
        }

        return response.json();
    }

    /**
     * Get session state
     *
     * @returns {Promise<Object>}
     */
    async getSessionState() {
        const response = await fetch(`${this.baseUrl}/session/${this.sessionId}`);

        if (!response.ok) {
            return { session_id: this.sessionId, active_kundali: null, kundali_count: 0 };
        }

        return response.json();
    }

    /**
     * Set ayanamsa system
     *
     * @param {string} system - Ayanamsa system name
     * @returns {Promise<Object>}
     */
    async setAyanamsa(system) {
        const response = await fetch(`${this.baseUrl}/ayanamsa`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                system: system
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to set ayanamsa');
        }

        return response.json();
    }

    /**
     * Get planet signification info
     *
     * @param {string} planet - Planet name
     * @returns {Promise<Object>}
     */
    async getPlanetInfo(planet) {
        const response = await fetch(`${this.baseUrl}/reference/planet/${planet}`);

        if (!response.ok) {
            return { planet, info: null };
        }

        return response.json();
    }

    /**
     * Reset the current session
     *
     * @returns {Promise<Object>}
     */
    async resetServerSession() {
        const response = await fetch(`${this.baseUrl}/session/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId
            })
        });

        if (!response.ok) {
            console.warn('[AstroAPI] Failed to reset server session');
        }

        return response.json().catch(() => ({ success: true }));
    }
}

// Export singleton instance
export default new AstroAPI();
