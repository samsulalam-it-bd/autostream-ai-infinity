import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.database import get_db
from app.models.models import CommentRule, CommentLog, Account, SystemSettings, ApiKeyVault
from app.schemas import CommentRuleCreate, CommentRuleOut, CommentLogOut
from app.services.ai_responder import generate_comment_reply, post_reply_to_meta, send_dm_to_meta_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comments", tags=["Audience Engagement"])


@router.get("/rules", response_model=List[CommentRuleOut])
async def get_comment_rules(db: AsyncSession = Depends(get_db)):
    """Fetch all configured comment rules."""
    result = await db.execute(select(CommentRule))
    rules = result.scalars().all()
    return rules


@router.post("/rules", response_model=CommentRuleOut)
async def create_or_update_comment_rule(rule_in: CommentRuleCreate, db: AsyncSession = Depends(get_db)):
    """Create or update the comment rule for a specific account."""
    # Check if account exists
    acc = await db.get(Account, rule_in.account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if rule already exists for this account
    result = await db.execute(select(CommentRule).where(CommentRule.account_id == rule_in.account_id))
    existing_rule = result.scalar_one_or_none()

    if existing_rule:
        existing_rule.custom_keywords = rule_in.custom_keywords
        existing_rule.auto_reply_enabled = rule_in.auto_reply_enabled
        existing_rule.auto_dm_enabled = rule_in.auto_dm_enabled
        existing_rule.ai_persona = rule_in.ai_persona
        await db.commit()
        await db.refresh(existing_rule)
        return existing_rule
    else:
        new_rule = CommentRule(**rule_in.dict())
        db.add(new_rule)
        await db.commit()
        await db.refresh(new_rule)
        return new_rule


@router.delete("/rules/{rule_id}")
async def delete_comment_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a specific comment rule."""
    rule = await db.get(CommentRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "Rule deleted"}


@router.get("/logs", response_model=List[CommentLogOut])
async def get_comment_logs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Fetch recent comment engagement logs."""
    result = await db.execute(select(CommentLog).order_by(CommentLog.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/webhooks/meta")
async def verify_meta_webhook(request: Request):
    """Handle Meta Webhook verification requests."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and settings.META_WEBHOOK_VERIFY_TOKEN and token == settings.META_WEBHOOK_VERIFY_TOKEN:
            logger.info("Meta Webhook Verified Successfully.")
            return Response(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Verification Token mismatch")

@router.post("/webhooks/meta")
async def handle_meta_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle incoming Meta events (Comments)."""
    payload = await request.json()
    logger.info(f"Received Meta Webhook Payload object={payload.get('object')} entries={len(payload.get('entry', []))}")
    
    # Process "page" or "instagram" objects
    if payload.get("object") in ["page", "instagram"]:
        for entry in payload.get("entry", []):
            page_id = entry.get("id")
            for change in entry.get("changes", []):
                value = change.get("value", {})
                item = value.get("item")
                verb = value.get("verb")
                
                # Only process new comments (not edits/deletes) and ignore our own replies
                if item == "comment" and verb == "add":
                    comment_id = value.get("comment_id")
                    message = value.get("message")
                    sender_id = value.get("from", {}).get("id")
                    
                    if sender_id == page_id:
                        continue # Skip our own comments
                    
                    # 1. Find the Account associated with this Meta Page ID
                    acc_result = await db.execute(select(Account).where(Account.channel_id == page_id))
                    acc = acc_result.scalar_one_or_none()
                    from app.core.security import decrypt_token
                    token = decrypt_token(acc.encrypted_access_token) if acc else ""
                    if not acc or not token:
                        continue
                        
                    # 2. Check if a CommentRule exists for this account
                    rule_result = await db.execute(select(CommentRule).where(CommentRule.account_id == acc.id))
                    rule = rule_result.scalar_one_or_none()
                    
                    if rule and rule.auto_reply_enabled:
                        # 3. Lookup Provider preferences
                        pref_row = await db.execute(select(SystemSettings).where(SystemSettings.key == "AI_PROVIDER_COMMENTS"))
                        pref = pref_row.scalar_one_or_none()
                        provider = pref.value if pref else "gemini"

                        # 4. Lookup Custom Key如果 not gemini
                        api_key = None
                        if provider != "gemini":
                            key_row = await db.execute(select(ApiKeyVault).where(ApiKeyVault.service_name == provider))
                            key_obj = key_row.scalar_one_or_none()
                            if key_obj:
                                api_key = key_obj.credentials_json.get("api_key")

                        # 5. Use chosen AI to generate the reply
                        ai_reply = await generate_comment_reply(message, rule.ai_persona, provider=provider, api_key=api_key)
                        
                        if ai_reply:
                            # Use Account token to reply
                            from app.core.security import decrypt_token
                            try:
                                token = decrypt_token(acc.encrypted_access_token)
                            except Exception as e:
                                logger.error(f"Failed to decrypt Meta token for auto-reply: {e}")
                                continue
                            
                            # Post Reply
                            success = await post_reply_to_meta(comment_id, ai_reply, token)
                            
                            dm_sent = False
                            if rule.auto_dm_enabled:
                                dm_sent = await send_dm_to_meta_user(comment_id, f"Thanks for commenting! {ai_reply}", token, page_id)
                            
                            # 4. Log the interaction
                            log = CommentLog(
                                account_id=acc.id,
                                platform="meta",
                                comment_id=comment_id,
                                author_name=value.get("from", {}).get("name", "Unknown"),
                                comment_text=message,
                                ai_reply_text=ai_reply,
                                dm_sent=dm_sent
                            )
                            db.add(log)
                            await db.commit()

    return Response(status_code=200, content="EVENT_RECEIVED")
