// File Explorer & Session Management
Object.assign(UI, {
    renderExplorer(data, onFileSelect) {
        const treeContainer = document.getElementById('explorer-tree');
        if (!treeContainer) return;
        treeContainer.innerHTML = '';
        if (data.error) {
            treeContainer.innerHTML = `<div class="explorer-error">${this.escapeHtml(data.error)}</div>`;
            return;
        }
        const getFileIcon = (fileName) => {
            const ext = fileName.split('.').pop().toLowerCase();
            const MAP = {
                'js': 'javascript', 'ts': 'typescript', 'py': 'terminal',
                'html': 'html', 'css': 'css', 'json': 'settings',
                'md': 'description', 'txt': 'description', 'png': 'image',
                'jpg': 'image', 'svg': 'image', 'pdf': 'picture_as_pdf'
            };
            return MAP[ext] || 'description';
        };
        const renderNode = (node) => {
            const container = document.createElement('div');
            container.className = 'tree-node';
            const item = document.createElement('div');
            item.className = `tree-item ${node.type}`;
            const icon = node.type === 'directory' ? 'folder' : getFileIcon(node.name);
            const arrow = node.type === 'directory' ? '<span class="material-symbols-outlined directory-icon">expand_more</span>' : '';
            item.innerHTML = `${arrow}<span class="material-symbols-outlined icon">${icon}</span><span class="name">${node.name}</span>`;
            container.appendChild(item);
            if (node.type === 'directory' && node.children) {
                const childrenContainer = document.createElement('div');
                childrenContainer.className = 'tree-item-children';
                node.children.forEach(child => {
                    childrenContainer.appendChild(renderNode(child));
                });
                container.appendChild(childrenContainer);
                item.onclick = (e) => {
                    e.stopPropagation();
                    container.classList.toggle('collapsed');
                };
            } else if (node.type === 'file') {
                item.onclick = (e) => {
                    e.stopPropagation();
                    if (onFileSelect) onFileSelect(node.path);
                };
            }
            return container;
        };
        if (data.type === 'directory' && data.children) {
            data.children.forEach(child => {
                treeContainer.appendChild(renderNode(child));
            });
        } else {
            treeContainer.appendChild(renderNode(data));
        }
    },

    renderSidebarSessions(workspaces, allSessions, currentSessionId, onSelect, onDelete) {
        const list = document.getElementById('sidebar-sessions-list');
        if (!list) return;
        list.innerHTML = '';
        const grouped = {};
        allSessions.forEach(s => {
            if (!grouped[s.workspace_id]) grouped[s.workspace_id] = [];
            grouped[s.workspace_id].push(s);
        });
        Object.entries(workspaces).forEach(([wsId, ws]) => {
            const sessions = grouped[wsId] || [];
            if (sessions.length === 0) return;
            const groupDiv = document.createElement('div');
            groupDiv.innerHTML = `<div class="sidebar-group-title"><span class="material-symbols-outlined icon">folder</span><span>${ws.name}</span></div>`;
            sessions.forEach(s => {
                const item = document.createElement('div');
                item.className = `nav-item sidebar-session-item ${s.id === currentSessionId ? 'active' : ''}`;
                item.innerHTML = `
                    <span class="name">${s.title || 'Untitled'}</span>
                    <div class="nav-actions"><button class="btn-item-action delete-session" title="Delete session"><span class="material-symbols-outlined">delete</span></button></div>
                `;
                item.onclick = (e) => {
                    if (e.target.closest('.delete-session')) {
                        e.stopPropagation();
                        onDelete(s.id);
                        return;
                    }
                    onSelect(s);
                };
                groupDiv.appendChild(item);
            });
            list.appendChild(groupDiv);
        });
    },

    renderSessionDropdown(currentWorkspaceId, sessions, currentSessionId, onSelect, onNew) {
        const menu = document.getElementById('session-dropdown-menu');
        if (!menu) return;
        menu.innerHTML = '';
        const newSessItem = document.createElement('div');
        newSessItem.className = 'dropdown-item';
        newSessItem.innerHTML = `<div class="item-info"><div class="item-title">New Session</div></div><span class="material-symbols-outlined">add</span>`;
        newSessItem.onclick = () => { onNew(currentWorkspaceId); menu.classList.add('hidden'); };
        menu.appendChild(newSessItem);
        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `dropdown-item ${s.id === currentSessionId ? 'active' : ''}`;
            item.innerHTML = `<div class="item-info"><div class="item-title">${s.title || 'Untitled'}</div><div class="item-meta">${new Date(s.created_at * 1000).toLocaleString()}</div></div>`;
            item.onclick = () => { onSelect(s); menu.classList.add('hidden'); };
            menu.appendChild(item);
        });
    },

    renderPlan(content) {
        const container = document.getElementById('plan-content');
        if (!container) return;
        if (!content) {
            container.innerHTML = '<div class="plan-empty">No active plan found (plan.md)</div>';
            return;
        }
        container.innerHTML = marked.parse(content);
    }
});
