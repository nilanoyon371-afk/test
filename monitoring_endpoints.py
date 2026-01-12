"""
Cache Statistics Endpoint
Monitor cache performance (zero cost)
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics - FREE monitoring"""
    from simple_cache import cache
    return cache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear all cache entries - admin only"""
    from simple_cache import cache
    await cache.clear()
    return {"status": "cache cleared"}


@router.get("/rate-limit/stats")
async def get_rate_limit_stats():
    """Get rate limiter statistics"""
    from rate_limiter import rate_limiter
    return rate_limiter.get_stats()
