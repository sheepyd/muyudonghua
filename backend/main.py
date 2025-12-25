import asyncio
import os
import traceback
from datetime import datetime
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
EMBY_HOST = os.getenv("EMBY_HOST", "https://tv.ydyd.me")
API_KEY = os.getenv("EMBY_API_KEY", "99131296af124aa289ae0f7ca0c49e33")
USER_ID = os.getenv("EMBY_USER_ID", "c22a12ff9204439184459d87e25da179")

# TMDB 配置
TMDB_READ_TOKEN = os.getenv("TMDB_READ_TOKEN")
TMDB_CACHE = {}  # 简单内存缓存: { "Name_Type": {"backdrop": "...", "logo": "..."} }

# --- 辅助函数 ---

async def fetch_tmdb_images(client: httpx.AsyncClient, name: str, emby_type: str):
    """
    根据名称和类型从 TMDB 获取高清 Backdrop 和 Logo
    """
    if not TMDB_READ_TOKEN:
        return None, None
        
    if emby_type not in ["Series", "Movie"]:
        return None, None

    cache_key = f"{name}_{emby_type}"
    if cache_key in TMDB_CACHE:
        return TMDB_CACHE[cache_key]["backdrop"], TMDB_CACHE[cache_key]["logo"]

    tmdb_type = "tv" if emby_type == "Series" else "movie"
    headers = {
        "Authorization": f"Bearer {TMDB_READ_TOKEN}",
        "accept": "application/json"
    }
    
    try:
        # 1. 搜索 ID
        search_url = f"https://api.themoviedb.org/3/search/{tmdb_type}?query={quote(name)}&language=zh-CN&page=1"
        resp = await client.get(search_url, headers=headers, timeout=5.0)
        if resp.status_code != 200:
            return None, None
        
        results = resp.json().get("results", [])
        if not results:
            return None, None
            
        tmdb_id = results[0]["id"]
        
        # 2. 获取图片
        images_url = f"https://api.themoviedb.org/3/{tmdb_type}/{tmdb_id}/images"
        img_resp = await client.get(f"{images_url}?include_image_language=zh,en,null", headers=headers, timeout=5.0)
        
        if img_resp.status_code != 200:
            return None, None
            
        img_data = img_resp.json()
        
        # 提取 Backdrop
        backdrop_path = None
        if img_data.get("backdrops"):
            backdrop_path = img_data["backdrops"][0]["file_path"]
        
        # 提取 Logo
        logo_path = None
        if img_data.get("logos"):
            logo_path = img_data["logos"][0]["file_path"]
            
        backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else None
        logo_url = f"https://image.tmdb.org/t/p/original{logo_path}" if logo_path else None
        
        # 写入缓存
        TMDB_CACHE[cache_key] = {"backdrop": backdrop_url, "logo": logo_url}
        return backdrop_url, logo_url

    except Exception as e:
        print(f"TMDB Fetch Error for {name}: {e}")
        return None, None

# --- 核心逻辑 ---

@app.get("/")
async def root():
    return {
        "message": "恭喜！后端服务器运行正常。",
        "docs": "请访问 /docs 查看接口文档",
        "demo": "请访问 /api/videos 查看视频列表"
    }

@app.get("/api/videos")
async def get_video_list(limit: int = 10, seriesId: str = None):
    async with httpx.AsyncClient() as client:
        params = {
            "api_key": API_KEY,
            "Recursive": "true",
            "Fields": "Overview,Path,MediaSources,AirDays,PremiereDate,ChannelImage,LogoImageTags,ArtImageTags,ThumbImageTags"
        }
        if USER_ID:
            params["UserId"] = USER_ID

        if seriesId:
            params.update({
                "IncludeItemTypes": "Episode",
                "ParentId": seriesId,
                "SortBy": "SortName",
                "SortOrder": "Ascending",
            })
        else:
            params.update({
                "IncludeItemTypes": "Series,Movie",
                "SortBy": "DateCreated",
                "SortOrder": "Descending",
                "Limit": limit,
            })

        try:
            response = await client.get(f"{EMBY_HOST}/emby/Items", params=params)
            response.raise_for_status()
            data = response.json()
            
            videos = []
            
            # 并发获取 TMDB 数据
            tmdb_tasks = []
            for item in data.get("Items", []):
                if not seriesId: 
                    tmdb_tasks.append(fetch_tmdb_images(client, item["Name"], item["Type"]))
                else:
                    tmdb_tasks.append(asyncio.sleep(0))

            tmdb_results = await asyncio.gather(*tmdb_tasks) if tmdb_tasks else [None] * len(data.get("Items", []))

            for idx, item in enumerate(data.get("Items", [])):
                # AirDays 逻辑
                air_days = item.get("AirDays", [])
                if not air_days:
                    p_date = item.get("PremiereDate")
                    if p_date:
                        try:
                            dt = datetime.strptime(p_date[:10], "%Y-%m-%d")
                            air_days = [dt.strftime("%A")]
                        except:
                            pass
                
                # 图片逻辑
                poster_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Primary?api_key={API_KEY}"
                
                tmdb_backdrop, tmdb_logo = None, None
                if tmdb_results and idx < len(tmdb_results):
                     result = tmdb_results[idx]
                     if isinstance(result, tuple):
                         tmdb_backdrop, tmdb_logo = result

                backdrop_url = tmdb_backdrop
                if not backdrop_url and item.get("BackdropImageTags"):
                    backdrop_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Backdrop/0?api_key={API_KEY}"
                
                logo_url = tmdb_logo
                if not logo_url and item.get("LogoImageTags"):
                     logo_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Logo?api_key={API_KEY}"
                
                thumb_url = ""
                if item.get("ThumbImageTags"):
                     thumb_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Thumb?api_key={API_KEY}"
                
                video = {
                    "id": item["Id"],
                    "title": item["Name"],
                    "type": item["Type"],
                    "poster_url": poster_url,
                    "backdrop_url": backdrop_url,
                    "logo_url": logo_url,
                    "thumb_url": thumb_url,
                    "year": item.get("ProductionYear"),
                    "container": item.get("Container"),
                    "is_folder": item.get("IsFolder", False),
                    "air_days": air_days
                }
                videos.append(video)
            return {"total": data.get("TotalRecordCount"), "items": videos}
            
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/play/{item_id}")
async def get_play_url(item_id: str):
    play_url = f"{EMBY_HOST}/emby/Videos/{item_id}/stream?static=true&api_key={API_KEY}"
    
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "api_key": API_KEY,
                "Fields": "ParentBackdropImageTags,BackdropImageTags,LogoImageTags"
            }
            res = await client.get(f"{EMBY_HOST}/emby/Items/{item_id}", params=params)
            res.raise_for_status()
            item = res.json()
            
            series_id = item.get("SeriesId")
            item_name = item.get("Name", "")
            
            tmdb_backdrop, tmdb_logo = None, None
            target_name = item_name
            target_type = item.get("Type")
            
            if target_type == "Episode" and series_id:
                try:
                    series_res = await client.get(f"{EMBY_HOST}/emby/Items/{series_id}", params={"api_key": API_KEY})
                    series_data = series_res.json()
                    target_name = series_data.get("Name")
                    target_type = "Series"
                except:
                    pass
            
            tmdb_backdrop, tmdb_logo = await fetch_tmdb_images(client, target_name, target_type)

            backdrop_url = tmdb_backdrop
            if not backdrop_url:
                if item.get("BackdropImageTags"):
                    backdrop_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Backdrop/0?api_key={API_KEY}"
                elif item.get("ParentBackdropImageTags"):
                    parent_id = item.get("ParentBackdropItemId", series_id) 
                    if parent_id:
                        backdrop_url = f"{EMBY_HOST}/emby/Items/{parent_id}/Images/Backdrop/0?api_key={API_KEY}"
                if not backdrop_url and series_id:
                    backdrop_url = f"{EMBY_HOST}/emby/Items/{series_id}/Images/Backdrop/0?api_key={API_KEY}"
            
            logo_url = tmdb_logo
            if not logo_url:
                if item.get("LogoImageTags"):
                    logo_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Logo?api_key={API_KEY}"
                elif series_id:
                    logo_url = f"{EMBY_HOST}/emby/Items/{series_id}/Images/Logo?api_key={API_KEY}"

            poster_url = f"{EMBY_HOST}/emby/Items/{item['Id']}/Images/Primary?api_key={API_KEY}"

            return {
                "url": play_url,
                "type": "auto",
                "series_id": series_id,
                "backdrop_url": backdrop_url,
                "poster_url": poster_url,
                "logo_url": logo_url,
                "title": item.get("Name")
            }
        except Exception as e:
            traceback.print_exc()
            return {
                "url": play_url,
                "type": "auto"
            }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)
