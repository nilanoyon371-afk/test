from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import HttpUrl
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
import masa49
import xhamster
import xnxx
import xvideos
from auth import (
    get_current_user,
    get_current_active_admin,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    generate_api_key,
    check_rate_limit,
)
from cache import cache
from config import settings
from database import get_db, init_db, close_db
from hls_proxy import hls_proxy
from logging_config import logger
from models import User, ScrapeHistory, VideoMetadata, APIStats
from rate_limit import RateLimitMiddleware
from schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ListItem,
    ListRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    HealthResponse,
    DetailedHealthResponse,
    UsageStats,
    UpdateQuota,
)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Advanced Scraper API")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Connect to Redis cache
    try:
        await cache.connect()
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
    
    logger.info(f"🎉 API started successfully on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down API")
    await close_db()
    await cache.disconnect()
    await hls_proxy.close()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced video scraper API with authentication, caching, and HLS proxy",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add rate limiting middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)


# ==================== Helper Functions ====================

async def _scrape_dispatch(url: str, host: str) -> dict[str, object]:
    """Dispatch scrape request to appropriate scraper"""
    if xhamster.can_handle(host):
        return await xhamster.scrape(url)
    if masa49.can_handle(host):
        return await masa49.scrape(url)
    if xnxx.can_handle(host):
        return await xnxx.scrape(url)
    if xvideos.can_handle(host):
        return await xvideos.scrape(url)
    raise HTTPException(status_code=400, detail="Unsupported host")


async def _list_dispatch(base_url: str, host: str, page: int, limit: int) -> list[dict[str, object]]:
    """Dispatch list request to appropriate scraper"""
    if xhamster.can_handle(host):
        return await xhamster.list_videos(base_url=base_url, page=page, limit=limit)
    if masa49.can_handle(host):
        return await masa49.list_videos(base_url=base_url, page=page, limit=limit)
    if xnxx.can_handle(host):
        return await xnxx.list_videos(base_url=base_url, page=page, limit=limit)
    if xvideos.can_handle(host):
        return await xvideos.list_videos(base_url=base_url, page=page, limit=limit)
    raise HTTPException(status_code=400, detail="Unsupported host")


async def _crawl_dispatch(
    base_url: str,
    host: str,
    start_page: int,
    max_pages: int,
    per_page_limit: int,
    max_items: int,
) -> list[dict[str, object]]:
    """Dispatch crawl request to appropriate scraper"""
    if xhamster.can_handle(host):
        return await xhamster.crawl_videos(
            base_url=base_url,
            start_page=start_page,
            max_pages=max_pages,
            per_page_limit=per_page_limit,
            max_items=max_items,
        )
    raise HTTPException(status_code=400, detail="Unsupported host")


async def log_request(
    db: AsyncSession,
    user: Optional[User],
    url: str,
    platform: str,
    endpoint_type: str,
    success: bool,
    status_code: Optional[int],
    error_message: Optional[str],
    response_time: float,
    cached: bool,
    request: Request,
):
    """Log scraping request to database"""
    # Temporarily disabled to debug endpoint issues
    return
    
    try:
        history = ScrapeHistory(
            user_id=user.id if user else None,
            url=url,
            platform=platform,
            endpoint_type=endpoint_type,
            success=success,
            status_code=status_code,
            error_message=error_message,
            response_time=response_time,
            cached=cached,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        db.add(history)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log request: {e}")
        # Don't let logging failures crash the API
        try:
            await db.rollback()
        except Exception:
            pass


# ==================== Authentication Endpoints ====================

@app.post("/auth/register", response_model=UserResponse, status_code=201, tags=["Authentication"])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user and generate API key"""
    # Check if user exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    api_key = generate_api_key()
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        api_key=api_key,
        role="user",
        is_active=True,
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.email}")
    return new_user


@app.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password to get JWT tokens"""
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


# ==================== Health & Status Endpoints ====================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    """Basic health check"""
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow()
    )


@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """Detailed health check with dependency status"""
    # Check database
    db_healthy = False
    try:
        await db.execute(select(func.count()).select_from(User))
        db_healthy = True
    except Exception:
        pass
    
    # Check Redis
    redis_stats = await cache.get_stats()
    redis_healthy = redis_stats.get("connected", False)
    
    return DetailedHealthResponse(
        status="ok" if db_healthy and redis_healthy else "degraded",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        database=db_healthy,
        redis=redis_healthy,
        celery=False,  # TODO: Implement Celery health check
        dependencies={
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "hls_proxy": "enabled" if settings.HLS_PROXY_ENABLED else "disabled",
        }
    )


# ==================== Scraping Endpoints ====================

@app.get("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def scrape(
    url: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scrape video metadata from URL (with caching)"""
    start_time = time.time()
    req = ScrapeRequest(url=url)
    platform = req.url.host or ""
    cached = False
    
    # Check quota
    if current_user:
        await check_rate_limit(current_user, db)
    
    # Check cache
    cached_data = await cache.get_scrape_cache(str(req.url))
    if cached_data:
        cached = True
        response_time = time.time() - start_time
        await log_request(db, current_user, str(req.url), platform, "scrape", True, 200, None, response_time, cached, request)
        cached_data["cached"] = True
        return ScrapeResponse(**cached_data)
    
    # Scrape
    try:
        data = await _scrape_dispatch(str(req.url), platform)
        response_time = time.time() - start_time
        
        # Cache result
        await cache.set_scrape_cache(str(req.url), data)
        
        # Log success
        await log_request(db, current_user, str(req.url), platform, "scrape", True, 200, None, response_time, cached, request)
        
        data["cached"] = False
        return ScrapeResponse(**data)
    except httpx.HTTPStatusError as e:
        response_time = time.time() - start_time
        await log_request(db, current_user, str(req.url), platform, "scrape", False, e.response.status_code, str(e), response_time, cached, request)
        raise HTTPException(status_code=e.response.status_code, detail="Upstream returned error") from e
    except Exception as e:
        response_time = time.time() - start_time
        await log_request(db, current_user, str(req.url), platform, "scrape", False, 502, str(e), response_time, cached, request)
        raise HTTPException(status_code=502, detail="Failed to fetch url") from e


@app.post("/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def scrape_post(
    body: ScrapeRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Scrape video metadata from URL (POST method with caching)"""
    return await scrape(str(body.url), request, current_user, db)


@app.get("/list", response_model=list[ListItem], tags=["Scraping"])
async def list_videos(
    base_url: str,
    page: int = 1,
    limit: int = 20,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List videos from a platform category/page (with caching)"""
    start_time = time.time()
    req = ListRequest(base_url=base_url)
    platform = req.base_url.host or ""
    cached = False
    
    # Validate parameters
    page = max(1, min(page, 100))
    limit = max(1, min(limit, 60))
    
    # Check quota
    if current_user:
        await check_rate_limit(current_user, db)
    
    # Check cache
    cached_data = await cache.get_list_cache(str(req.base_url), page, limit)
    if cached_data:
        cached = True
        return [ListItem(**it) for it in cached_data]
    
    # Fetch list
    try:
        items = await _list_dispatch(str(req.base_url), platform, page, limit)
        response_time = time.time() - start_time
        
        # Cache result
        await cache.set_list_cache(str(req.base_url), page, limit, items)
        
        return [ListItem(**it) for it in items]
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Upstream returned error") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail="Failed to fetch url") from e


@app.get("/crawl", response_model=list[ListItem], tags=["Scraping"])
async def crawl_videos(
    base_url: str,
    start_page: int = 1,
    max_pages: int = 5,
    per_page_limit: int = 0,
    max_items: int = 500,
    request: Request = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crawl multiple pages of videos"""
    start_time = time.time()
    req = ListRequest(base_url=base_url)
    platform = req.base_url.host or ""
    
    # Validate parameters
    start_page = max(1, start_page)
    max_pages = max(1, min(max_pages, 20))
    per_page_limit = max(0, min(per_page_limit, 200))
    max_items = max(1, min(max_items, 1000))
    
    # Check quota
    if current_user:
        await check_rate_limit(current_user, db)
    
    try:
        items = await _crawl_dispatch(
            str(req.base_url),
            platform,
            start_page,
            max_pages,
            per_page_limit,
            max_items,
        )
        response_time = time.time() - start_time
        
        # Log success
        await log_request(db, current_user, str(req.base_url), platform, "crawl", True, 200, None, response_time, False, request)
        
        return [ListItem(**it) for it in items]
    except httpx.HTTPStatusError as e:
        response_time = time.time() - start_time
        await log_request(db, current_user, str(req.base_url), platform, "crawl", False, e.response.status_code, str(e), response_time, False, request)
        raise HTTPException(status_code=e.response.status_code, detail="Upstream returned error") from e
    except Exception as e:
        response_time = time.time() - start_time
        await log_request(db, current_user, str(req.base_url), platform, "crawl", False, 502, str(e), response_time, False, request)
        raise HTTPException(status_code=502, detail="Failed to fetch url") from e


# ==================== HLS Proxy Endpoints ====================

@app.get("/api/hls/proxy", tags=["HLS Proxy"])
async def hls_proxy_endpoint(
    url: str = Query(..., description="URL of the HLS playlist or segment to proxy"),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Proxy HLS video streams to bypass IP restrictions"""
    if not settings.HLS_PROXY_ENABLED:
        raise HTTPException(status_code=503, detail="HLS proxy is disabled")
    
    # For M3U8 playlists
    if ".m3u8" in url or "m3u8" in url:
        # Get the base proxy URL for rewriting
        base_proxy_url = "/api/hls/proxy"
        modified_playlist = await hls_proxy.proxy_m3u8(url, base_proxy_url)
        return Response(content=modified_playlist, media_type="application/vnd.apple.mpegurl")
    
    # For TS segments or other files
    return await hls_proxy.stream_segment(url)


# ==================== Admin Endpoints ====================

@app.get("/admin/stats", response_model=UsageStats, tags=["Admin"])
async def get_usage_stats(
    current_admin: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get API usage statistics (admin only)"""
    # Get today's stats
    today = datetime.utcnow().date()
    result = await db.execute(
        select(APIStats).filter(func.date(APIStats.date) == today)
    )
    stats = result.scalar_one_or_none()
    
    if not stats:
        # Return empty stats
        return UsageStats(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            scrape_requests=0,
            list_requests=0,
            crawl_requests=0,
            unique_users=0,
        )
    
    return UsageStats(
        total_requests=stats.total_requests,
        successful_requests=stats.successful_requests,
        failed_requests=stats.failed_requests,
        scrape_requests=stats.scrape_requests,
        list_requests=stats.list_requests,
        crawl_requests=stats.crawl_requests,
        unique_users=stats.unique_users,
        cache_hit_rate=stats.cache_hit_rate,
        avg_response_time=stats.avg_response_time,
    )


@app.get("/admin/users", response_model=list[UserResponse], tags=["Admin"])
async def list_users(
    current_admin: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all users (admin only)"""
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users


@app.post("/admin/users/{user_id}/quota", response_model=UserResponse, tags=["Admin"])
async def update_user_quota(
    user_id: int,
    quota_update: UpdateQuota,
    current_admin: User = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update user's daily quota (admin only)"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.daily_quota = quota_update.daily_quota
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Admin {current_admin.email} updated quota for user {user.email} to {quota_update.daily_quota}")
    return user


@app.post("/admin/cache/clear", tags=["Admin"])
async def clear_cache(
    current_admin: User = Depends(get_current_active_admin),
    pattern: str = "*"
):
    """Clear cache (admin only)"""
    cleared = await cache.clear(pattern)
    logger.info(f"Admin {current_admin.email} cleared cache (pattern: {pattern}, keys: {cleared})")
    return {"message": f"Cleared {cleared} cache keys", "pattern": pattern}
