# Rate Limiting Middleware

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from cache import cache
from config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Skip rate limiting for health endpoints
        if request.url.path in ["/health", "/health/detailed", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier (IP or user ID)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"
        
        # Check rate limits
        current_minute = int(time.time() / 60)
        current_hour = int(time.time() / 3600)
        
        minute_key = f"ratelimit:minute:{identifier}:{current_minute}"
        hour_key = f"ratelimit:hour:{identifier}:{current_hour}"
        
        # Increment counters
        minute_count = await cache.increment(minute_key, ttl=60)
        hour_count = await cache.increment(hour_key, ttl=3600)
        
        # Check limits
        if minute_count > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: {settings.RATE_LIMIT_PER_MINUTE} requests per minute",
                    "retry_after": 60 - int(time.time() % 60)
                },
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(60 - int(time.time() % 60)),
                    "Retry-After": str(60 - int(time.time() % 60))
                }
            )
        
        if hour_count > settings.RATE_LIMIT_PER_HOUR:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: {settings.RATE_LIMIT_PER_HOUR} requests per hour",
                    "retry_after": 3600 - int(time.time() % 3600)
                },
                headers={
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_HOUR),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(3600 - int(time.time() % 3600)),
                    "Retry-After": str(3600 - int(time.time() % 3600))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE - minute_count)
        response.headers["X-RateLimit-Limit-Hour"] = str(settings.RATE_LIMIT_PER_HOUR)
        response.headers["X-RateLimit-Remaining-Hour"] = str(settings.RATE_LIMIT_PER_HOUR - hour_count)
        
        return response
