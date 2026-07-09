import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Enum, 
    ForeignKey, Text, BigInteger, JSON, Date, Float
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PlatformEnum(str, enum.Enum):
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class AccountStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    PENDING = "pending"


class VideoStatusEnum(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    PROCESSING = "processing"
    READY = "ready"
    UPLOADED = "uploaded"
    FAILED = "failed"


class MediaTypeEnum(str, enum.Enum):
    VIDEO = "video"
    IMAGE = "image"


class ChannelGroup(Base):
    __tablename__ = "channel_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    accounts = relationship("Account", back_populates="channel_group")
    upload_schedules = relationship("UploadSchedule", back_populates="target_group")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(Enum(PlatformEnum), nullable=False, index=True)
    channel_name = Column(String(255), nullable=False)
    channel_id = Column(String(255), nullable=True, index=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("channel_groups.id"), nullable=True, index=True)
    vault_id = Column(UUID(as_uuid=True), ForeignKey("api_key_vault.id"), nullable=True, index=True)
    # Tokens stored encrypted using Fernet
    encrypted_access_token = Column(Text, nullable=True)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(AccountStatusEnum), default=AccountStatusEnum.PENDING, nullable=False, index=True)
    avatar_url = Column(String(500), nullable=True)
    subscriber_count = Column(BigInteger, default=0)
    drive_folder_link = Column(String(1000), nullable=True)  # Per-account dedicated Drive folder
    automation_settings = Column(JSONB, default={}, server_default='{}')  # Full setup snapshot
    auto_comment = Column(Boolean, default=False, nullable=False)
    auto_comment_text = Column(Text, nullable=True)
    ai_time_predictor = Column(Boolean, default=False, nullable=False)
    optimal_slots = Column(JSONB, default={}, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channel_group = relationship("ChannelGroup", back_populates="accounts")
    upload_schedules = relationship("UploadSchedule", back_populates="account")
    comment_rules = relationship("CommentRule", back_populates="account")
    comment_logs = relationship("CommentLog", back_populates="account")
    analytics = relationship("ChannelAnalytics", back_populates="account", cascade="all, delete-orphan")
    api_vault_key = relationship("ApiKeyVault")


class ApiKeyVault(Base):
    __tablename__ = "api_key_vault"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False, index=True)  # google, meta, gemini
    project_name = Column(String(255), nullable=True)
    credentials_json = Column(JSONB, nullable=False)  # Stores the full GCP service account JSON
    daily_usage = Column(Integer, default=0)
    daily_limit = Column(Integer, default=10000)
    is_locked = Column(Boolean, default=False, index=True)
    unlock_time = Column(DateTime(timezone=True), nullable=True)
    lock_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SourceVideo(Base):
    __tablename__ = "source_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    drive_file_id = Column(String(255), nullable=False, unique=True)
    drive_view_link = Column(String(500), nullable=True)
    drive_download_link = Column(String(500), nullable=True)
    original_filename = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    media_type = Column(Enum(MediaTypeEnum), default=MediaTypeEnum.VIDEO, nullable=False, index=True)
    # AI-generated metadata
    ai_title = Column(String(500), nullable=True)
    ai_description = Column(Text, nullable=True)
    ai_tags = Column(JSON, nullable=True)  # list of strings
    ai_hashtags = Column(JSON, nullable=True)  # list of strings
    # Processing status
    status = Column(Enum(VideoStatusEnum), default=VideoStatusEnum.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    upload_schedules = relationship("UploadSchedule", back_populates="video", cascade="all, delete-orphan")


class UploadSchedule(Base):
    __tablename__ = "upload_schedule"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("source_videos.id"), nullable=False, index=True)
    target_group_id = Column(UUID(as_uuid=True), ForeignKey("channel_groups.id"), nullable=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True, index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    published_url = Column(String(500), nullable=True)
    add_watermark = Column(Boolean, default=True)
    auto_comment = Column(Boolean, default=False)
    auto_comment_text = Column(Text, nullable=True)
    metadata_overrides = Column(JSON, nullable=True)
    original_scheduled_time = Column(DateTime(timezone=True), nullable=True)
    is_optimized_by_ai = Column(Boolean, default=False, nullable=False)
    celery_task_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    view_count = Column(BigInteger, default=0)
    like_count = Column(BigInteger, default=0)
    comment_count = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    video = relationship("SourceVideo", back_populates="upload_schedules")
    target_group = relationship("ChannelGroup", back_populates="upload_schedules")
    account = relationship("Account", back_populates="upload_schedules")

    @property
    def media_type(self) -> str:
        if "video" in self.__dict__ and self.video:
            if hasattr(self.video, 'media_type') and self.video.media_type:
                return self.video.media_type.value
        return "VIDEO"


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), default="INFO")
    source = Column(String(100), nullable=True)  # e.g. "celery_worker", "api_rotation"
    message = Column(Text, nullable=False)
    extra_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommentRule(Base):
    __tablename__ = "comment_rules"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    custom_keywords = Column(JSON, default=list)  # e.g., ["price", "how much", "link"]
    auto_reply_enabled = Column(Boolean, default=True)
    auto_dm_enabled = Column(Boolean, default=False)
    ai_persona = Column(String, default="Helpful and friendly")  # Prompt context for Gemini
    custom_reply_text = Column(String, nullable=True)  # Static response text if supplied
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    account = relationship("Account", back_populates="comment_rules")


class CommentLog(Base):
    __tablename__ = "comment_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String, index=True) # youtube, facebook, instagram
    comment_id = Column(String, index=True, nullable=False) # ID from the platform (to prevent duplicates)
    author_name = Column(String)
    comment_text = Column(Text)
    ai_reply_text = Column(Text, nullable=True)
    dm_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    account = relationship("Account", back_populates="comment_logs")


class SystemSettings(Base):
    """Key-value store for dynamic system settings (Telegram config, notification toggles, etc.)"""
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChannelAnalytics(Base):
    __tablename__ = "channel_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    followers_count = Column(BigInteger, default=0)
    views_count = Column(BigInteger, default=0)
    likes_count = Column(BigInteger, default=0)
    engagement_rate = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    account = relationship("Account", back_populates="analytics")

