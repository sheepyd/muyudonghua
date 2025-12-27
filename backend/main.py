import asyncio
import hashlib
import json
import os
import re
import traceback
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlencode

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

# 播放鉴权：主页开放，但播放/流需要 cookie
AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "ydyd_auth")
AUTH_COOKIE_VALUE = os.getenv("AUTH_COOKIE_VALUE", "1")

# 本地缓存 (避免每次请求都打到 TMDB/Emby)
BASE_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(BASE_DIR, ".cache")
TMDB_CACHE_FILE = os.path.join(CACHE_DIR, "tmdb_cache.json")
IMAGE_CACHE_DIR = os.path.join(CACHE_DIR, "images")
ENABLE_DISK_CACHE = os.getenv("ENABLE_DISK_CACHE", "1") != "0"

# TMDB 缓存
TMDB_CACHE = {}
TMDB_PREFETCH_INFLIGHT = set()
TMDB_PREFETCH_SEMAPHORE = None


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _is_play_authorized(request: Request) -> bool:
    return request.cookies.get(AUTH_COOKIE_NAME) == AUTH_COOKIE_VALUE


def _require_play_auth(request: Request):
    if _is_play_authorized(request):
        return
    raise HTTPException(status_code=401, detail="Password required")


def _load_tmdb_cache_from_disk():
    if not ENABLE_DISK_CACHE:
        return
    try:
        if not os.path.exists(TMDB_CACHE_FILE):
            return
        with open(TMDB_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            TMDB_CACHE.update(data)
    except Exception as e:
        print(f"TMDB cache load error: {e}")


def _save_tmdb_cache_to_disk():
    if not ENABLE_DISK_CACHE:
        return
    try:
        _ensure_dir(CACHE_DIR)
        tmp_path = TMDB_CACHE_FILE + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(TMDB_CACHE, f, ensure_ascii=False)
        os.replace(tmp_path, TMDB_CACHE_FILE)
    except Exception as e:
        print(f"TMDB cache save error: {e}")


def _get_tmdb_cached(name: str, emby_type: str):
    cache_key = f"{name}_{emby_type}"
    cached = TMDB_CACHE.get(cache_key)
    if not isinstance(cached, dict):
        return None, None
    return cached.get("backdrop"), cached.get("logo")


async def _prefetch_tmdb_images(name: str, emby_type: str):
    if not TMDB_READ_TOKEN or emby_type not in ["Series", "Movie"]:
        return

    cache_key = f"{name}_{emby_type}"
    if cache_key in TMDB_CACHE or cache_key in TMDB_PREFETCH_INFLIGHT:
        return

    TMDB_PREFETCH_INFLIGHT.add(cache_key)

    async def runner():
        try:
            global TMDB_PREFETCH_SEMAPHORE
            if TMDB_PREFETCH_SEMAPHORE is None:
                TMDB_PREFETCH_SEMAPHORE = asyncio.Semaphore(3)
            async with TMDB_PREFETCH_SEMAPHORE:
                async with httpx.AsyncClient() as client:
                    await fetch_tmdb_images(client, name, emby_type)
        except Exception:
            pass
        finally:
            TMDB_PREFETCH_INFLIGHT.discard(cache_key)

    asyncio.create_task(runner())


_load_tmdb_cache_from_disk()

# --- 核心代理逻辑 (保护 API Key) ---

@app.get("/api/proxy/image")
async def proxy_emby_image(path: str, request: Request):
    """
    代理 Emby 图片请求，隐藏 API Key
    path 格式如: /Items/123/Images/Primary
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key not configured")
    
    # 构造真实的 Emby 地址 (确保 path 以 / 开头)
    clean_path = path if path.startswith("/") else f"/{path}"
    emby_url = f"{EMBY_HOST}/emby{clean_path}"

    upstream_headers = {}
    if request.headers.get("if-none-match"):
        upstream_headers["If-None-Match"] = request.headers["if-none-match"]
    if request.headers.get("if-modified-since"):
        upstream_headers["If-Modified-Since"] = request.headers["if-modified-since"]

    forward_params = dict(request.query_params)
    forward_params.pop("path", None)
    forward_params.pop("api_key", None)
    forward_params["api_key"] = API_KEY
    
    cache_key = None
    cache_meta_path = None
    cache_bytes_path = None
    if ENABLE_DISK_CACHE:
        try:
            cache_params = dict(forward_params)
            cache_params.pop("api_key", None)
            key = clean_path + "?" + urlencode(sorted(cache_params.items()))
            cache_key = hashlib.sha256(key.encode("utf-8")).hexdigest()
            cache_meta_path = os.path.join(IMAGE_CACHE_DIR, f"{cache_key}.json")
            cache_bytes_path = os.path.join(IMAGE_CACHE_DIR, f"{cache_key}.bin")

            if os.path.exists(cache_meta_path) and os.path.exists(cache_bytes_path):
                with open(cache_meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f) or {}

                etag = meta.get("etag")
                last_modified = meta.get("last_modified")
                headers = {"Cache-Control": "public, max-age=604800"}
                if etag:
                    headers["etag"] = etag
                if last_modified:
                    headers["last-modified"] = last_modified

                if etag and request.headers.get("if-none-match") == etag:
                    return Response(status_code=304, headers=headers)
                if last_modified and request.headers.get("if-modified-since") == last_modified:
                    return Response(status_code=304, headers=headers)

                with open(cache_bytes_path, "rb") as f:
                    content = f.read()
                return Response(content=content, headers=headers, media_type=meta.get("content_type"))
        except Exception:
            cache_key = None
            cache_meta_path = None
            cache_bytes_path = None

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(emby_url, params=forward_params, headers=upstream_headers, timeout=10.0)
            if resp.status_code not in (200, 304):
                return Response(status_code=resp.status_code)

            headers = {"Cache-Control": "public, max-age=604800"}
            for key in ("etag", "last-modified", "expires"):
                if key in resp.headers:
                    headers[key] = resp.headers[key]

            if resp.status_code == 304:
                return Response(status_code=304, headers=headers)

            if ENABLE_DISK_CACHE and cache_key and cache_meta_path and cache_bytes_path:
                try:
                    _ensure_dir(IMAGE_CACHE_DIR)
                    meta = {
                        "content_type": resp.headers.get("content-type"),
                        "etag": resp.headers.get("etag"),
                        "last_modified": resp.headers.get("last-modified"),
                    }
                    tmp_meta = cache_meta_path + ".tmp"
                    tmp_bytes = cache_bytes_path + ".tmp"
                    with open(tmp_bytes, "wb") as f:
                        f.write(resp.content)
                    with open(tmp_meta, "w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False)
                    os.replace(tmp_bytes, cache_bytes_path)
                    os.replace(tmp_meta, cache_meta_path)
                except Exception:
                    pass

            return Response(content=resp.content, headers=headers, media_type=resp.headers.get("content-type"))
        except Exception as e:
            print(f"Proxy Image Error: {e}")
            raise HTTPException(status_code=502)

@app.get("/api/proxy/stream/{item_id}")
async def proxy_emby_stream(item_id: str, request: Request):
    """
    智能流媒体代理：支持 Range 请求 (拖拽进度条)
    """
    _require_play_auth(request)

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

_SORT_SEASON_EP_RE = re.compile(r"S(?P<season>\d+)\s*E(?P<ep>\d+)", re.IGNORECASE)
_TITLE_EP_RE = re.compile(r"第\s*(?P<ep>\d+)\s*(?:集|话|話|回|章|卷|巻)")
_EP_ONLY_RE = re.compile(r"(?:EP|E)\s*(?P<ep>\d+)", re.IGNORECASE)


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_iso_datetime(value):
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _home_sort_timestamp(item: dict):
    item_type = item.get("Type")
    if item_type == "Series":
        dt = (
            _parse_iso_datetime(item.get("DateLastMediaAdded"))
            or _parse_iso_datetime(item.get("DateLastContentAdded"))
            or _parse_iso_datetime(item.get("DateCreated"))
        )
    else:
        dt = _parse_iso_datetime(item.get("DateCreated")) or _parse_iso_datetime(item.get("PremiereDate"))

    if not dt:
        return 0
    try:
        return dt.timestamp()
    except Exception:
        return 0


def _extract_season_episode(item: dict):
    season = _safe_int(item.get("ParentIndexNumber"))
    episode = _safe_int(item.get("IndexNumber"))

    sort_name = item.get("SortName") or ""
    if (season is None or episode is None) and sort_name:
        match = _SORT_SEASON_EP_RE.search(sort_name)
        if match:
            if season is None:
                season = _safe_int(match.group("season"))
            if episode is None:
                episode = _safe_int(match.group("ep"))

    if episode is None:
        name = item.get("Name") or ""
        for text in (name, sort_name):
            if not text:
                continue
            match = _TITLE_EP_RE.search(text)
            if match:
                episode = _safe_int(match.group("ep"))
                break

    if episode is None and sort_name:
        match = _EP_ONLY_RE.search(sort_name)
        if match:
            episode = _safe_int(match.group("ep"))

    return season, episode


def _proxy_image_url(
    item_id: str,
    emby_image_path: str,
    max_width: Optional[int] = None,
    quality: Optional[int] = None,
):
    params = [f"path=/Items/{item_id}/Images/{emby_image_path}"]
    if max_width is not None:
        params.append(f"maxWidth={max_width}")
    if quality is not None:
        params.append(f"quality={quality}")
    return "/api/proxy/image?" + "&".join(params)


def _episode_sort_key(raw: dict):
    season, episode = _extract_season_episode(raw)
    return (
        1 if season is None else 0,
        season or 0,
        1 if episode is None else 0,
        episode or 0,
        raw.get("SortName") or raw.get("Name") or "",
        str(raw.get("Id") or ""),
    )


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
            
        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
        logo_url = f"https://image.tmdb.org/t/p/w500{logo_path}" if logo_path else None
        
        TMDB_CACHE[cache_key] = {"backdrop": backdrop_url, "logo": logo_url}
        _save_tmdb_cache_to_disk()
        return backdrop_url, logo_url
    except Exception as e:
        print(f"TMDB Error: {e}")
        return None, None

# --- 核心路由 ---

@app.get("/api/videos")
async def get_video_list(limit: int = 10, seriesId: str = None):
    async with httpx.AsyncClient() as client:
        params = {"api_key": API_KEY, "Recursive": "true", "Fields": "Overview,PremiereDate,AirDays,SortName"}
        if USER_ID: params["UserId"] = USER_ID

        try:
            items = []
            if seriesId:
                def unique_by_id(raw_items):
                    seen = set()
                    unique_items = []
                    for raw in raw_items:
                        raw_id = raw.get("Id")
                        if not raw_id or raw_id in seen:
                            continue
                        seen.add(raw_id)
                        unique_items.append(raw)
                    return unique_items

                # 1) 首选 Show Episodes (支持分页/去重，兼容 Emby 限制)
                try:
                    show_base_params = {
                        "api_key": API_KEY,
                        "SortBy": "SortName",
                        "SortOrder": "Ascending",
                        "Fields": "Overview,PremiereDate,AirDays,SortName",
                    }
                    if USER_ID:
                        show_base_params["UserId"] = USER_ID

                    collected = []
                    seen_ids = set()
                    start_index = 0
                    page_limit = 200
                    while True:
                        page_params = dict(show_base_params)
                        page_params.update({"StartIndex": start_index, "Limit": page_limit})
                        response = await client.get(f"{EMBY_HOST}/emby/Shows/{seriesId}/Episodes", params=page_params)
                        response.raise_for_status()
                        data = response.json()
                        page = data.get("Items", [])
                        if not page:
                            break
                        new_count = 0
                        for raw in page:
                            raw_id = raw.get("Id")
                            if not raw_id or raw_id in seen_ids:
                                continue
                            seen_ids.add(raw_id)
                            collected.append(raw)
                            new_count += 1
                        if new_count == 0:
                            break
                        start_index += len(page)
                        total = data.get("TotalRecordCount")
                        if isinstance(total, int) and len(collected) >= total:
                            break
                        if start_index > 5000:
                            break
                    items = unique_by_id(collected)
                except Exception:
                    items = []

                # 2) 兜底：按 Season 拉取 Episodes (有些库/元数据会导致 /Shows/{id}/Episodes 返回不全)
                if len(items) <= 1:
                    try:
                        seasons = []
                        season_params = {"api_key": API_KEY}
                        if USER_ID:
                            season_params["UserId"] = USER_ID
                        try:
                            season_resp = await client.get(f"{EMBY_HOST}/emby/Shows/{seriesId}/Seasons", params=season_params)
                            season_resp.raise_for_status()
                            seasons = season_resp.json().get("Items", []) or []
                        except Exception:
                            seasons = []

                        if not seasons:
                            season_query = dict(params)
                            season_query.update({
                                "IncludeItemTypes": "Season",
                                "ParentId": seriesId,
                                "Recursive": "true",
                                "SortBy": "SortName",
                                "SortOrder": "Ascending",
                                "Limit": 2000,
                            })
                            season_resp = await client.get(f"{EMBY_HOST}/emby/Items", params=season_query)
                            season_resp.raise_for_status()
                            seasons = season_resp.json().get("Items", []) or []

                        season_items = []
                        for season in seasons:
                            season_id = season.get("Id")
                            if not season_id:
                                continue
                            season_query = dict(params)
                            season_query.update({
                                "IncludeItemTypes": "Episode,Video",
                                "ParentId": season_id,
                                "Recursive": "false",
                                "SortBy": "SortName",
                                "SortOrder": "Ascending",
                                "Limit": 2000,
                            })
                            s_ep_resp = await client.get(f"{EMBY_HOST}/emby/Items", params=season_query)
                            s_ep_resp.raise_for_status()
                            season_items.extend(s_ep_resp.json().get("Items", []))

                        items = unique_by_id(season_items) or items
                    except Exception:
                        # 保持 items，不中断主流程
                        pass

                # 3) 兜底：递归查询 Series 下的所有视频 (兼容 Episode/Video 混合)
                if len(items) <= 1:
                    params.update({
                        "IncludeItemTypes": "Episode,Video",
                        "ParentId": seriesId,
                        "SortBy": "SortName",
                        "SortOrder": "Ascending",
                        "Limit": 2000,
                    })
                    response = await client.get(f"{EMBY_HOST}/emby/Items", params=params)
                    response.raise_for_status()
                    data = response.json()
                    items = unique_by_id(data.get("Items", []))
                items.sort(key=_episode_sort_key)
            else:
                home_params = dict(params)
                home_params.update(
                    {
                        "IncludeItemTypes": "Series,Movie",
                        "SortOrder": "Descending",
                        "Limit": limit,
                    }
                )

                response = None
                data = None
                for sort_by in ("DateLastMediaAdded", "DateLastContentAdded", "DateCreated"):
                    try:
                        candidate = dict(home_params)
                        candidate["SortBy"] = sort_by
                        response = await client.get(f"{EMBY_HOST}/emby/Items", params=candidate)
                        response.raise_for_status()
                        data = response.json()
                        break
                    except Exception:
                        response = None
                        data = None

                if data is None:
                    raise HTTPException(status_code=502, detail="Failed to fetch items from Emby")

                items = data.get("Items", [])
                items.sort(key=_home_sort_timestamp, reverse=True)
            
            # TMDB：优先使用本地缓存；未命中则后台预取（不阻塞首页加载）
            tmdb_results = []
            if seriesId:
                tmdb_results = [(None, None) for _ in items]
            else:
                for item in items:
                    name = item.get("Name") or ""
                    emby_type = item.get("Type") or ""
                    backdrop, logo = _get_tmdb_cached(name, emby_type)
                    tmdb_results.append((backdrop, logo))
                    if backdrop is None and logo is None:
                        await _prefetch_tmdb_images(name, emby_type)

            videos = []
            for idx, item in enumerate(items):
                # 安全获取各种图片 (通过代理)
                # 我们的代理地址: /api/proxy/image?path=/Items/{id}/Images/Primary
                poster_url = _proxy_image_url(item["Id"], "Primary", max_width=600, quality=90)
                
                tmdb_backdrop, tmdb_logo = None, None
                if not seriesId and isinstance(tmdb_results[idx], tuple):
                    tmdb_backdrop, tmdb_logo = tmdb_results[idx]

                backdrop_url = tmdb_backdrop or _proxy_image_url(item["Id"], "Backdrop/0", max_width=1600, quality=80)
                logo_url = tmdb_logo or _proxy_image_url(item["Id"], "Logo", max_width=700, quality=90)

                season_number, episode_number = _extract_season_episode(item) if seriesId else (None, None)
                
                videos.append({
                    "id": item["Id"],
                    "title": item["Name"],
                    "type": item["Type"],
                    "poster_url": poster_url,
                    "backdrop_url": backdrop_url,
                    "logo_url": logo_url,
                    "year": item.get("ProductionYear"),
                    "air_days": item.get("AirDays", []),
                    "parent_index_number": season_number,
                    "index_number": episode_number,
                })
            return {"items": videos}
        except HTTPException:
            raise
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/play/{item_id}")
async def get_play_url(item_id: str, request: Request):
    """
    返回播放信息，同样使用代理隐藏密钥
    """
    _require_play_auth(request)

    async with httpx.AsyncClient() as client:
        try:
            emby_params = {"api_key": API_KEY}
            if USER_ID:
                emby_params["UserId"] = USER_ID

            res = await client.get(f"{EMBY_HOST}/emby/Items/{item_id}", params=emby_params)
            res.raise_for_status()
            item = res.json()
            
            series_id = item.get("SeriesId")
            season_id = item.get("SeasonId")
            parent_id = item.get("ParentId")
            item_type = item.get("Type")
            
            # 这里的 url 改为我们后端的流代理地址
            # 注意：如果服务器带宽撑不住，也可以考虑直接返回 Emby 地址，
            # 但那样就无法完全隐藏 API Key。
            masked_play_url = f"/api/proxy/stream/{item_id}"
            
            response_payload = {
                "url": masked_play_url,
                "type": item_type,
                "series_id": series_id,
                "season_id": season_id,
                "parent_id": parent_id,
                "backdrop_url": _proxy_image_url(item["Id"], "Backdrop/0", max_width=1600, quality=80),
                "poster_url": _proxy_image_url(item["Id"], "Primary", max_width=900, quality=90),
                "logo_url": _proxy_image_url(item["Id"], "Logo", max_width=900, quality=90),
                "title": item.get("Name"),
                "parent_index_number": _safe_int(item.get("ParentIndexNumber")),
                "index_number": _safe_int(item.get("IndexNumber")),
            }

            # 尝试从 TMDB 获取背景（失败不影响 series_id/播放）
            target_name = item.get("Name")
            target_type = item.get("Type")
            if target_type == "Episode" and series_id:
                try:
                    s_res = await client.get(f"{EMBY_HOST}/emby/Items/{series_id}", params=emby_params)
                    s_res.raise_for_status()
                    target_name = s_res.json().get("Name") or target_name
                    target_type = "Series"
                except Exception:
                    pass

            tmdb_backdrop, tmdb_logo = _get_tmdb_cached(target_name or "", target_type or "")
            if tmdb_backdrop:
                response_payload["backdrop_url"] = tmdb_backdrop
            if tmdb_logo:
                response_payload["logo_url"] = tmdb_logo
            if not tmdb_backdrop and not tmdb_logo:
                await _prefetch_tmdb_images(target_name or "", target_type or "")

            return response_payload
        except Exception as e:
            traceback.print_exc()
            return {"url": f"/api/proxy/stream/{item_id}", "type": "auto"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)
