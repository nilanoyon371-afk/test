"""
Test script to fetch and analyze xHamster HTML structure
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
import re

async def fetch_and_analyze():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    url = "https://xhamster.com/categories/straight"
    
    print(f"Fetching {url}...")
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(url)
        html = resp.text
    
    print(f"HTML length: {len(html)} chars\n")
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Find all video links
    video_links = soup.select('a[href*="/videos/"]')
    print(f"Found {len(video_links)} total video links\n")
    
    # Process first 3 unique video cards
    seen_urls = set()
    count = 0
    
    for link in video_links:
        url = link.get('href', '')
        if not url or url in seen_urls or '/videos/' not in url:
            continue
        
        seen_urls.add(url)
        count += 1
        
        if count > 3:
            break
        
        print(f"\n{'='*70}")
        print(f"VIDEO CARD {count}")
        print(f"{'='*70}")
        print(f"URL: {url}")
        
        # Get the parent container
        container = link
        for tag in ("article", "div", "li"):
            p = link.find_parent(tag)
            if p:
                container = p
                print(f"Container: <{container.name}> with classes: {container.get('class', [])}")
                break
        
        # Extract title
        title_el = link.find(class_=re.compile(r"name|title", re.I))
        img = link.find('img')
        title = None
        if title_el:
            title = title_el.get_text(strip=True)
        elif img:
            title = img.get('alt')
        
        print(f"Title: {title}")
        
        # Look for uploader links within container
        uploader_selectors = [
            'a[href*="/users/"]',
            'a[href*="/pornstars/"]',
            'a[href*="/channels/"]',
            'a[href*="/creators/"]'
        ]
        
        uploader_found = None
        for selector in uploader_selectors:
            for uploader_link in container.select(selector):
                # Make sure it's not the video link itself
                if uploader_link == link:
                    continue
                uploader_text = uploader_link.get_text(strip=True)
                if uploader_text and len(uploader_text) > 1:
                    uploader_found = uploader_text
                    print(f"Uploader: {uploader_found} (from {uploader_link.get('href', '')})")
                    break
            if uploader_found:
                break
        
        if not uploader_found:
            print("Uploader: Not found")
        
        # Look for views
        container_text = container.get_text(" ", strip=True)
        views = None
        
        # Try multiple patterns
        patterns = [
            r"(\d+(?:\.\d+)?[KMB])\s*views?",
            r"(\d+(?:,\d{3})+)\s*views?",
            r"(\d+)\s*views?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, container_text, re.I)
            if match:
                views = match.group(1)
                print(f"Views: {views} (pattern: {pattern})")
                break
        
        if not views:
            print("Views: Not found")
            print(f"\nContainer text (first 300 chars): {container_text[:300]}")

asyncio.run(fetch_and_analyze())
