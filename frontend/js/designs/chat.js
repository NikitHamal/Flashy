(function () {
    const state = window.DesignState;

    const chatHistory = () => document.getElementById('design-chat-history');

    function addBubble(content, role = 'ai') {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;
        bubble.innerHTML = content;
        chatHistory().appendChild(bubble);
        chatHistory().scrollTop = chatHistory().scrollHeight;
        return bubble;
    }

    function appendToolPill(target, label, payload) {
        const pill = document.createElement('div');
        pill.className = 'tool-pill';
        pill.innerHTML = `<span class="material-symbols-outlined">build</span><span>${label}</span>`;
        if (payload) {
            pill.title = payload;
        }
        target.appendChild(pill);
    }

    function extractDesignSpec(text) {
        if (!text) return null;
        const codeBlockMatch = text.match(/```json\s*([\s\S]*?)```/i);
        if (codeBlockMatch) {
            try {
                const parsed = JSON.parse(codeBlockMatch[1]);
                if (parsed && parsed.flashy_design) return parsed.flashy_design;
            } catch (_) {
                return null;
            }
        }
        const inlineMatch = text.match(/\{[\s\S]*"flashy_design"[\s\S]*\}/i);
        if (inlineMatch) {
            try {
                const parsed = JSON.parse(inlineMatch[0]);
                if (parsed && parsed.flashy_design) return parsed.flashy_design;
            } catch (_) {
                return null;
            }
        }
        return null;
    }

    async function sendMessage(text, files = []) {
        const finalText = `${text}\n\nReturn a JSON code block with key \"flashy_design\" if you want to update the canvas. Use elements with types rect, circle, text, line.`;
        addBubble(text, 'user');

        const aiBubble = addBubble('<span>Thinking...</span>', 'ai');
        let aiText = '';

        try {
            await API.sendMessage(finalText, state.sessionId, null, files, (chunk) => {
                if (chunk.text) {
                    aiText += chunk.text;
                    aiBubble.innerHTML = aiText.replace(/\n/g, '<br>');
                }
                if (chunk.tool_call) {
                    appendToolPill(aiBubble, `Tool: ${chunk.tool_call.name}`, JSON.stringify(chunk.tool_call.args || {}));
                }
                if (chunk.tool_result) {
                    appendToolPill(aiBubble, 'Tool result', chunk.tool_result);
                }
                if (chunk.is_final) {
                    const spec = extractDesignSpec(aiText);
                    if (spec) {
                        window.DesignCanvas.applyDesignSpec(spec);
                    }
                }
            });
        } catch (e) {
            aiBubble.innerHTML = `Error: ${e.message}`;
        }
    }

    async function sendCanvasToAgent() {
        const blob = await window.DesignExport.exportCanvasBlob(2);
        if (!blob) return;
        const file = new File([blob], `flashy-design-${Date.now()}.png`, { type: 'image/png' });
        await sendMessage('Here is the current canvas export. Review and suggest improvements or apply layout updates.', [file]);
    }

    window.DesignChat = {
        sendMessage,
        sendCanvasToAgent
    };
})();
