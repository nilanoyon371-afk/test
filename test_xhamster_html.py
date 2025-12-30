"""
Test script to analyze xHamster HTML structure
"""
from bs4 import BeautifulSoup
import re

# Read the HTML file
with open('xhamster_test.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')

# Find all video links
video_links = soup.select('a[href*="/videos/"]')[:5]

print(f"Found {len(video_links)} video links\n")

for i, link in enumerate(video_links):
    print(f"\n{'='*60}")
    print(f"VIDEO {i+1}")
    print(f"{'='*60}")
    
    # Get URL
    url = link.get('href', '')
    print(f"URL: {url}")
    
    # Get title
    title_el = link.find(class_=re.compile(r"name|title", re.I))
    title = title_el.get_text(strip=True) if title_el else link.get('title', 'N/A')
    print(f"Title: {title}")
    
    # Get thumbnail
    img = link.find('img')
    thumb = img.get('data-src') or img.get('src') if img else 'N/A'
    print(f"Thumbnail: {thumb[:50]}...")
    
    # Find parent container
    container = link
    for tag in ("article", "li", "div"):
        p = link.find_parent(tag)
        if p:
            container = p
            break
    
    print(f"Container: <{container.name} class='{' '.join(container.get('class', []))}'>")
    
    # Look for uploader in container
    uploader_links = container.select('a[href*="/users/"], a[href*="/pornstars/"], a[href*="/channels/"]')
    print(f"\nUploader links found: {len(uploader_links)}")
    for ul in uploader_links[:3]:
        if ul != link:
            print(f"  - {ul.get_text(strip=True)} -> {ul.get('href', '')}")
    
    # Look for views in container
    container_text = container.get_text(" ", strip=True)
    views_match = re.search(r"(\d+(?:\.\d+)?[KMB]?)\s*views?", container_text, re.I)
    print(f"\nViews found: {views_match.group(0) if views_match else 'N/A'}")
    
    # Print a snippet of the container text
    print(f"\nContainer text snippet: {container_text[:200]}")
