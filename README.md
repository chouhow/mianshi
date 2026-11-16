# 技术面试系统

本地运行的技术面试系统：**题库管理 → 随机组卷 → 现场面试（实时语音转写）→ LLM 评分报告**。

- 前端：Electron + React（Vite）
- 后端：Python FastAPI（本地服务，Electron 启动时自动拉起）
- 存储：本地 JSON 文件（`data/` 目录），无需数据库
- 语音识别：火山引擎豆包大模型流式 ASR（WebSocket 实时转写）
- 评分：火山方舟大模型（OpenAI 兼容接口）

## 环境要求

- Node.js ≥ 18
- Python ≥ 3.10

## 安装与启动

### 方式一：快捷启动（推荐）

- **Windows**：双击 `start.bat`（首次运行自动安装依赖，之后一键启动）
- **macOS / Linux / Git Bash**：`./start.sh`

脚本会自动检查环境（Node 18+、Python 3.10+），首次运行时安装依赖（Electron 走国内镜像，pip 失败自动换清华源），然后启动应用。关闭 Electron 窗口即退出。

### 方式二：手动命令

```bash
# 1. 安装前端依赖
npm install

# 2. 创建 Python 虚拟环境并安装后端依赖
python -m venv .venv
.venv\Scripts\pip install -r backend/requirements.txt    # Windows
# ./venv/bin/pip install -r backend/requirements.txt     # macOS/Linux

# 3. 启动（自动拉起 vite、Electron 与 Python 后端）
npm run dev
```

- 后端服务固定运行在 `http://127.0.0.1:18742`
- 也可只起 Web 调试：`npm run dev:web` 后浏览器打开 `http://localhost:5173`

## 配置密钥

两种方式，任选其一（设置页显式配置的值优先）：

**方式一：`.env` 文件（推荐，换机/重装不丢配置）**

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

在 `.env` 中填入 `ASR_API_KEY`（或旧版 `ASR_APP_ID` + `ASR_ACCESS_TOKEN`）、`ARK_API_KEY`、`ARK_MODEL` 等（文件内有注释说明）。`.env` 已被 gitignore，不会误提交。

**方式二：系统设置页**（保存在 `data/config.json`，留空的字段自动回退读取 `.env`）

| 配置 | 说明 |
| --- | --- |
| ASR App ID / Access Token（或新版 API Key） | 火山引擎控制台「豆包语音大模型」凭据，用于实时语音识别 |
| ASR Resource ID | 默认 `volc.bigasr.sauc.duration`（时长版） |
| 方舟 API Key + 模型 ID | 火山方舟控制台创建，用于评分与简历题生成（如 `doubao-seed-1-6-250615` 或 `ep-xxx`） |
| 评分模式 | 逐题评判（默认）或整卷评判，可两种都试后选择 |
| Mock 模式 | 勾选后 LLM 返回模拟评分，无密钥也能跑通全流程 |

## 使用流程

1. **题库管理**：创建题目（题干、参考答案必填；讲解可选；类型/难度/所属部分）。
   所属部分 = 评分部分：基础（40 分）/ 应用（30 分）/ 简历（30 分），每题 5 分。
2. **试卷管理**：随机组卷（默认基础 8 题、应用 6 题、简历 1 题库题 + 3 道 LLM 简历题），生成后可增删题目。
3. **开始面试**：填候选人姓名、粘贴简历 →（可选）LLM 生成简历个性化题目 → 进入面试。
   - 选择题目 → 🎙️ 开始录音（实时转写）→ 结束录音 → 文本可编辑 → 保存回答
   - 面试者不会 → 「不会」按钮（计 0 分）；不问的题不影响评分
   - 录音自动保存为 `data/audio/{面试ID}/{题目ID}.wav`
4. **结束面试** → 自动进入报告页 → LLM 逐题评分（0-5 分）+ 简历熟悉度评价（0-15 分）→ 按规则汇总。

## 评分规则

- 每题满分 5 分：「不会」计 0 分，「未问」不计入
- **加权两段式记分（Top-K 占 80% + 剩余题占 20%）**：
  - 计分题数 ≥ K：最好的 K 题折算平均分占 80%，剩余题折算平均分占 20%，加权求和
  - 计分题数 < K：**直接求和**（每题满分 5 分，答几题算几分，不足满分的差距就是少答的代价）
  - 基础 40 分（K=8）、应用 30 分（K=6）、简历题 15 分（K=3）
  - 例：基础 12 题，前 4 题得 3 分、后 8 题全对 → 36.8 分（好题主导，一般题只占两成）
  - 例：只答 3 题且全对 → 15 分；再答 2 题中等凑满 8 题 → 36 分（多答升分）
- 简历 30 分 = 简历题 15 分 + 简历熟悉度 15 分（LLM 整体评价）
- 总分 = 基础 + 应用 + 简历（满分 100）

## 目录结构

```
electron/     Electron 主进程（拉起 Python 后端）
src/          React 前端（页面、音频采集、API 客户端）
backend/      FastAPI 后端（路由 / 服务：ASR 中继、LLM 评分、评分规则）
backend/tests pytest 测试（评分规则 + 全流程 API，无需密钥）
data/         运行时数据：题库、试卷、面试记录、录音、配置
```

## 测试

```bash
.venv\Scripts\python -m pytest backend/tests -v
```
