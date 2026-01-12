from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse
from app.services.hls_proxy import hls_proxy

router = APIRouter()

@router.get("/proxy")
async def proxy_stream(url: str = Query(..., description="URL to proxy")):
    """
    General proxy for video segments and resources.
    """
    # If it's a TS file, stream it
    if ".ts" in url or ".m4s" in url: 
         return await hls_proxy.stream_segment(url)
    
    # Otherwise generic proxy
    return await hls_proxy.proxy_request(url)

@router.get("/playlist")
async def proxy_playlist(url: str = Query(..., description="M3U8 Playlist URL")):
    """
    Proxy M3U8 playlist and rewrite internal URLs to use /proxy endpoint.
    """
    # We need the base URL of THIS API to rewrite links
    # Hardcoded for now or use Request request.base_url
    # Let's assume the client uses the same host.
    
    # We'll use a relative path for rewrites if possible, or construct absolute.
    # But proxy_m3u8 takes base_proxy_url.
    # Let's use a hardcoded base for simplicity or extract from request if we had Request object.
    
    # Ideally should be: http://localhost:8000/api/hls/proxy
    # But to be safe let's use the /proxy endpoint relative to API root
    
    # For now, let's just pass the localhost default or specific dev URL
    base_proxy_url = "http://localhost:8000/api/hls/proxy"
    
    content = await hls_proxy.proxy_m3u8(url, base_proxy_url)
    
    return Response(
        content=content, 
        media_type="application/vnd.apple.mpegurl"
    )
