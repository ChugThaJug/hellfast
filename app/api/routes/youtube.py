from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.db.database import get_db
from app.models.database import OutputFormat, ProcessingMode, User, Video
from app.services.youtube import YouTubeService, YouTubeProcessingJob
from app.dependencies.auth import get_current_active_user, validate_api_key
from app.services.subscription import SubscriptionService
from app.core.settings import settings

router = APIRouter(prefix="/youtube", tags=["youtube"])

# Initialize services
youtube_service = YouTubeService()

@router.post("/process/{video_id}")
async def process_youtube_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    mode: str = Query("simple", description="Processing mode: simple or detailed"),
    output_format: str = Query("step_by_step", description="Output format: bullet_points, summary, step_by_step, or podcast_article"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a YouTube video with specified mode and output format.
    
    Args:
        video_id: YouTube video ID
        mode: Processing mode (simple or detailed)
        output_format: Output format for the processed content
    """
    # Log request in development mode
    if settings.APP_ENV == "development":
        return await _process_video_dev_mode(video_id, mode, output_format, background_tasks, current_user, db)
    
    # Convert string parameters to enum values
    try:
        processing_mode = ProcessingMode(mode)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode: {mode}. Valid values are: simple, detailed"
        )
    
    try:
        output_format_enum = OutputFormat(output_format)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid output format: {output_format}. Valid values are: bullet_points, summary, step_by_step, podcast_article"
        )
    
    # Validate subscription permissions
    await SubscriptionService.validate_processing_request(
        db, current_user.id, processing_mode, output_format_enum
    )
    
    # Create video entry in database
    db_video = await youtube_service.create_video_db_entry(
        db, current_user.id, video_id, processing_mode, output_format_enum
    )
    
    # Create processing job
    job = await youtube_service.create_processing_job(
        db, db_video.id, processing_mode, output_format_enum
    )
    
    # Process in background
    processing_job = await YouTubeProcessingJob.get_job(db, job.job_id)
    background_tasks.add_task(processing_job.process)
    
    # Increment usage quota
    await SubscriptionService.increment_usage(db, current_user.id)
    
    return {
        "job_id": job.job_id,
        "video_id": video_id,
        "status": "processing",
        "mode": processing_mode.value,
        "output_format": output_format_enum.value
    }

# Special development mode handler
async def _process_video_dev_mode(
    video_id: str,
    mode: str,
    output_format: str,
    background_tasks: BackgroundTasks,
    current_user: User,
    db: Session
):
    """Development mode video processing handler with simplified validation."""
    try:
        processing_mode = ProcessingMode(mode)
    except ValueError:
        processing_mode = ProcessingMode.DETAILED if mode == "detailed" else ProcessingMode.SIMPLE
    
    try:
        output_format_enum = OutputFormat(output_format)
    except ValueError:
        output_format_enum = OutputFormat.STEP_BY_STEP
    
    # Create video entry in database
    try:
        db_video = await youtube_service.create_video_db_entry(
            db, current_user.id, video_id, processing_mode, output_format_enum
        )
        
        # Create processing job
        job = await youtube_service.create_processing_job(
            db, db_video.id, processing_mode, output_format_enum
        )
        
        # Process in background
        processing_job = await YouTubeProcessingJob.get_job(db, job.job_id)
        background_tasks.add_task(processing_job.process)
        
        return {
            "job_id": job.job_id,
            "video_id": video_id,
            "status": "processing",
            "mode": processing_mode.value,
            "output_format": output_format_enum.value,
            "development_mode": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in development mode: {str(e)}"
        )

@router.get("/job-status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the status of a processing job."""
    try:
        # Get job from database
        job = db.query(ProcessingJob).filter(
            ProcessingJob.job_id == job_id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Skip ownership check in development mode
        if settings.APP_ENV != "development":
            # Check if job belongs to user
            video = db.query(Video).filter(Video.id == job.video_id).first()
            if not video or video.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to access this job")
        
        # Get processing job
        processing_job = await YouTubeProcessingJob.get_job(db, job_id)
        
        return {
            "job_id": job_id,
            "video_id": db.query(Video).filter(Video.id == job.video_id).first().video_id,
            "status": processing_job.job.status,
            "progress": processing_job.job.progress,
            "error": processing_job.job.error,
            "mode": processing_job.job.mode.value,
            "output_format": processing_job.job.output_format.value,
            "created_at": processing_job.job.created_at.isoformat(),
            "completed_at": processing_job.job.completed_at.isoformat() if processing_job.job.completed_at else None,
            "development_mode": settings.APP_ENV == "development"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

# API endpoint with simplified header check
@router.post("/api/process/{video_id}")
async def api_process_youtube_video(
    video_id: str,
    background_tasks: BackgroundTasks,
    mode: str = Query("detailed", description="Processing mode: simple or detailed"),
    output_format: str = Query("step_by_step", description="Output format: bullet_points, summary, step_by_step, or podcast_article"),
    api_key: Optional[str] = Header(None, description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """API endpoint for processing a YouTube video."""
    # In development mode, always accept requests
    if settings.APP_ENV == "development":
        # Get demo user
        from app.services.firebase_auth import FirebaseAuthService
        user = FirebaseAuthService.create_demo_user(db)
        
        # Process without validation
        return await _process_video_dev_mode(
            video_id, mode, output_format, background_tasks, user, db
        )
    
    # In production, validate API key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required"
        )
    
    # Validate API key and get user
    user = await validate_api_key(api_key, db)
    
    # Process request normally
    return await process_youtube_video(
        video_id, background_tasks, mode, output_format, user, db
    )

# The rest of your YouTube endpoints...








@router.get("/video-result/{video_id}")
async def get_processed_video(
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

@router.get("/status")
async def youtube_status():
    """Check if YouTube routes are working."""
    return {"status": "YouTube routes are working"}


@router.get("/api/job-status/{job_id}")
async def api_get_job_status(
    job_id: str,
    api_key: str = Header(..., description="API key for authentication"),
    db: Session = Depends(get_db)
):
    """API endpoint to get the status of a processing job."""
    # Validate API key and get user
    user = await validate_api_key(api_key, db)
    
    try:
        # Get job from database
        job = db.query(ProcessingJob).filter(
            ProcessingJob.job_id == job_id
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
            "created_at": processing_job.job.created_at.isoformat(),
            "completed_at": processing_job.job.completed_at.isoformat() if processing_job.job.completed_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

@router.get("/api/video-result/{video_id}")
async def api_get_processed_video(
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
            "created_at": video.created_at.isoformat(),
            "updated_at": video.updated_at.isoformat()
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
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.video_id == video.id
    ).all()
    
    for job in jobs:
        db.delete(job)
    
    # Delete video
    db.delete(video)
    db.commit()
    
    return {"message": "Video and associated jobs deleted successfully"}