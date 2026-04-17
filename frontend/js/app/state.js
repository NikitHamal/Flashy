var currentWorkspaceId = null;
var currentSessionId = null;
var globalData = {
    workspaces: {},
    sessions: []
};
var workspaceFiles = [];
var cachedModels = [];
var useWebSocket = true;
var wsConnected = false;

const hiddenStyle = document.createElement('style');
hiddenStyle.textContent = '.hidden { display: none !important; }';
document.head.appendChild(hiddenStyle);
