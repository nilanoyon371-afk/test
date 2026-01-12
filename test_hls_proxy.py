import asyncio
import httpx
import urllib.parse

async def test_hls_url():
    # The original HLS URL
    original_url = "https://video-nss.xhcdn.com/rOLt4mNtEjC0H_gKiT4gDQ==,1768273200/media=hls4/multi=256x144:144p:,426x240:240p:,854x480:480p:,1280x720:720p:,1920x1080:1080p:,3840x2160:2160p:/028/216/343/_TPL_.av1.mp4.m3u8"
    referer = "https://xhamster.com/videos/when-my-bhabhi-crazy-for-hard-fucking-xhsIxaD"
    
    print("Testing HLS URL:")
    print("=" * 70)
    print(f"Original URL: {original_url}")
    print(f"Referer: {referer}")
    print("=" * 70)
    
    # Test 1: Direct access to original URL
    print("\n[TEST 1] Direct access to original URL:")
    print("-" * 70)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": referer
    }
    
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            resp = await client.get(original_url, headers=headers, timeout=10.0)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                content = resp.text[:500]
                print(f"Content preview:\n{content}")
            else:
                print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test 2: Access through proxy
    print("\n\n[TEST 2] Access through Railway proxy:")
    print("-" * 70)
    
    encoded_url = urllib.parse.quote(original_url, safe='')
    encoded_referer = urllib.parse.quote(referer, safe='')
    proxy_url = f"https://test-production-8fbc.up.railway.app/api/hls/playlist?url={encoded_url}&referer={encoded_referer}"
    
    print(f"Proxy URL: {proxy_url[:100]}...")
    
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            resp = await client.get(proxy_url, timeout=30.0)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                content = resp.text[:500]
                print(f"Content preview:\n{content}")
            else:
                print(f"Error: {resp.text[:300]}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_hls_url())
