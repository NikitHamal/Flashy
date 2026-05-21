const { app, BrowserWindow, Menu, dialog, ipcMain, shell, session } = require('electron');
const { spawn } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');

let mainWindow;
let backendProcess;
let serverUrl;
let serverPort;
let authPassword;
let authHeader;
let isQuitting = false;

const repoRoot = path.resolve(__dirname, '..', '..');
const isDev = !app.isPackaged;
app.setAppUserModelId('dev.flashy.desktop');

function getLogPath() {
  const logDir = path.join(app.getPath('userData'), 'logs');
  fs.mkdirSync(logDir, { recursive: true });
  return path.join(logDir, 'backend.log');
}

function appendBackendLog(chunk) {
  try {
    fs.appendFileSync(getLogPath(), chunk.toString());
  } catch (_) {
    // Logging must never crash the shell.
  }
}

function randomPort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      const port = address.port;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function getBackendExecutable() {
  if (process.env.FLASHY_BACKEND_BIN) {
    return process.env.FLASHY_BACKEND_BIN;
  }

  if (isDev) {
    return process.env.PYTHON || process.env.PYTHON_EXECUTABLE || (process.platform === 'win32' ? 'python' : 'python3');
  }

  const name = process.platform === 'win32' ? 'flashy-backend.exe' : 'flashy-backend';
  return path.join(process.resourcesPath, 'backend', name);
}

function getBackendArgs() {
  if (process.env.FLASHY_BACKEND_CMD) {
    return process.env.FLASHY_BACKEND_CMD.split(' ').filter(Boolean);
  }
  if (isDev) {
    return ['-m', 'backend.app'];
  }
  return [];
}

function configureAuthHeaders() {
  const filter = {
    urls: [
      `http://127.0.0.1:${serverPort}/*`,
      `ws://127.0.0.1:${serverPort}/*`
    ]
  };

  session.defaultSession.webRequest.onBeforeSendHeaders(filter, (details, callback) => {
    details.requestHeaders.Authorization = authHeader;
    callback({ requestHeaders: details.requestHeaders });
  });
}

function waitForHealth(timeoutMs = 30000) {
  const started = Date.now();

  return new Promise((resolve, reject) => {
    const attempt = () => {
      const request = http.get(`${serverUrl}/global/health`, { timeout: 1500 }, (response) => {
        response.resume();
        if (response.statusCode === 200) {
          resolve();
          return;
        }
        retry();
      });
      request.on('timeout', () => request.destroy(new Error('health timeout')));
      request.on('error', retry);
    };

    const retry = () => {
      if (Date.now() - started > timeoutMs) {
        reject(new Error(`Flashy backend did not become ready. Log: ${getLogPath()}`));
        return;
      }
      setTimeout(attempt, 350);
    };

    attempt();
  });
}

async function startBackend() {
  serverPort = await randomPort();
  serverUrl = `http://127.0.0.1:${serverPort}`;
  authPassword = crypto.randomUUID();
  authHeader = `Basic ${Buffer.from(`flashy:${authPassword}`).toString('base64')}`;

  const executable = getBackendExecutable();
  const args = getBackendArgs();
  const userData = path.join(app.getPath('userData'), 'backend-data');
  fs.mkdirSync(userData, { recursive: true });

  const env = {
    ...process.env,
    FLASHY_DESKTOP: '1',
    FLASHY_HOST: '127.0.0.1',
    FLASHY_PORT: String(serverPort),
    FLASHY_RELOAD: '0',
    FLASHY_LOG_LEVEL: process.env.FLASHY_LOG_LEVEL || 'INFO',
    FLASHY_DATA_DIR: userData,
    FLASHY_DESKTOP_AUTH_USERNAME: 'flashy',
    FLASHY_DESKTOP_AUTH_PASSWORD: authPassword,
    PYTHONUNBUFFERED: '1'
  };

  if (isDev) {
    env.PYTHONPATH = repoRoot;
  }

  const cwd = isDev ? repoRoot : path.dirname(executable);
  appendBackendLog(`\n\n[desktop] Starting backend: ${executable} ${args.join(' ')}\n`);

  backendProcess = spawn(executable, args, {
    cwd,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true
  });

  backendProcess.stdout.on('data', appendBackendLog);
  backendProcess.stderr.on('data', appendBackendLog);
  backendProcess.on('exit', (code, signal) => {
    appendBackendLog(`[desktop] Backend exited code=${code} signal=${signal}\n`);
    backendProcess = undefined;
    if (!isQuitting && mainWindow) {
      mainWindow.webContents.send('flashy:backend-exit', { code, signal });
    }
  });

  configureAuthHeaders();
  await waitForHealth();
}

function stopBackend() {
  if (!backendProcess) return;
  const proc = backendProcess;
  backendProcess = undefined;

  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(proc.pid), '/T', '/F'], { windowsHide: true });
  } else {
    proc.kill('SIGTERM');
    setTimeout(() => {
      if (proc.exitCode === null && proc.signalCode === null) proc.kill('SIGKILL');
    }, 2500).unref();
  }
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1320,
    height: 900,
    minWidth: 980,
    minHeight: 640,
    title: 'Flashy',
    backgroundColor: '#0b0f1a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      additionalArguments: [
        `--flashy-auth-token=${authPassword}`,
        `--flashy-base-url=${serverUrl}`
      ]
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = undefined;
  });

  await mainWindow.loadURL(serverUrl);
}

function buildMenu() {
  const template = [
    ...(process.platform === 'darwin' ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Workspace Folder…',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] });
            if (!result.canceled && result.filePaths[0]) {
              await mainWindow.webContents.executeJavaScript(
                `window.dispatchEvent(new CustomEvent('flashy:native-folder-picked', { detail: ${JSON.stringify(result.filePaths[0])} }))`
              );
            }
          }
        },
        { type: 'separator' },
        process.platform === 'darwin' ? { role: 'close' } : { role: 'quit' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Backend',
      submenu: [
        {
          label: 'Restart Backend',
          click: async () => {
            await restartBackend();
          }
        },
        {
          label: 'Open Backend Log',
          click: () => shell.openPath(getLogPath())
        }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function restartBackend() {
  stopBackend();
  await startBackend();
  if (mainWindow) {
    await mainWindow.loadURL(serverUrl);
  }
  return { ok: true, serverUrl };
}

ipcMain.handle('flashy:get-context', () => ({
  serverUrl,
  port: serverPort,
  userData: app.getPath('userData'),
  backendLog: getLogPath(),
  packaged: app.isPackaged,
  platform: process.platform,
  arch: process.arch
}));

ipcMain.handle('flashy:select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] });
  if (result.canceled) return null;
  return result.filePaths[0];
});

ipcMain.handle('flashy:open-path', async (_, targetPath) => shell.openPath(targetPath));
ipcMain.handle('flashy:reveal-path', async (_, targetPath) => shell.showItemInFolder(targetPath));
ipcMain.handle('flashy:restart-backend', restartBackend);

app.whenReady().then(async () => {
  try {
    app.setName('Flashy');
    buildMenu();
    await startBackend();
    await createWindow();
  } catch (error) {
    dialog.showErrorBox('Flashy failed to start', `${error.message}\n\nBackend log: ${getLogPath()}`);
    app.quit();
  }

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow();
    }
  });
});

app.on('before-quit', () => {
  isQuitting = true;
  stopBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
