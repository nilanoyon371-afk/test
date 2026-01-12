import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Simulate the URL rewriting logic
def test_url_rewriting():
    base_proxy_url = "https://test-production-8fbc.up.railway.app/api/hls/proxy"
    
    test_urls = [
        "144p.av1.mp4.m3u8",  # Nested m3u8
        "segment001.ts",       # TS segment
        "https://example.com/720p.m3u8",  # Absolute m3u8
        "https://example.com/chunk.ts",    # Absolute segment
    ]
    
    print("Testing URL Rewriting Logic:")
    print("=" * 80)
    print(f"Base Proxy URL: {base_proxy_url}\n")
    
    for url in test_urls:
        print(f"Input: {url}")
        
        # Check if this is an m3u8
        if '.m3u8' in url:
            # Should use playlist endpoint
            proxied_url = base_proxy_url.replace('/proxy', '/playlist')
            print(f"  -> Routes to: /api/hls/playlist")
            print(f"  -> Expected: {proxied_url}")
        else:
            # Should use proxy endpoint
            proxied_url = base_proxy_url
            print(f"  -> Routes to: /api/hls/proxy")
            print(f"  -> Expected: {proxied_url}")
        
        print()

if __name__ == "__main__":
    test_url_rewriting()
