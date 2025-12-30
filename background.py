from datetime import datetime
import uuid
import asyncio
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal as async_session_factory
from models import Job
import xhamster
import masa49
import xnxx
import xvideos

class JobManager:
    @staticmethod
    async def create_job(user_id: int | None, job_type: str, params: dict) -> str:
        """Create a new job record and return the job_id"""
        job_uuid = str(uuid.uuid4())
        
        async with async_session_factory() as session:
            new_job = Job(
                job_id=job_uuid,
                user_id=user_id,
                job_type=job_type,
                parameters=params,
                status="pending",
                progress=0,
                created_at=datetime.utcnow()
            )
            session.add(new_job)
            await session.commit()
            
        return job_uuid

    @staticmethod
    async def run_crawl_task(job_uuid: str):
        """Background task entry point"""
        async with async_session_factory() as session:
            query = select(Job).where(Job.job_id == job_uuid)
            result = await session.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                print(f"Job {job_uuid} not found during execution")
                return

            try:
                # Update status to running
                job.status = "running"
                job.started_at = datetime.utcnow()
                await session.commit()
                
                # Extract params
                params = job.parameters
                base_url = params.get("base_url")
                max_pages = params.get("max_pages", 5)
                max_items = params.get("max_items", 100)
                
                # Logic directly from main.py's crawl structure
                # We replicate dispatch here to avoid circular imports with main.py
                host = ""
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    host = (parsed.netloc or "").lower()
                except:
                    pass

                all_items = []
                page = 1
                
                # Determine which scraper to use
                scraper_module = None
                if xhamster.can_handle(host):
                    scraper_module = xhamster
                elif masa49.can_handle(host):
                    scraper_module = masa49
                elif xnxx.can_handle(host):
                    scraper_module = xnxx
                elif xvideos.can_handle(host):
                    scraper_module = xvideos
                
                if not scraper_module:
                    raise ValueError(f"Unsupported host: {host}")

                while len(all_items) < max_items and page <= max_pages:
                    # Fetch page
                    # Note: list_videos returns dicts usually in these modules
                    items = await scraper_module.list_videos(base_url=base_url, page=page, limit=20)
                    
                    if not items:
                        break
                        
                    all_items.extend(items)
                    
                    # Update progress
                    current_progress = int((page / max_pages) * 100)
                    job.progress = min(current_progress, 99)
                    job.items_processed = len(all_items)
                    # We commit periodically to show progress
                    await session.commit()
                    
                    page += 1
                    await asyncio.sleep(1) # Be nice to the upstream server

                # Complete
                job.status = "completed"
                job.progress = 100
                job.completed_at = datetime.utcnow()
                job.result = all_items[:max_items] # Store result (careful with size!)
                job.items_processed = len(job.result)
                await session.commit()

            except Exception as e:
                print(f"Job {job_uuid} failed: {e}")
                job.status = "failed"
                job.error = str(e)
                job.completed_at = datetime.utcnow()
                await session.commit()

# Global instance not strictly needed as methods are static, but for consistency:
job_manager = JobManager()
