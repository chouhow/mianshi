const { app, BrowserWindow } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')
const http = require('http')

const ROOT = path.join(__dirname, '..')
const BACKEND_PORT = 18742
const HEALTH_URL = `http://127.0.0.1:${BACKEND_PORT}/health`

let pythonProcess = null
let mainWindow = null

// Python 命令优先级：data/config.json 的 python_cmd > 项目内 .venv > 系统 python
function getPythonCmd() {
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'config.json'), 'utf-8'))
    if (cfg.python_cmd && cfg.python_cmd.trim()) return cfg.python_cmd.trim()
  } catch (_e) {
    /* 配置不存在继续检测 venv */
  }
  const venvPython = process.platform === 'win32'
    ? path.join(ROOT, '.venv', 'Scripts', 'python.exe')
    : path.join(ROOT, '.venv', 'bin', 'python')
  if (fs.existsSync(venvPython)) return venvPython
  return 'python'
}

function startBackend() {
  const cmd = getPythonCmd()
  const backendDir = path.join(ROOT, 'backend')
  pythonProcess = spawn(cmd, ['main.py', '--port', String(BACKEND_PORT)], {
    cwd: backendDir,
    windowsHide: true,
  })
  pythonProcess.stdout.on('data', (d) => process.stdout.write(`[py] ${d}`))
  pythonProcess.stderr.on('data', (d) => process.stderr.write(`[py] ${d}`))
  pythonProcess.on('exit', (code) => {
    console.log(`[electron] python 后端退出 code=${code}`)
    pythonProcess = null
  })
}

function stopBackend() {
  if (!pythonProcess) return
  const pid = pythonProcess.pid
  pythonProcess = null
  if (process.platform === 'win32') {
    // Windows 下杀掉整棵进程树，避免 uvicorn 子进程残留
    spawn('taskkill', ['/pid', String(pid), '/T', '/F'], { windowsHide: true })
  } else {
    try {
      pythonProcess.kill('SIGTERM')
    } catch (_e) {
      /* ignore */
    }
  }
}

function waitForBackend(retries = 60, interval = 500) {
  return new Promise((resolve, reject) => {
    const tryOnce = (left) => {
      const req = http.get(HEALTH_URL, (res) => {
        res.resume()
        if (res.statusCode === 200) resolve()
        else retry(left)
      })
      req.on('error', () => retry(left))
      req.setTimeout(2000, () => {
        req.destroy()
        retry(left)
      })
    }
    const retry = (left) => {
      if (left <= 0) return reject(new Error('后端启动超时'))
      setTimeout(() => tryOnce(left - 1), interval)
    }
    tryOnce(retries)
  })
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1360,
    height: 880,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      spellcheck: false,
    },
  })
  // 允许麦克风（面试语音识别）
  mainWindow.webContents.session.setPermissionRequestHandler((_wc, _permission, callback) => callback(true))
  // 防止拖拽文件等操作导致窗口被导航离开应用
  mainWindow.webContents.on('will-navigate', (e) => e.preventDefault())
  if (process.env.VITE_DEV || process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL || 'http://localhost:5173')
    mainWindow.webContents.openDevTools({ mode: 'detach' })
  } else {
    mainWindow.loadFile(path.join(ROOT, 'dist', 'index.html'))
  }
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(async () => {
  startBackend()
  try {
    await waitForBackend()
  } catch (e) {
    console.error(`[electron] ${e.message}，请检查 python 命令与依赖安装`)
  }
  createWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  stopBackend()
  app.quit()
})

app.on('before-quit', stopBackend)
