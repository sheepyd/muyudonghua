import asyncio
import os
import traceback
from datetime import datetime
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

# 加载环境变量
load_dotenv()

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 配置部分 ---
# 严格从环境变量读取，避免硬编码
EMBY_HOST = os.getenv("EMBY_HOST", "https://tv.ydyd.me").rstrip("/")
API_KEY = os.getenv("EMBY_API_KEY")
USER_ID = os.getenv("EMBY_USER_ID")
TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")

if not API_KEY:
    print("❌ 警告: 未检测到 EMBY_API_KEY，请检查 .env 文件")

# TMDB 缓存
TMDB_CACHE = {}

# --- 核心代理逻辑 (保护 API Key) ---

@app.get("/api/proxy/image")
async def proxy_emby_image(path: str):
    """
    代理 Emby 图片请求，隐藏 API Key
    path 格式如: /Items/123/Images/Primary
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")
    
    # 构造真实的 Emby 地址 (确保 path 以 / 开头)
    clean_path = path if path.startswith("/") else f"/{path}"
    emby_url = f"{EMBY_HOST}/emby{clean_path}?api_key={API_KEY}"
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(emby_url, timeout=10.0)
            if resp.status_code != 200:
                return Response(status_code=resp.status_code)
            return Response(content=resp.content, media_type=resp.headers.get("content-type"))
        except Exception as e:
            print(f"Proxy Image Error: {e}")
            raise HTTPException(status_code=502)

@app.get("/api/proxy/stream/{item_id}")
async def proxy_emby_stream(item_id: str, request: Request):
    """
    智能流媒体代理：支持 Range 请求 (拖拽进度条)
    """
    stream_url = f"{EMBY_HOST}/emby/Videos/{item_id}/stream?static=true&api_key={API_KEY}"
    
    # 1. 透传 Range 头 (关键：告诉 Emby 我们只需要视频的一部分)
    headers = {}
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header
    
    # 使用独立的 Client 实例以控制生命周期，并禁用超时（防止播放中断）
    client = httpx.AsyncClient(timeout=None)
    req = client.build_request("GET", stream_url, headers=headers)
    
    try:
        # 发送请求但不立即下载 Body
        upstream_resp = await client.send(req, stream=True)
    except Exception as e:
        await client.aclose()
        print(f"Stream Connect Error: {e}")
        raise HTTPException(status_code=502, detail="Upstream Connect Error")

    # 2. 筛选需要转发给浏览器的响应头
    forward_headers = {}
    # 只要这几个关键头，其他的过滤掉以免冲突
    for key in ["content-type", "content-length", "content-range", "accept-ranges"]:
        if key in upstream_resp.headers:
            forward_headers[key] = upstream_resp.headers[key]
            
    # 关键：告诉 Nginx 不要缓存此响应，直接流式传输给客户端
    forward_headers["X-Accel-Buffering"] = "no"

    # 3. 定义流生成器 (一边收一边发)
    async def stream_generator():
        try:
            async for chunk in upstream_resp.aiter_bytes(chunk_size=64 * 1024): # 64KB chunks
                yield chunk
        except Exception as e:
            print(f"Stream Transfer Error: {e}")
        finally:
            # 必须手动关闭上游连接
            await upstream_resp.aclose()
            await client.aclose()

    # 4. 返回流式响应，状态码透传 (200 或 206)
    return StreamingResponse(
        stream_generator(), 
        status_code=upstream_resp.status_code,
        headers=forward_headers,
        media_type=upstream_resp.headers.get("content-type")
    )

# --- 辅助函数 ---

async def fetch_tmdb_images(client: httpx.AsyncClient, name: str, emby_type: str):
    if not TMDB_READ_TOKEN or emby_type not in ["Series", "Movie"]:
        return None, None

    cache_key = f"{name}_{emby_type}"
    if cache_key in TMDB_CACHE:
        return TMDB_CACHE[cache_key]["backdrop"], TMDB_CACHE[cache_key]["logo"]

    tmdb_type = "tv" if emby_type == "Series" else "movie"
    headers = {"Authorization": f"Bearer {TMDB_READ_TOKEN}", "accept": "application/json"}
    
    try:
        search_url = f"https://api.themoviedb.org/3/search/{tmdb_type}?query={quote(name)}&language=zh-CN&page=1"
        resp = await client.get(search_url, headers=headers, timeout=5.0)
        results = resp.json().get("results", [])
        if not results: return None, None
            
        tmdb_id = results[0]["id"]
        img_resp = await client.get(f"https://api.themoviedb.org/3/{tmdb_type}/{tmdb_id}/images?include_image_language=zh,en,null", headers=headers, timeout=5.0)
        img_data = img_resp.json()
        
        backdrop_path = img_data["backdrops"][0]["file_path"] if img_data.get("backdrops") else None
        logo_path = img_data["logos"][0]["file_path"] if img_data.get("logos") else None
            
        backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else None
        logo_url = f"https://image.tmdb.org/t/p/original{logo_path}" if logo_path else None
        
        TMDB_CACHE[cache_key] = {"backdrop": backdrop_url, "logo": logo_url}
        return backdrop_url, logo_url
    except Exception as e:
        print(f"TMDB Error: {e}")
        return None, None

# --- 核心路由 ---

@app.get("/api/videos")
async def get_video_list(limit: int = 10, seriesId: str = None):
    async with httpx.AsyncClient() as client:
        params = {"api_key": API_KEY, "Recursive": "true", "Fields": "Overview,PremiereDate,AirDays"}
        if USER_ID: params["UserId"] = USER_ID

        if seriesId:
            params.update({
                "IncludeItemTypes": "Episode",
                "ParentId": seriesId,
                "SortBy": "SortName",
                "SortOrder": "Ascending",
                "Limit": 2000,
            })
        else:
            params.update({"IncludeItemTypes": "Series,Movie", "SortBy": "DateCreated", "SortOrder": "Descending", "Limit": limit})

        try:
            response = await client.get(f"{EMBY_HOST}/emby/Items", params=params)
            response.raise_for_status()
            data = response.json()
            
            # 并发获取 TMDB
            tmdb_tasks = [fetch_tmdb_images(client, item["Name"], item["Type"]) if not seriesId else asyncio.sleep(0) for item in data.get("Items", [])]
            tmdb_results = await asyncio.gather(*tmdb_tasks)

            videos = []
            for idx, item in enumerate(data.get("Items", [])):
                # 安全获取各种图片 (通过代理)
                # 我们的代理地址: /api/proxy/image?path=/Items/{id}/Images/Primary
                poster_url = f"/api/proxy/image?path=/Items/{item['Id']}/Images/Primary"
                
                tmdb_backdrop, tmdb_logo = None, None
                if not seriesId and isinstance(tmdb_results[idx], tuple):
                    tmdb_backdrop, tmdb_logo = tmdb_results[idx]

                backdrop_url = tmdb_backdrop or f"/api/proxy/image?path=/Items/{item['Id']}/Images/Backdrop/0"
                logo_url = tmdb_logo or f"/api/proxy/image?path=/Items/{item['Id']}/Images/Logo"
                
                videos.append({
                    "id": item["Id"],
                    "title": item["Name"],
                    "type": item["Type"],
                    "poster_url": poster_url,
                    "backdrop_url": backdrop_url,
                    "logo_url": logo_url,
                    "year": item.get("ProductionYear"),
                    "air_days": item.get("AirDays", [])
                })
            return {"items": videos}
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/play/{item_id}")
async def get_play_url(item_id: str):
    """
    返回播放信息，同样使用代理隐藏密钥
    """
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{EMBY_HOST}/emby/Items/{item_id}", params={"api_key": API_KEY})
            res.raise_for_status()
            item = res.json()
            
            series_id = item.get("SeriesId")
            
            # 这里的 url 改为我们后端的流代理地址
            # 注意：如果服务器带宽撑不住，也可以考虑直接返回 Emby 地址，
            # 但那样就无法完全隐藏 API Key。
            masked_play_url = f"/api/proxy/stream/{item_id}"
            
            # 尝试从 TMDB 获取背景
            target_name = item.get("Name")
            target_type = item.get("Type")
            if target_type == "Episode" and series_id:
                s_res = await client.get(f"{EMBY_HOST}/emby/Items/{series_id}", params={"api_key": API_KEY})
                target_name = s_res.json().get("Name")
                target_type = "Series"
            
            tmdb_backdrop, tmdb_logo = await fetch_tmdb_images(client, target_name, target_type)

            return {
                "url": masked_play_url,
                "series_id": series_id,
                "backdrop_url": tmdb_backdrop or f"/api/proxy/image?path=/Items/{item['Id']}/Images/Backdrop/0",
                "poster_url": f"/api/proxy/image?path=/Items/{item['Id']}/Images/Primary",
                "logo_url": tmdb_logo or f"/api/proxy/image?path=/Items/{item['Id']}/Images/Logo",
                "title": item.get("Name")
            }
        except Exception as e:
            traceback.print_exc()
            return {"url": f"/api/proxy/stream/{item_id}", "type": "auto"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)
