
import asyncio
from curl_cffi.requests import AsyncSession

# The specific URL user failed to fetch
# Decoded: https://video-nss.xhcdn.com/05c92101ae1a901841942082976d7657a53c895b990b78f37f46a14b5b,1768269600/media=hls4/multi=256x144:144p:,426x240:240p:,854x480:480p:,1280x720:720p:,1920x1080:1080p:/028/479/974/_TPL_.av1.mp4.m3u8
TEST_URL = "https://video-nss.xhcdn.com/05c92101ae1a901841942082976d7657a53c895b990b78f37f46a14b5b,1768269600/media=hls4/multi=256x144:144p:,426x240:240p:,854x480:480p:,1280x720:720p:,1920x1080:1080p:/028/479/974/_TPL_.av1.mp4.m3u8"
REFERER = "https://xhamster.com/videos/bangladeshi-hot-sex-video-xhMbdRL"

async def get_real_cookies(video_url: str):
    print(f"Fetch Cookies from: {video_url}")
    async with AsyncSession(impersonate="chrome120") as s:
        response = await s.get(video_url)
        print(f"Cookie Page Status: {response.status_code}")
        return s.cookies

async def test_access(name: str, cookies: dict = None):
    print(f"\n--- Testing: {name} ---")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*, application/vnd.t1c.int-27903",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-CH-UA": '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Referer": "https://xhamster.com/" 
    }
    
    try:
        async with AsyncSession(
            impersonate="chrome120", 
            headers=headers, 
            verify=False,
            cookies=cookies
        ) as s:
            response = await s.get(TEST_URL)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {response.headers}")
            if response.status_code == 200:
                print("✅ SUCCESS")
                print(f"Content Preview: {response.text[:100]}")
            else:
                print("❌ FAILED")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

async def main():
    # 1. Test WITHOUT Cookies (Simulates current code)
    await test_access("No Cookies")
    
    # 2. Extract Cookies & Test
    cookies = await get_real_cookies(REFERER)
    if cookies:
        print(f"Got cookies: {list(cookies.keys())}")
        await test_access("With Cookies", cookies)
    else:
        print("Could not get cookies")

if __name__ == "__main__":
    asyncio.run(main())
