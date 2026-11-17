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
let stopping = false
let retryTimer = null
let retryDelay = 500

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
  pythonProcess.on('error', (error) => console.error('[electron] 后端启动失败', error.message))
  pythonProcess.once('close', () => {
    pythonProcess = null
    if (!stopping) {
      retryTimer = setTimeout(ensureBackend, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 8000)
    }
  })
}

function stopBackend() {
  stopping = true
  clearTimeout(retryTimer)
  const child = pythonProcess
  if (!child?.pid) return
  pythonProcess = null
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { windowsHide: true })
  } else {
    child.kill('SIGTERM')
  }
}

function backendHealthy() {
  return new Promise((resolve) => {
    const req = http.get(HEALTH_URL, (res) => {
      let body = ''
      res.on('data', chunk => { body += chunk })
      res.on('error', () => resolve(false))
      res.on('end', () => {
        try {
          resolve(res.statusCode === 200 && JSON.parse(body).service === 'mianshi-backend')
        } catch {
          resolve(false)
        }
      })
    })
    req.on('error', () => resolve(false))
    req.setTimeout(1500, () => req.destroy())
  })
}

async function ensureBackend() {
  const healthy = await backendHealthy()
  if (stopping) return
  if (healthy) {
    retryDelay = 500
    // Also supervise availability when another launcher owns the service.
    retryTimer = setTimeout(ensureBackend, 3000)
  } else if (!pythonProcess) {
    startBackend()
  }
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
  await ensureBackend()
  for (let i = 0; i < 20 && !stopping; i++) {
    if (await backendHealthy()) break
    await new Promise(resolve => setTimeout(resolve, 250))
  }
  if (stopping) return
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
