import asyncio
import httpx

async def test_segment():
    # Test a specific segment URL through the proxy
    segment_url = "https://test-production-8fbc.up.railway.app/api/hls/proxy?url=https%3A%2F%2Fvideo-nss.xhcdn.com%2FrOLt4mNtEjC0H_gKiT4gDQ%3D%3D%2C1768273200%2Fmedia%3Dhls4%2Fmulti%3D256x144%3A144p%3A%2C426x240%3A240p%3A%2C854x480%3A480p%3A%2C1280x720%3A720p%3A%2C1920x1080%3A1080p%3A%2C3840x2160%3A2160p%3A%2F028%2F216%2F343%2F144p.av1.mp4.m3u8&referer=https%3A%2F%2Fxhamster.com%2Fvideos%2Fwhen-my-bhabhi-crazy-for-hard-fucking-xhsIxaD"
    
    print("Testing segment playlist URL through proxy:")
    print("=" * 70)
    print(f"URL: {segment_url[:80]}...")
    print("=" * 70)
    
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(segment_url)
            print(f"\nStatus: {resp.status_code}")
            
            if resp.status_code == 200:
                content = resp.text
                print(f"Content type: {resp.headers.get('content-type')}")
                print(f"\nFirst 800 characters:")
                print("-" * 70)
                print(content[:800])
                
                # Count how many segment URLs are in the playlist
                lines = content.split('\n')
                segment_count = sum(1 for line in lines if line.strip() and not line.startswith('#'))
                print(f"\n{segment_count} video segments found in playlist")
                
            else:
                print(f"ERROR: {resp.status_code}")
                print(resp.text[:500])
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_segment())
