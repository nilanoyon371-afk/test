from fastapi import APIRouter, HTTPException, Query
from app.services.recommendation import RecommendationEngine
from app.services.video_streaming import get_video_info

router = APIRouter()

@router.get("/similar", summary="Get similar videos")
async def get_similar_videos(
    url: str = Query(..., description="Source video URL to find recommendations for"),
    limit: int = 20
):
    """
    Get recommendations similar to a specific video.
    Uses hybrid engine: Scraped 'Related Videos' + Content-Based Tag Matching.
    """
    try:
        # First, we need to info about the source video (tags, category, etc.)
        # We use get_video_info which now returns 'related_videos' too!
        video_metadata = await get_video_info(url)
        
        # Pass full metadata to engine
        recommendations = await RecommendationEngine.get_similar_videos(video_metadata, limit=limit)
        
        return {
            "source_video": video_metadata["title"],
            "count": len(recommendations),
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/for-you", summary="Get 'For You' feed")
async def get_for_you_feed(limit: int = 20):
    """
    Get a personalized discovery feed.
    Currently implements 'Cold Start' logic (Trending + Random Exploration).
    """
    try:
        feed = await RecommendationEngine.get_for_you_feed(limit=limit)
        return {
            "count": len(feed),
            "feed": feed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
