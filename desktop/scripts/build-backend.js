const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const desktopDir = path.resolve(__dirname, '..');
const repoRoot = path.resolve(desktopDir, '..');
const python = process.env.PYTHON || process.env.PYTHON_EXECUTABLE || (process.platform === 'win32' ? 'python' : 'python3');
const spec = path.join('desktop', 'pyinstaller', 'flashy-backend.spec');

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, {
    cwd: repoRoot,
    stdio: 'inherit',
    shell: process.platform === 'win32',
    ...options
  });
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

function removeCaches(dir) {
  if (!fs.existsSync(dir)) return;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === '__pycache__' || entry.name === '.pytest_cache') {
        fs.rmSync(full, { recursive: true, force: true });
      } else {
        removeCaches(full);
      }
    } else if (/\.(pyc|pyo|log)$/i.test(entry.name)) {
      fs.rmSync(full, { force: true });
    }
  }
}

run(python, ['-m', 'PyInstaller', spec, '--noconfirm', '--clean']);

const exeName = process.platform === 'win32' ? 'flashy-backend.exe' : 'flashy-backend';
const source = path.join(repoRoot, 'dist', exeName);
const targetDir = path.join(desktopDir, 'build', 'backend');
const target = path.join(targetDir, exeName);

fs.rmSync(targetDir, { recursive: true, force: true });
fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(source, target);
removeCaches(targetDir);

if (process.platform !== 'win32') {
  fs.chmodSync(target, 0o755);
}

const sizeMb = fs.statSync(target).size / (1024 * 1024);
console.log(`Backend sidecar ready: ${path.relative(repoRoot, target)} (${sizeMb.toFixed(1)} MB)`);
console.log(`Platform: ${process.platform}/${process.arch} on ${os.release()}`);
