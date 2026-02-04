from __future__ import annotations

import httpx
from typing import Any
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://noihjnkjhkjhiusydauytfer.vip"
API_BASE = f"{BASE_URL}/api"

def can_handle(host: str) -> bool:
    return "noihjnkjhkjhiusydauytfer.vip" in host.lower()


async def fetch_json(url: str) -> dict:
    """Fetch JSON from API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": BASE_URL + "/",
    }
    async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


async def list_videos(base_url: str, page: int = 1, limit: int = 20) -> list[dict[str, Any]]:
    """
    List videos using the listMediaBySearchType API
    
    Based on API endpoint: /api/listMediaBySearchType or /api/get
    """
    try:
        # Try the get API first (simpler)
        api_url = f"{API_BASE}/get?page={page}&limit={limit}"
        
        try:
            data = await fetch_json(api_url)
        except Exception:
            # Fallback to listMediaBySearchType
            api_url = f"{API_BASE}/listMediaBySearchType?page={page}&limit={limit}"
            data = await fetch_json(api_url)
        
        items = []
        
        # Parse response - structure may vary
        videos = data.get("data", data.get("list", data.get("items", [])))
        
        for video in videos:
            # Extract fields - adjust based on actual API response
            item = {
                "url": f"{BASE_URL}/video/{video.get('id', video.get('_id', ''))}",
                "title": video.get("title", video.get("name", "Unknown")),
                "thumbnail_url": video.get("thumb", video.get("thumbnail", video.get("cover"))),
                "duration": video.get("duration", video.get("length", "0:00")),
                "views": str(video.get("views", video.get("playCount", "0"))),
                "uploader_name": video.get("author", video.get("uploader", "Xinbake")),
            }
            items.append(item)
        
        return items
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return []


async def scrape(url: str) -> dict[str, Any]:
    """
    Scrape video details using getMediaById API
    
    Extract video ID from URL and fetch metadata
    """
    try:
        # Extract video ID from URL
        # URL format: https://noihjnkjhkjhiusydauytfer.vip/video/123
        video_id = url.split("/")[-1].split("?")[0]
        
        # Call API
        api_url = f"{API_BASE}/getMediaById?id={video_id}"
        data = await fetch_json(api_url)
        
        # Parse response
        video = data.get("data", data)
        
        # Extract video streams
        streams = []
        default_url = None
        
        # Check for video URLs in various formats
        if "videoUrl" in video:
            default_url = video["videoUrl"]
            streams.append({
                "quality": "default",
                "url": default_url,
                "format": "mp4" if ".mp4" in default_url else "hls"
            })
        elif "sources" in video:
            for source in video["sources"]:
                url_str = source.get("url", source.get("src", ""))
                quality = source.get("quality", source.get("label", "unknown"))
                streams.append({
                    "quality": str(quality),
                    "url": url_str,
                    "format": "hls" if ".m3u8" in url_str else "mp4"
                })
            if streams:
                default_url = streams[0]["url"]
        
        video_data = {
            "streams": streams,
            "default": default_url,
            "has_video": len(streams) > 0
        }
        
        return {
            "url": url,
            "title": video.get("title", video.get("name")),
            "description": video.get("description", video.get("desc")),
            "thumbnail_url": video.get("thumb", video.get("thumbnail", video.get("cover"))),
            "duration": video.get("duration", video.get("length")),
            "views": str(video.get("views", video.get("playCount", "0"))),
            "uploader_name": video.get("author", video.get("uploader", "Xinbake")),
            "category": "Xinbake",
            "tags": video.get("tags", []),
            "video": video_data,
            "related_videos": [],
            "preview_url": None
        }
        
    except Exception as e:
        logger.error(f"Error scraping video {url}: {e}")
        raise
