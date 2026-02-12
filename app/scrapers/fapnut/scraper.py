import asyncio
import base64
import re
import urllib.parse
from datetime import datetime

from bs4 import BeautifulSoup
from app.core import fetch_html

BASE_URL = "https://fapnut.net"

def can_handle(host: str) -> bool:
    return host.lower().endswith("fapnut.net")

import json
import os

async def get_categories() -> list[dict[str, object]]:
    """
    Get list of categories from static file.
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "categories.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading categories.json: {e}")
        return []

async def scrape_categories() -> list[dict[str, object]]:
    """
    Scrape categories from the website (live).
    """
    url = f"{BASE_URL}/categories/"
    print(f"Fetching categories from: {url}")
    try:
        html = await fetch_html(url)
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    categories = []

    # Selector based on HTML: <article ... class="thumb-block ...">
    articles = soup.select("article.thumb-block")

    for article in articles:
        try:
            link_tag = article.select_one("a")
            if not link_tag:
                continue
            
            cat_url = link_tag.get("href")
            
            # Title
            title_tag = article.select_one(".cat-title")
            title = title_tag.get_text(strip=True) if title_tag else link_tag.get("title")
            
            # Thumbnail
            thumb_url = None
            img_tag = article.select_one("img")
            if img_tag:
                thumb_url = img_tag.get("data-lazy-src") or img_tag.get("src")
                # Handle svg placeholder
                if "data:image/svg+xml" in str(thumb_url) or not thumb_url:
                     # fallback to source srcset if available or finding another img
                     # The HTML shows <source ... data-lazy-srcset="...">
                     picture = article.select_one("picture")
                     if picture:
                         source = picture.select_one("source")
                         if source:
                             srcset = source.get("data-lazy-srcset")
                             if srcset:
                                 # Take the first url from srcset (usually comma separated)
                                 # "url 150w, url 238w, ..."
                                 thumb_url = srcset.split(",")[0].split(" ")[0]

            if cat_url and title:
                categories.append({
                    "name": title,
                    "url": cat_url,
                    "thumbnail_url": thumb_url,
                    "video_count": None
                })
        except Exception as e:
            print(f"Error parsing category item: {e}")
            continue
            
    return categories

async def list_videos(base_url: str = BASE_URL, page: int = 1, limit: int = 20) -> list[dict[str, object]]:
    """
    List videos from a category or homepage.
    """
    if "fapnut.net" not in base_url:
        base_url = BASE_URL

    url = base_url
    if page > 1:
        # Check if base_url is a search query
        if "?s=" in base_url or "&s=" in base_url:
            # WordPress search pagination: /page/X/?s=query
            # Remove existing /page/X/ if present
            clean_url = re.sub(r"/page/\d+/?", "", base_url)
            
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(clean_url)
            query_params = parse_qs(parsed.query)
            
            # Reconstruct URL with /page/X/ path before query
            # Base domain + path (without query)
            path = parsed.path.rstrip("/")
            new_path = f"{path}/page/{page}/"
            
            # Re-add query params
            new_query = urlencode(query_params, doseq=True)
            
            url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                new_path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        elif "/page/" in base_url:
             # Already has page, might be tricky. Assume base_url is a category root.
             # Remove trailing slash
             url = base_url.rstrip("/")
             # Check if it ends with /page/X
             url = re.sub(r"/page/\d+/?$", "", url)
             url = f"{url}/page/{page}/"
        else:
             url = base_url.rstrip("/") + f"/page/{page}/"

    print(f"Fetching list from: {url}")
    try:
        html = await fetch_html(url)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    
    videos = []
    
    # Selector based on HTML: <article ... class="loop-video thumb-block ...">
    articles = soup.select("article.thumb-block")
    
    for article in articles:
        try:
            # Title matches: <a href="..." title="..."> ... </a>
            link_tag = article.select_one("a")
            if not link_tag:
                continue
                
            video_url = link_tag.get("href")
            title = link_tag.get("title")
            
            # Thumbnail matches: data-main-thumb="..." on article or inside picture/img
            thumb_url = article.get("data-main-thumb")
            if not thumb_url:
                img_tag = article.select_one("img")
                if img_tag:
                    thumb_url = img_tag.get("data-lazy-src") or img_tag.get("src")
            
            # Duration matches: <span class="duration">...</span>
            duration_tag = article.select_one(".duration")
            duration = duration_tag.get_text(strip=True) if duration_tag else None
            
            if video_url and title:
                videos.append({
                    "url": video_url,
                    "title": title,
                    "thumbnail_url": thumb_url,
                    "duration": duration,
                    "views": None, # Not visible in snippet
                    "uploader_name": None, # Actors listed in class or tags, but not generic uploader
                    "upload_time": None
                })
        except Exception as e:
            print(f"Error parsing video item: {e}")
            continue
            
    return videos

async def scrape(url: str) -> dict[str, object]:
    """
    Scrape a single video page.
    """
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    
    # Title
    title = ""
    title_tag = soup.select_one("h1.entry-title")
    if title_tag:
        title = title_tag.get_text(strip=True)
        
    # Tags / Categories
    tags = []
    # <div class="tags-list"><a ... class="label">...</a></div>
    tag_links = soup.select(".tags-list a.label")
    for link in tag_links:
        tags.append(link.get_text(strip=True))
        
    # Actors
    # <div id="video-actors"> ... <a ...>Actor Name</a> ... </div>
    actors = []
    actor_links = soup.select("#video-actors a")
    for link in actor_links:
        actors.append(link.get_text(strip=True))
        
    # Video extraction
    # The iframe src contains base64 encoded params
    # <iframe ... src=".../player-x.php?q=BASE64...">
    
    video_url = None
    hls_url = None
    
    iframe = soup.select_one("iframe[src*='player-x.php']")
    if iframe:
        src = iframe.get("src")
        # Extract 'q' param
        parsed_url = urllib.parse.urlparse(src)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        q_param = query_params.get("q", [""])[0]
        
        if q_param:
            try:
                # Decode base64
                # It might need padding? usually urlsafe_b64decode or standard
                # The sample provided was standard base64
                decoded_bytes = base64.b64decode(q_param)
                decoded_str = decoded_bytes.decode("utf-8")
                
                # Decoded string is like: post_id=...&tag=%3Cvideo...
                # Parse this inner query string
                inner_params = urllib.parse.parse_qs(decoded_str)
                tag_encoded = inner_params.get("tag", [""])[0]
                
                if tag_encoded:
                    # Look for source src in the tag HTML
                    # tag is URL encoded, e.g. %3Cvideo...
                    # Wait, urllib.parse.parse_qs DOES NOT decode values automatically? 
                    # Actually it usually dodes percent decoding on keys and values.
                    # Let's verify if 'tag' needs unquoting again.
                    # In my verify script:
                    # params = urllib.parse.parse_qs(decoded)
                    # tag_encoded = params.get('tag', [''])[0]
                    # tag = urllib.parse.unquote(tag_encoded) -- It seems I did unquote it manually.
                    # parse_qs normally decodes + to space and %XX to chars.
                    # If the value inside base64 was double encoded or specific, we might need to check.
                    # The snippet I wrote used unquote (likely standard for this player).
                    
                    # The value from parse_qs is ALREADY decoded from the query string format.
                    # BUT the content of 'tag' param might be HTML encoded or URL encoded itself.
                    # In the provided verify_decode.py:
                    # q = "..." (base64)
                    # decoded = ...
                    # params = parse_qs(decoded) -> tag is "%3Cvideo..."
                    # So yes, it validates that 'tag' value is URL-encoded HTML.
                    
                    # parse_qs decodes the query string structure (key=value), but if value is %3C... it stays %3C...
                    # Wait, standard parse_qs DECODES percent encoding.
                    # If I have "a=b%20c", parse_qs returns {'a': ['b c']}.
                    # If I have "tag=%3Cvideo...", parse_qs SHOULD return {'tag': ['<video...']}.
                    # Let's re-verify my script output.
                    # Script: tag = urllib.parse.unquote(tag_encoded)
                    # Use unquote confirms it was still encoded? Or did I just double check?
                    # If base64 contained "tag=%3Cvideo...", parse_qs converts it to "<video...".
                    # EXCEPT if the base64 string literally contained "tag=%253Cvideo..." (double encoded).
                    # Let's trust my verify script which worked: it used unquote.
                    # However, to be safe, I'll try to unquote, and if it looks like HTML, use it.
                    
                    # NOTE: urllib.parse.parse_qs DOES decode percent encodings.
                    # If the verify script needed `unquote`, it means `parse_qs` result was satisfyingly UNQUOTED?
                    # Wait. `parse_qs` result: `{'tag': ['<video ...']}`.
                    # If I print `tag_encoded`, I see `<video ...`?
                    # If I run `unquote('<video ...')`, it remains `<video ...`.
                    # So `unquote` is harmless if already decoded.
                    
                    # I will assume `tag` HTML is available.
                    
                    tag_html = tag_encoded
                    if "%3C" in tag_html or "%3c" in tag_html:
                         tag_html = urllib.parse.unquote(tag_html)
                         
                    tag_soup = BeautifulSoup(tag_html, "html.parser")
                    source = tag_soup.select_one("source")
                    if source:
                        src_candidate = source.get("src")
                        if ".m3u8" in src_candidate:
                            hls_url = src_candidate
                            video_url = src_candidate # use HLS as default for now if no mp4
                            
                        # If there are other sources?
                        # Usually just one in this player-x
            except Exception as e:
                print(f"Error decoding/parsing iframe: {e}")

    # Fallback/Additional logic for poster
    thumbnail_url = None
    if iframe:
        # Check if poster is in query args too (it was in the long base64 string)
         pass
         
    return {
        "title": title,
        "description": "",
        "thumbnail_url": None, # Could parse from og:image
        "video": {
            "hls": hls_url,
            "default": video_url,
            "streams": [{"url": hls_url, "quality": "auto", "format": "hls"}] if hls_url else [],
            "has_video": bool(video_url)
        },
        "tags": tags,
        "models": actors, # Add models/actors field if supported by schema, otherwise tags
        "related_videos": [] 
    }

async def crawl_videos(base_url: str, start_page: int, max_pages: int, per_page_limit: int, max_items: int) -> list[dict[str, object]]:
    """
    Crawl videos function.
    """
    all_videos = []
    current_page = start_page
    
    while current_page < start_page + max_pages:
        videos = await list_videos(base_url=base_url, page=current_page)
        if not videos:
            break
            
        all_videos.extend(videos)
        if len(all_videos) >= max_items:
            break
            
        current_page += 1
        
    return all_videos[:max_items]

