
import asyncio
from app.scrapers.spankbang.scraper import list_videos

async def test_pagination():
    base_url = "https://spankbang.com/"
    print(f"Testing pagination for {base_url}...")

    print("Fetching Page 1...")
    page1 = await list_videos(base_url, page=1)
    print(f"Page 1 Items: {len(page1)}")
    if page1:
        print(f"First item: {page1[0]['title']} ({page1[0]['url']})")

    print("\nFetching Page 2...")
    page2 = await list_videos(base_url, page=2)
    print(f"Page 2 Items: {len(page2)}")
    if page2:
        print(f"First item: {page2[0]['title']} ({page2[0]['url']})")
    
    if not page1 or not page2:
        print("\n❌ Failed to fetch one or both pages.")
        return

    # Check for duplicates
    p1_first_url = page1[0]['url']
    p2_first_url = page2[0]['url']

    if p1_first_url == p2_first_url:
        print("\n❌ DUPLICATE DETECTED! Page 1 and Page 2 start with the same video.")
        print(f"Page 1 URL: {p1_first_url}")
        print(f"Page 2 URL: {p2_first_url}")
    else:
        print("\n✅ content seems different.")
        
        # Check intersection
        p1_urls = set(item['url'] for item in page1)
        p2_urls = set(item['url'] for item in page2)
        intersection = p1_urls.intersection(p2_urls)
        print(f"Intersection count: {len(intersection)}")
        if len(intersection) > 5:
             print("⚠️ High overlap between pages!")

if __name__ == "__main__":
    asyncio.run(test_pagination())
