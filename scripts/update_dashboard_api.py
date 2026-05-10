path = r"f:\autostream-ai\backend\app\routers\dashboard.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update get_dashboard_stats
old_stats = """    total_accounts = await db.execute(select(func.count(Account.id)))
    total_videos = await db.execute(select(func.count(SourceVideo.id)))

    return DashboardStats(
        total_uploads_today=uploads_today.scalar() or 0,
        active_api_keys=active_keys.scalar() or 0,
        pending_schedules=pending.scalar() or 0,
        total_accounts=total_accounts.scalar() or 0,
        total_videos=total_videos.scalar() or 0,
    )"""

new_stats = """    total_accounts = await db.execute(select(func.count(Account.id)))
    total_videos = await db.execute(select(func.count(SourceVideo.id)))
    
    # Engagement totals
    total_views = await db.execute(select(func.sum(UploadSchedule.view_count)).where(UploadSchedule.is_published == True))
    total_likes = await db.execute(select(func.sum(UploadSchedule.like_count)).where(UploadSchedule.is_published == True))
    total_comments = await db.execute(select(func.sum(UploadSchedule.comment_count)).where(UploadSchedule.is_published == True))

    return DashboardStats(
        total_uploads_today=uploads_today.scalar() or 0,
        active_api_keys=active_keys.scalar() or 0,
        pending_schedules=pending.scalar() or 0,
        total_accounts=total_accounts.scalar() or 0,
        total_videos=total_videos.scalar() or 0,
        total_views=total_views.scalar() or 0,
        total_likes=total_likes.scalar() or 0,
        total_comments=total_comments.scalar() or 0,
    )"""
content = content.replace(old_stats, new_stats)

# 2. Update get_published_history
old_history = """                "published_at": s.published_at.isoformat() if hasattr(s, "published_at") and s.published_at else None,
                "published_url": str(getattr(s, "published_url", "") or ""),
                "add_watermark": bool(getattr(s, "add_watermark", False)),
            })"""

new_history = """                "published_at": s.published_at.isoformat() if hasattr(s, "published_at") and s.published_at else None,
                "published_url": str(getattr(s, "published_url", "") or ""),
                "add_watermark": bool(getattr(s, "add_watermark", False)),
                "view_count": int(getattr(s, "view_count", 0)),
                "like_count": int(getattr(s, "like_count", 0)),
                "comment_count": int(getattr(s, "comment_count", 0)),
            })"""
content = content.replace(old_history, new_history)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("dashboard.py updated.")
