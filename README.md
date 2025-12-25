# MuYuDonghua (暮雨动画) v0

一个基于 FastAPI 和 Vue 3 开发的高颜值动漫流媒体平台，集成 Emby 和 TMDB。

## ✨ 特性

- **高级暗黑模式**: 现代 Slate UI 风格，搭配霓虹粉强调色。
- **TMDB 深度集成**: 自动搜索并抓取高清海报、背景图及 Logo。
- **动态播放器**: 集成 Artplayer，支持画中画、截图、倍速播放等高级功能。
- **响应式设计**: 完美适配桌面端和移动端。
- **模块化后端**: 基于异步 FastAPI，性能强劲。

## 🛠️ 项目结构

- `backend/`: FastAPI 后端服务。
  - `main.py`: 核心 API 逻辑。
  - `venv/`: Python 虚拟环境 (已被 git 忽略)。
  - `requirements.txt`: 依赖列表。
- `frontend/`: Vue 3 + Vite 前端应用。
  - `src/`: 组件、视图及路由。
  - `style.css`: 全局样式定义。
- `.env`: 隐私密钥配置 (Emby & TMDB)。
- `start_dev.sh`: 一键启动脚本。

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.9+
- Node.js & npm

### 2. 配置环境变量

将根目录下的 `.env.example` 重命名为 `.env`，并填入你的密钥：

```env
# Emby 配置
EMBY_HOST=https://your-emby-server
EMBY_API_KEY=your-api-key
EMBY_USER_ID=your-user-id

# TMDB 配置
TMDB_READ_TOKEN=your-tmdb-token
```

### 3. 一键启动 (推荐)

在项目根目录下执行：

```bash
chmod +x start_dev.sh
./start_dev.sh
```

脚本会自动：
1. 检测并使用 `backend/venv`。
2. 安装前端 `node_modules` (如果不存在)。
3. 同时启动后端 (8800) 和前端 (3000)。

### 4. 手动启动

#### 后端 (Backend)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

#### 前端 (Frontend)
```bash
cd frontend
npm install
npm run dev
```

## 📦 部署与同步

项目已配置好 `.gitignore`。上传到你的 GitHub 仓库：

```bash
git add .
git commit -m "update: feature or fix description"
git push
```
