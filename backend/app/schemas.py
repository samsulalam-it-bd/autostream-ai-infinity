import uuid
from typing import Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.models import PlatformEnum, AccountStatusEnum, VideoStatusEnum


# ── Channel Groups ─────────────────────────────────────────────────────────
class ChannelGroupCreate(BaseModel):
    name: str = Field(..., max_length=255)
    platform: PlatformEnum
    description: Optional[str] = None

class ChannelGroupOut(BaseModel):
    id: uuid.UUID
    name: str
    platform: PlatformEnum
    description: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ── Scheduling ───────────────────────────────────────────────────────────────
class AccountCreate(BaseModel):
    platform: PlatformEnum
    channel_name: str = Field(..., max_length=255)
    channel_id: Optional[str] = Field(None, max_length=255)
    group_id: Optional[uuid.UUID] = None
    access_token: str
    refresh_token: Optional[str] = None
    avatar_url: Optional[str] = None
    subscriber_count: Optional[int] = 0

class AccountOut(BaseModel):
    id: uuid.UUID
    platform: PlatformEnum
    channel_name: str
    channel_id: Optional[str]
    group_id: Optional[uuid.UUID]
    status: AccountStatusEnum
    avatar_url: Optional[str]
    subscriber_count: int
    drive_folder_link: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class AccountUpdate(BaseModel):
    status: Optional[AccountStatusEnum] = None
    group_id: Optional[uuid.UUID] = None
    drive_folder_link: Optional[str] = None

class ScheduleCreate(BaseModel):
    video_id: uuid.UUID
    target_group_id: Optional[uuid.UUID] = None
    account_id: Optional[uuid.UUID] = None
    scheduled_time: datetime
    add_watermark: bool = True
    auto_comment: bool = False
    auto_comment_text: Optional[str] = None

class ScheduleOut(BaseModel):
    id: uuid.UUID
    video_id: uuid.UUID
    target_group_id: Optional[uuid.UUID]
    account_id: Optional[uuid.UUID]
    scheduled_time: datetime
    is_published: bool
    published_at: Optional[datetime]
    published_url: Optional[str]
    add_watermark: bool
    auto_comment: bool
    metadata_overrides: Optional[dict] = None
    celery_task_id: Optional[str]
    error_message: Optional[str]
    retry_count: int
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class ScheduleConfig(BaseModel):
    timezone: str
    frequency: int
    time_slots: Optional[List[str]] = None
    comment_mode: str
    manual_comment: Optional[str] = None

class EditorElement(BaseModel):
    id: str
    type: str # 'text' or 'logo'
    x: Union[float, str]
    y: Union[float, str]
    width: Union[float, str]
    height: Union[float, str]
    content: str
    color: Optional[str] = None
    bgColor: Optional[str] = None

class MetadataOverrides(BaseModel):
    mode: str
    custom_title_append: Optional[str] = None
    custom_description: Optional[str] = None
    tags: Optional[str] = None
    editor_elements: List[EditorElement] = Field(default_factory=list)
    add_watermark: Optional[bool] = False

class AutoDripRequest(BaseModel):
    # Legacy fields
    video_ids: Optional[List[uuid.UUID]] = None
    target_group_id: Optional[uuid.UUID] = None
    account_ids: Optional[List[uuid.UUID]] = None
    account_id: Optional[uuid.UUID] = None
    start_datetime: Optional[datetime] = None
    total_days: Optional[int] = 1
    interval_hours: Optional[float] = None
    add_watermark: Optional[bool] = True
    auto_comment: Optional[bool] = False
    daily_limit_per_account: Optional[int] = None
    daily_time_slots: Optional[List[str]] = None
    
    # New V2 Wizard Fields
    targets: Optional[List[uuid.UUID]] = None
    media_pool: Optional[List[uuid.UUID]] = None
    schedule_config: Optional[ScheduleConfig] = None
    metadata_overrides: Optional[MetadataOverrides] = None


# ── API Key Vault ──────────────────────────────────────────────────────────
class ApiKeyVaultOut(BaseModel):
    id: uuid.UUID
    service_name: str
    project_name: Optional[str]
    daily_usage: int
    daily_limit: int
    is_locked: bool
    unlock_time: Optional[datetime]
    lock_reason: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class MetaKeyCreate(BaseModel):
    app_name: str = Field(..., max_length=255)
    app_id: str
    app_secret: str
    access_token: str
    daily_limit: Optional[int] = 5000

class CustomKeyCreate(BaseModel):
    service_name: str = Field(..., max_length=100)
    project_name: str = Field(..., max_length=255)
    api_key: str


# ── Dashboard & Stats ──────────────────────────────────────────────────────────
class SourceVideoOut(BaseModel):
    id: uuid.UUID
    drive_file_id: str
    drive_view_link: Optional[str]
    original_filename: Optional[str]
    file_size_bytes: Optional[int]
    ai_title: Optional[str]
    ai_description: Optional[str]
    ai_tags: Optional[list]
    ai_hashtags: Optional[list]
    status: VideoStatusEnum
    error_message: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True


# ── Upload Schedule ────────────────────────────────────────────────────────




# ── System Logs ────────────────────────────────────────────────────────────
class SystemLogOut(BaseModel):
    id: uuid.UUID
    level: str
    source: Optional[str]
    message: str
    extra_data: Optional[dict]
    created_at: datetime
    class Config:
        from_attributes = True


# ── Comments & Engagement ──────────────────────────────────────────────────
class CommentRuleCreate(BaseModel):
    account_id: uuid.UUID
    custom_keywords: List[str] = Field(default_factory=list)
    auto_reply_enabled: bool = True
    auto_dm_enabled: bool = False
    ai_persona: str = "Helpful and friendly"

class CommentRuleOut(BaseModel):
    id: int
    account_id: uuid.UUID
    custom_keywords: List[str]
    auto_reply_enabled: bool
    auto_dm_enabled: bool
    ai_persona: str
    created_at: datetime
    class Config:
        from_attributes = True

class CommentLogOut(BaseModel):
    id: int
    account_id: uuid.UUID
    platform: str
    comment_id: str
    author_name: Optional[str]
    comment_text: str
    ai_reply_text: Optional[str]
    dm_sent: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ── Drive Sync ─────────────────────────────────────────────────────────────
class DriveSyncRequest(BaseModel):
    folder_link: str
    account_id: uuid.UUID


# ── Stats ──────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_uploads_today: int
    active_api_keys: int
    pending_schedules: int
    total_accounts: int
    total_videos: int
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0

