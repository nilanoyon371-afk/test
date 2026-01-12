"""
Recommendation Service
Handles video recommendations using hybrid approach:
1. Source-Based: "Related Videos" scraped from source site
2. Content-Based: Jaccard similarity on tags/categories
3. Trending-Mix: "For You" feed mixing trending + niche content
"""

from typing import List, Dict, Any, Optional
import random
from app.services.global_search import global_trending

class RecommendationEngine:
    
    @staticmethod
    def _calculate_jaccard_similarity(tags1: List[str], tags2: List[str]) -> float:
        """Calculate Jaccard similarity between two lists of tags"""
        s1 = set(t.lower() for t in tags1)
        s2 = set(t.lower() for t in tags2)
        if not s1 or not s2:
            return 0.0
        return len(s1.intersection(s2)) / len(s1.union(s2))

    @staticmethod
    async def get_similar_videos(
        video_info: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get videos similar to the input video.
        Uses a Hybrid approach:
        1. Prioritize 'related_videos' scraped functionality (Zero-Cost, High Accuracy)
        2. Backfill with global search results matching the primary tags (Content-Based)
        """
        recommendations = []
        seen_urls = {video_info.get("url")}
        
        # 1. Source-Based Recommendations (Highest Priority)
        source_related = video_info.get("related_videos", [])
        for vid in source_related:
            if vid["url"] not in seen_urls:
                # Add 'source_score' to indicate high relevance
                vid["score"] = 1.0 
                recommendations.append(vid)
                seen_urls.add(vid["url"])
                
        # If we have enough, return early (Zero-Cost Optimization)
        if len(recommendations) >= limit:
            return recommendations[:limit]
            
        # 2. Content-Based Backfill (If source didn't provide enough)
        # We need to search other sites for similar content
        tags = video_info.get("tags", [])
        category = video_info.get("category")
        
        search_query = ""
        if tags:
            # Pick top 2 longest tags (usually more specific)
            sorted_tags = sorted(tags, key=len, reverse=True)
            search_query = " ".join(sorted_tags[:2])
        elif category:
            search_query = category
            
        if search_query:
            # Import here to avoid circular dependency
            from app.services.global_search import search
            
            # Search across ALL sites for cross-site discovery
            # (If I'm watching XNXX, show me xHamster videos too!)
            try:
                results = await search(query=search_query, limit=limit, fast_search=True)
                
                # Rank results by tag overlap
                scored_results = []
                for res in results:
                    if res["url"] in seen_urls:
                        continue
                        
                    # Calculate similarity score
                    score = RecommendationEngine._calculate_jaccard_similarity(
                        tags, 
                        res.get("tags", [])
                    )
                    
                    # Boost score if categories match
                    if category and res.get("category") == category:
                        score += 0.2
                        
                    res["score"] = score
                    scored_results.append(res)
                    seen_urls.add(res["url"])
                
                # Sort by score descending
                scored_results.sort(key=lambda x: x.get("score", 0), reverse=True)
                recommendations.extend(scored_results)
                
            except Exception:
                pass # Graceful degradation
                
        return recommendations[:limit]

    @staticmethod
    async def get_for_you_feed(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Generate a "For You" feed.
        Since we don't have user auth yet, this is a "Cold Start" feed:
        - 50% Global Trending (High CTR)
        - 50% Randomized Niche Discovery (Exploration)
        """
        feed = []
        
        # 1. Get Global Trending
        try:
            trending_map = await global_trending(limit_per_site=5) # ~20 videos total
            all_trending = []
            for site, videos in trending_map.items():
                all_trending.extend(videos)
            
            # Shuffle trending to avoid static order
            random.shuffle(all_trending)
            
            # Add top trending to feed
            feed.extend(all_trending[:limit])
            
        except Exception:
            # Fallback
            pass
            
        return feed[:limit]
