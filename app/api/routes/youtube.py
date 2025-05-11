from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.db.database import get_db
from app.models.database import OutputFormat, ProcessingMode, User, Video
from app.services.youtube import YouTubeService, YouTubeProcessingJob
from app.services.auth import get_current_active_user, validate_api_key
from app.services.subscription import SubscriptionService

router = APIRouter(prefix="/youtube", tags=["youtube"])

# Initialize services
youtube_service = YouTubeService()

@router.post("/process/{video_id}")
async def process_youtube_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    mode: str = Query("simple", description="Processing mode: simple or detailed"),
    output_format: str = Query("step_by_step", description="Output format: bullet_points, summary, step_by_step, or podcast_article"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process a YouTube video with specified mode and output format.
    
    Args:
        video_id: YouTube video ID
        mode: Processing mode (simple or detailed)
        output_format: Output format for the processed content
    """
    # For development, we'll just return a mock response
    return {
        "job_id": "dev_job_123",
        "video_id": video_id,
        "status": "processing",
        "mode": mode,
        "output_format": output_format
    }

@router.get("/status/{job_id}")
async def get_processing_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the status of a processing job."""
    # For development, we'll just return a mock response
    return {
        "job_id": job_id,
        "status": "processing",
        "progress": 0.5,
        "created_at": "2025-05-11T12:00:00Z"
    }

@router.get("/result/{video_id}")
async def get_video_result(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the processed result for a video."""
    # For development, we'll just return a mock response
    return {
        "video_id": video_id,
        "title": "Sample Video",
        "output_format": "step_by_step",
        "content": {
            "type": "step_by_step",
            "sections": [
                {
                    "title": "Introduction",
                    "steps": ["Step 1: Getting started", "Step 2: Understanding the basics"]
                },
                {
                    "title": "Main Content",
                    "steps": ["Step 3: Detailed explanation", "Step 4: Examples"]
                }
            ]
        }
    }

@router.get("/status")
async def youtube_status():
    return {"status": "YouTube routes are working"}

@router.post("/api/process/{video_id}")
async def api_process_youtube_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    mode: ProcessingMode = Query(
        ProcessingMode.DETAILED,
        description="Processing mode: simple or detailed"
    ),
    output_format: OutputFormat = Query(
        OutputFormat.STEP_BY_STEP,
        description="Output format: bullet_points, summary, step_by_step, or podcast_article"
    ),
    api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """API endpoint for processing a YouTube video."""
    # Validate API key and get user
    user = await validate_api_key(api_key, db)
    
    # Validate subscription permissions
    await SubscriptionService.validate_processing_request(db, user.id, mode, output_format)
    
    # Create video entry in database
    db_video = await youtube_service.create_video_db_entry(
        db, user.id, video_id, mode, output_format
    )
    
    # Create processing job
    job = await youtube_service.create_processing_job(db, db_video.id, mode, output_format)
    
    # Process in background
    processing_job = await YouTubeProcessingJob.get_job(db, job.job_id)
    background_tasks.add_task(processing_job.process)
    
    # Increment usage quota
    await SubscriptionService.increment_usage(db, user.id)
    
    return {
        "job_id": job.job_id,
        "video_id": video_id,
        "status": "processing",
        "mode": mode.value,
        "output_format": output_format.value
    }

@router.get("/status/{job_id}")
async def get_processing_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the status of a processing job."""
    try:
        # Get job from database
        job = db.query(YouTubeProcessingJob).filter(
            YouTubeProcessingJob.job_id == job_id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job belongs to user
        video = db.query(Video).filter(Video.id == job.video_id).first()
        if not video or video.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
        # Get processing job
        processing_job = await YouTubeProcessingJob.get_job(db, job_id)
        
        return {
            "job_id": job_id,
            "video_id": video.video_id,
            "status": processing_job.job.status,
            "progress": processing_job.job.progress,
            "error": processing_job.job.error,
            "mode": processing_job.job.mode.value,
            "output_format": processing_job.job.output_format.value,
            "created_at": processing_job.job.created_at,
            "completed_at": processing_job.job.completed_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/api/status/{job_id}")
async def api_get_processing_status(
    job_id: str,
    api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """API endpoint to get the status of a processing job."""
    # Validate API key and get user
    user = await validate_api_key(api_key, db)
    
    try:
        # Get job from database
        job = db.query(YouTubeProcessingJob).filter(
            YouTubeProcessingJob.job_id == job_id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job belongs to user
        video = db.query(Video).filter(Video.id == job.video_id).first()
        if not video or video.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
        # Get processing job
        processing_job = await YouTubeProcessingJob.get_job(db, job_id)
        
        return {
            "job_id": job_id,
            "video_id": video.video_id,
            "status": processing_job.job.status,
            "progress": processing_job.job.progress,
            "error": processing_job.job.error,
            "mode": processing_job.job.mode.value,
            "output_format": processing_job.job.output_format.value,
            "created_at": processing_job.job.created_at,
            "completed_at": processing_job.job.completed_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/result/{video_id}")
async def get_video_result(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get the processed result for a video."""
    try:
        # Get video from database
        video = db.query(Video).filter(
            Video.video_id == video_id,
            Video.user_id == current_user.id
        ).first()
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check if processing is complete
        if video.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Video processing is not complete. Current status: {video.status}"
            )
        
        # Get latest job
        job = await YouTubeProcessingJob.get_latest_for_video(db, video.id)
        
        if not job or job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="No completed processing job found for this video"
            )
        
        return {
            "video_id": video_id,
            "title": video.title,
            "output_format": job.output_format.value,
            "content": job.result,
            "stats": {
                "input_tokens": job.input_tokens,
                "output_tokens": job.output_tokens,
                "cost": job.cost,
                "mode": job.mode.value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video result: {str(e)}"
        )

@router.get("/api/result/{video_id}")
async def api_get_video_result(
    video_id: str,
    api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """API endpoint to get the processed result for a video."""
    # Validate API key and get user
    user = await validate_api_key(api_key, db)
    
    try:
        # Get video from database
        video = db.query(Video).filter(
            Video.video_id == video_id,
            Video.user_id == user.id
        ).first()
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Check if processing is complete
        if video.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Video processing is not complete. Current status: {video.status}"
            )
        
        # Get latest job
        job = await YouTubeProcessingJob.get_latest_for_video(db, video.id)
        
        if not job or job.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="No completed processing job found for this video"
            )
        
        return {
            "video_id": video_id,
            "title": video.title,
            "output_format": job.output_format.value,
            "content": job.result,
            "stats": {
                "input_tokens": job.input_tokens,
                "output_tokens": job.output_tokens,
                "cost": job.cost,
                "mode": job.mode.value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video result: {str(e)}"
        )

@router.get("/user/videos")
async def get_user_videos(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all videos for the current user."""
    videos = db.query(Video).filter(
        Video.user_id == current_user.id
    ).order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for video in videos:
        results.append({
            "id": video.id,
            "video_id": video.video_id,
            "title": video.title,
            "status": video.status,
            "processing_mode": video.processing_mode.value,
            "output_format": video.output_format.value,
            "created_at": video.created_at,
            "updated_at": video.updated_at
        })
    
    return results

@router.delete("/video/{video_id}")
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a video and its processing jobs."""
    # Get video from database
    video = db.query(Video).filter(
        Video.video_id == video_id,
        Video.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete associated jobs
    jobs = db.query(YouTubeProcessingJob).filter(
        YouTubeProcessingJob.video_id == video.id
    ).all()
    
    for job in jobs:
        db.delete(job)
    
    # Delete video
    db.delete(video)
    db.commit()
    
    return {"message": "Video and associated jobs deleted successfully"}