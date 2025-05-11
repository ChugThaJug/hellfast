from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, Boolean, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class OutputFormat(enum.Enum):
    BULLET_POINTS = "bullet_points"
    SUMMARY = "summary"
    STEP_BY_STEP = "step_by_step"
    PODCAST_ARTICLE = "podcast_article"

class ProcessingMode(enum.Enum):
    SIMPLE = "simple"
    DETAILED = "detailed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=True)  # Firebase User ID
    display_name = Column(String, nullable=True)  # From Firebase profile
    photo_url = Column(String, nullable=True)  # From Firebase profile
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    videos = relationship("Video", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    api_key = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan_id = Column(String)
    status = Column(String)  # active, canceled, past_due, etc.
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional subscription metrics
    monthly_quota = Column(Integer, default=5)  # Number of videos per month
    used_quota = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="subscription")

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=True)
    status = Column(String)  # pending, processing, completed, failed
    processing_mode = Column(Enum(ProcessingMode))
    output_format = Column(Enum(OutputFormat))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing results
    chapters = Column(JSON, nullable=True)
    stats = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    jobs = relationship("ProcessingJob", back_populates="video")
    
    # Add composite unique constraint for user_id and video_id
    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='uix_user_video'),
    )

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    status = Column(String)  # pending, processing, completed, failed, cancelled
    progress = Column(Float, default=0.0)
    mode = Column(Enum(ProcessingMode))
    output_format = Column(Enum(OutputFormat))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    # Processing results
    result = Column(JSON, nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Relationships
    video = relationship("Video", back_populates="jobs")