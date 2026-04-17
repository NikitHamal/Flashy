        const API_BASE = window.location.protocol + '//' + window.location.host;
        
        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/qwencode`;
        
        let socket = null;
        let isGenerating = false;
        
        const chatHistory = document.getElementById('chat-history');
        const messageInput = document.getElementById('message-input');
        const btnSend = document.getElementById('btn-send');
        const btnPickFolder = document.getElementById('btn-pick-folder');
        const workspaceInput = document.getElementById('workspace-input');
        
        const authSelect = document.getElementById('auth-type-select');
        const modelSelect = document.getElementById('model-select');
        
        const QWEN_MODELS = [
            { value: 'qwen3.6-plus', label: 'qwen3.6-plus' },
            { value: 'qwen3.5-plus', label: 'qwen3.5-plus' },
            { value: 'qwen3-coder-plus', label: 'qwen3-coder-plus' }
        ];
        
        const DEEPINFRA_MODELS = [
            { value: 'zai-org/GLM-5.1', label: 'GLM 5.1' },
            { value: 'meta-llama/Meta-Llama-3-8B-Instruct', label: 'Llama 3 8B' },
            { value: 'Qwen/Qwen2.5-Coder-32B-Instruct', label: 'Qwen 2.5 Coder 32B' }
        ];
        
        function updateModels() {
            const isDeepInfra = authSelect.value === 'deepinfra-free';
            const models = isDeepInfra ? DEEPINFRA_MODELS : QWEN_MODELS;
            modelSelect.innerHTML = models.map(m => `<option value="${m.value}">${m.label}</option>`).join('');
        }
        
        authSelect.addEventListener('change', updateModels);
        
        btnPickFolder.addEventListener('click', async () => {
            try {
                const response = await fetch(`${API_BASE}/path/pick`, { method: 'POST' });
                if (response.ok) {
                    const data = await response.json();
                    if (data.path) {
                        workspaceInput.value = data.path;
                    }
                }
            } catch (e) {
                console.error('Failed to pick folder:', e);
                alert('Could not open folder picker. Please enter path manually.');
            }
        });
        
        function connect() {
            socket = new WebSocket(wsUrl);
            
            socket.onopen = () => {
                console.log('Connected to Qwen Code Bridge');
            };
            
            socket.onclose = () => {
                console.log('Disconnected, reconnecting...');
                setTimeout(connect, 3000);
            };
            
            socket.onerror = (err) => {
                console.error('WebSocket error:', err);
            };
            
            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };
        }
        
        let currentAssistantBubble = null;
        let currentThoughtBubble = null;
        let typingIndicator = null;
        
        function showTypingIndicator() {
            if (!typingIndicator) {
                typingIndicator = document.createElement('div');
                typingIndicator.className = 'typing-indicator';
                typingIndicator.innerHTML = '<span></span><span></span><span></span';
                chatHistory.appendChild(typingIndicator);
                scrollToBottom();
            }
        }
        
        function hideTypingIndicator() {
            if (typingIndicator) {
                typingIndicator.remove();
                typingIndicator = null;
            }
        }
        
        function handleMessage(data) {
            hideTypingIndicator();
            
            if (data.type === 'text') {
                if (!currentAssistantBubble) {
                    currentAssistantBubble = document.createElement('div');
                    currentAssistantBubble.className = 'msg-bubble msg-assistant';
                    chatHistory.appendChild(currentAssistantBubble);
                }
                
                if (data.content) {
                    currentAssistantBubble.textContent = (currentAssistantBubble.textContent || '') + data.content;
                }
                
                if (data.is_final) {
                    currentAssistantBubble = null;
                    currentThoughtBubble = null;
                    isGenerating = false;
                    updateSendButton(false);
                }
                scrollToBottom();
                
            } else if (data.type === 'thought') {
                if (!currentThoughtBubble) {
                    currentThoughtBubble = document.createElement('div');
                    currentThoughtBubble.className = 'thought-bubble';
                    const lastMsg = chatHistory.lastElementChild;
                    if (lastMsg && lastMsg !== currentThoughtBubble) {
                        chatHistory.insertBefore(currentThoughtBubble, lastMsg.nextSibling);
                    } else {
                        chatHistory.appendChild(currentThoughtBubble);
                    }
                }
                currentThoughtBubble.textContent = (currentThoughtBubble.textContent || '') + data.content;
                scrollToBottom();
                
            } else if (data.type === 'tool_call') {
                const toolBubble = document.createElement('div');
                toolBubble.className = 'tool-call-bubble';
                toolBubble.innerHTML = `<span class="tool-name">${data.name}</span>\n${JSON.stringify(data.args, null, 2)}`;
                chatHistory.appendChild(toolBubble);
                scrollToBottom();
                
            } else if (data.type === 'error') {
                const bubble = document.createElement('div');
                bubble.className = 'msg-bubble msg-assistant msg-error';
                bubble.textContent = `Error: ${data.message}`;
                chatHistory.appendChild(bubble);
                isGenerating = false;
                updateSendButton(false);
                scrollToBottom();
                
            } else if (data.type === 'stream_end') {
                isGenerating = false;
                currentAssistantBubble = null;
                currentThoughtBubble = null;
                updateSendButton(false);
            }
        }
        
        function updateSendButton(stopMode) {
            if (stopMode) {
                btnSend.classList.add('stop-mode');
                btnSend.innerHTML = '<span class="material-symbols-outlined">stop</span>';
                btnSend.disabled = false;
            } else {
                btnSend.classList.remove('stop-mode');
                btnSend.innerHTML = '<span class="material-symbols-outlined">send</span>';
                btnSend.disabled = false;
            }
        }
        
        function scrollToBottom() {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        
        function sendMessage() {
            if (isGenerating || !socket || socket.readyState !== WebSocket.OPEN) return;
            
            const prompt = messageInput.value.trim();
            if (!prompt) return;
            
            const userBubble = document.createElement('div');
            userBubble.className = 'msg-bubble msg-user';
            userBubble.textContent = prompt;
            chatHistory.appendChild(userBubble);
            scrollToBottom();
            
            messageInput.value = '';
            
            isGenerating = true;
            updateSendButton(true);
            showTypingIndicator();
            
            const payload = {
                prompt: prompt,
                auth_type: authSelect.value,
                model: modelSelect.value,
                workspace_path: workspaceInput.value || ''
            };
            
            socket.send(JSON.stringify(payload));
            currentAssistantBubble = null;
            currentThoughtBubble = null;
        }
        
        btnSend.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });
        
        connect();
