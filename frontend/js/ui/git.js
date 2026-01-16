// Git Sidebar Logic
Object.assign(UI, {
    renderGit(data, onBranchClick) {
        const container = document.getElementById('git-repo-status');
        const branchesList = document.getElementById('git-branches-list');
        const logList = document.getElementById('git-log-list');

        if (!data.is_repo) {
            container.innerHTML = '<div class="git-empty">No git repository detected.</div>';
            branchesList.innerHTML = '';
            logList.innerHTML = '';
            return;
        }

        // Staging Area
        container.innerHTML = ''; 
        
        const stagedSection = document.createElement('div');
        stagedSection.className = 'git-section';
        stagedSection.innerHTML = '<div class="git-section-header"><span>Staged Changes</span></div>';
        const stagedList = document.createElement('div');
        stagedList.className = 'git-file-list';
        stagedSection.appendChild(stagedList);
        
        const changesSection = document.createElement('div');
        changesSection.className = 'git-section';
        changesSection.innerHTML = '<div class="git-section-header"><span>Changes</span></div>';
        const changesList = document.createElement('div');
        changesList.className = 'git-file-list';
        changesSection.appendChild(changesList);

        const createFileItem = (file, isStaged) => {
            const item = document.createElement('div');
            item.className = 'git-file-item';
            
            const icon = isStaged ? 'remove' : 'add';
            const actionTitle = isStaged ? 'Unstage' : 'Stage';
            const actionMethod = isStaged ? 'gitUnstage' : 'gitStage';
            
            item.innerHTML = `
                <div class="git-file-status ${file.status}">${file.status[0].toUpperCase()}</div>
                <div class="git-file-path" title="${file.path}">${file.path}</div>
                <div class="git-action-btn" title="${actionTitle}">
                    <span class="material-symbols-outlined" style="font-size: 14px;">${icon}</span>
                </div>
            `;
            
            item.querySelector('.git-action-btn').onclick = async (e) => {
                e.stopPropagation();
                try {
                    await API[actionMethod](currentWorkspaceId, file.path);
                    if (typeof refreshGit === 'function') refreshGit();
                } catch (err) {
                    alert("Git action failed: " + err.message);
                }
            };
            return item;
        };

        if (data.status.staged && data.status.staged.length > 0) {
            data.status.staged.forEach(f => stagedList.appendChild(createFileItem(f, true)));
        } else {
            stagedList.innerHTML = '<div style="padding:4px 8px; color:#555; font-size:11px;">No staged changes</div>';
        }

        if (data.status.unstaged && data.status.unstaged.length > 0) {
            data.status.unstaged.forEach(f => changesList.appendChild(createFileItem(f, false)));
        } else {
            changesList.innerHTML = '<div style="padding:4px 8px; color:#555; font-size:11px;">No changes</div>';
        }

        container.appendChild(stagedSection);
        container.appendChild(changesSection);

        // Commit Box
        const commitBox = document.createElement('div');
        commitBox.className = 'commit-box';
        commitBox.innerHTML = `
            <textarea class="commit-input" rows="2" placeholder="Message (Ctrl+Enter to commit)"></textarea>
            <button class="btn-commit">Commit</button>
        `;
        
        const commitInput = commitBox.querySelector('.commit-input');
        const commitBtn = commitBox.querySelector('.btn-commit');
        
        const doCommit = async () => {
            const msg = commitInput.value.trim();
            if (!msg) return;
            try {
                commitBtn.disabled = true;
                commitBtn.textContent = 'Committing...';
                await API.gitCommit(currentWorkspaceId, msg);
                commitInput.value = '';
                if (typeof refreshGit === 'function') refreshGit();
            } catch (err) {
                alert("Commit failed: " + err.message);
            } finally {
                commitBtn.disabled = false;
                commitBtn.textContent = 'Commit';
            }
        };

        commitBtn.onclick = doCommit;
        commitInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') doCommit();
        });

        container.appendChild(commitBox);

        // Branches
        branchesList.innerHTML = '';
        data.branches.forEach(b => {
            const item = document.createElement('div');
            item.className = `git-branch-item ${b.current ? 'active' : ''}`;
            item.innerHTML = `
                <span class="material-symbols-outlined" style="font-size: 14px;">${b.current ? 'radio_button_checked' : 'radio_button_unchecked'}</span>
                <span>${b.name}</span>
            `;
            if (!b.current) {
                item.onclick = () => onBranchClick(b.name);
            }
            branchesList.appendChild(item);
        });

        // Log
        logList.innerHTML = '';
        if (data.log && Array.isArray(data.log)) {
            data.log.forEach(commit => {
                const item = document.createElement('div');
                item.className = 'git-log-item';
                item.innerHTML = `
                    <div class="commit-header">
                        <span class="commit-hash">${commit.hash}</span>
                        <span class="commit-date">${commit.date}</span>
                    </div>
                    <div class="commit-msg">${this.escapeHtml(commit.message)}</div>
                    <div class="commit-author">by ${commit.author}</div>
                `;
                logList.appendChild(item);
            });
        } else {
            logList.innerHTML = '<div class="git-empty">No commit history found.</div>';
        }
    }
});
