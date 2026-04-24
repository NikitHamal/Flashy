const { contextBridge, ipcRenderer } = require('electron');

function argValue(prefix) {
  const arg = process.argv.find((value) => value.startsWith(prefix));
  return arg ? arg.slice(prefix.length) : '';
}

const authToken = argValue('--flashy-auth-token=');
const baseUrl = argValue('--flashy-base-url=');

contextBridge.exposeInMainWorld('flashyDesktop', {
  authToken,
  baseUrl,
  platform: process.platform,
  versions: process.versions,
  getContext: () => ipcRenderer.invoke('flashy:get-context'),
  selectDirectory: () => ipcRenderer.invoke('flashy:select-directory'),
  openPath: (targetPath) => ipcRenderer.invoke('flashy:open-path', targetPath),
  revealPath: (targetPath) => ipcRenderer.invoke('flashy:reveal-path', targetPath),
  restartBackend: () => ipcRenderer.invoke('flashy:restart-backend')
});
