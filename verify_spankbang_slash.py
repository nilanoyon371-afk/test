
import asyncio
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup

async def check_url(url, label):
    print(f"--- Checking {label}: {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
        "Referer": "https://spankbang.com/",
        "Cookie": "age_verified=1; sb_theme=dark",
    }
    try:
        async with AsyncSession(
            impersonate="safari15_3",
            headers=headers,
            timeout=20.0
        ) as client:
            # Check response history to see redirects
            resp = await client.get(url, allow_redirects=True)
            print(f"  Status: {resp.status_code}")
            print(f"  Final URL: {resp.url}")
            if resp.history:
                print(f"  Redirects: {[r.url for r in resp.history]}")
            
            # Extract first video title to fingerprint the page
            soup = BeautifulSoup(resp.text, "lxml")
            first_title = "Unknown"
            item = soup.select_one(".js-video-item a, .video-item a")
            if item:
                # Try finding title in item
                t_el = item.find_parent(class_="video-item").select_one(".n") if item.find_parent(class_="video-item") else None
                if not t_el: t_el = item
                first_title = t_el.get_text(strip=True)[:30]
            
            print(f"  First Video Title: {first_title}")
            return first_title

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

async def main():
    # 1. Check Home
    home_title = await check_url("https://spankbang.com/", "Home")
    
    # 2. Check Amateur WITHOUT Slash
    amateur_no_slash = await check_url("https://spankbang.com/s/amateur", "Amateur (No Slash)")
    
    # 3. Check Amateur WITH Slash
    amateur_slash = await check_url("https://spankbang.com/s/amateur/", "Amateur (Slash)")

    print("\n--- Analysis ---")
    if amateur_no_slash == home_title:
        print("🚨 Amateur (No Slash) == Home Title! (Redirect detected)")
    else:
        print("✅ Amateur (No Slash) seems unique.")
        
    if amateur_slash == home_title:
        print("🚨 Amateur (Slash) == Home Title! (Broken)")
    else:
        print("✅ Amateur (Slash) seems unique.")

    if amateur_no_slash == amateur_slash:
        print("ℹ️ Slash vs No-Slash Content is Identical.")
    else:
         print("ℹ️ Slash vs No-Slash Content DIFFERS.")


if __name__ == "__main__":
    asyncio.run(main())
