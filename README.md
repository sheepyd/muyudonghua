# YDYD.ME / MuYuDonghua v0

基于 `FastAPI` + `Vue 3 (Vite)` 的动漫网站前后端项目，深度集成 Emby，支持可选的 TMDB 元数据，并使用胶片风格前端模板作为主 UI。

## 功能概览

- 胶片风格主页 + 播放页（右侧 Playlist 选集）
- Emby 图片/视频流后端代理（隐藏 `EMBY_API_KEY`，视频流支持 Range）
- 播放密码门禁：主页公开，播放/选集/视频流需要密码（浏览器记住登录）
- 本地缓存：TMDB 元数据与图片代理会落盘缓存，降低首次加载后的重复请求
- 选集 EP 编号：优先使用 Emby 的真实集数（`IndexNumber` 等）

## 目录结构

- `backend/`：FastAPI 后端（Emby 代理、列表、播放、鉴权、缓存）
- `frontend/`：Vue 3 + Vite 前端（胶片主页、播放页、密码弹窗）
- `.env`：运行配置（密钥/密码等）
- `start_dev.sh`：一键启动脚本（创建 venv、安装依赖、启动前后端）
- `模板/`：你的前端模板目录（已忽略，不会提交到 Git）

## 快速开始（开发）

### 1) 配置环境变量

```bash
cp .env.example .env
```

`.env` 关键配置：

- `EMBY_HOST`：你的 Emby 地址（例：`https://tv.example.com`）
- `EMBY_API_KEY`：Emby API Key（必填）
- `EMBY_USER_ID`：可选（有些库接口会需要/更完整）
- `TMDB_READ_TOKEN`：可选（不填也能用，只是缺少 TMDB 背景/Logo）

播放密码门禁（建议至少设置 `AUTH_SECRET`）：

- `AUTH_PASSWORD`：播放密码（默认 `ydydme`）
- `AUTH_SECRET`：签名密钥（生产环境必须是强随机；不设置会导致后端重启后需要重新输入密码）
- `AUTH_TOKEN_TTL_SECONDS`：登录有效期（默认 30 天）
- `COOKIE_SECURE`：HTTPS 部署时设为 `1`

### 2) 一键启动

```bash
chmod +x start_dev.sh
bash start_dev.sh
```

- 前端：`http://localhost:3000`
- 后端：`http://127.0.0.1:8800`

## 播放密码门禁说明

- 主页任意访问。
- 点击播放按钮或直接访问 `/play/:id` 时，会弹出密码框。
- 密码校验在后端完成，成功后写入 `HttpOnly` Cookie，浏览器会记住一段时间（默认 30 天）。

## 缓存说明

- 后端缓存目录：`backend/.cache/`
  - `backend/.cache/tmdb_cache.json`：TMDB 结果缓存
  - `backend/.cache/images/`：图片代理缓存
- 缓存可安全删除（会在下次请求时自动重新生成）。

## 生产部署建议（Nginx/反代）

1) 构建前端：

```bash
cd frontend && npm run build
```

2) 运行后端（示例）：

```bash
cd backend && ./venv/bin/python main.py
```

3) Nginx 配置要点：

- 静态站点根目录指向 `frontend/dist`
- 将 `/api/` 反代到后端 `http://127.0.0.1:8800`
- HTTPS 时建议：
  - 设置 `COOKIE_SECURE=1`
  - 或者反代时补齐 `X-Forwarded-Proto: https`（让后端能自动识别并设置 Secure Cookie）

## 安全提示（重要）

当前是“共享播放密码”的门禁方案，并非多用户系统；如需更强的权限控制（账号体系、访问审计、不同用户权限），建议接入更完整的鉴权系统或直接使用 Emby 的用户鉴权能力。
