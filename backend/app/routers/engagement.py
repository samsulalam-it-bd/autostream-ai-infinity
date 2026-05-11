from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import asyncio
import json

from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.api_rotation import get_active_api_key, report_quota_exceeded, increment_usage
from app.services.ai_responder import generate_comment_reply, _gemini_generate_sync
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/engagement", tags=["AI Assistant"])

class ChatRequest(BaseModel):
    message: str
    persona: Optional[str] = "Helpful social media strategist"
    provider: Optional[str] = "gemini"

class QuickGenRequest(BaseModel):
    topic: str
    platform: str
    style: str = "Viral"

@router.post("/chat")
async def ai_chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """General AI chat for generating content ideas."""
    try:
        reply = await generate_comment_reply(req.message, req.persona, provider=req.provider, db=db)
        if not reply:
            return {"reply": "I'm sorry, I couldn't generate a response right now. Please try again."}
        return {"reply": reply}
    except Exception as e:
        logger.error(f"AI Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quick-gen")
async def quick_generate(req: QuickGenRequest, db: AsyncSession = Depends(get_db)):
    """Generate title, tags, description based on topic using real AI."""
    try:
        prompt = f"""Generate viral social media metadata for a video.
Topic: {req.topic}
Platform: {req.platform}
Style: {req.style}

Return ONLY a valid JSON object:
{{
  "title": "Clean, curiosity-driven title",
  "description": "Engaging description/caption",
  "tags": ["tag1", "tag2"],
  "hashtags": ["#hashtag1", "#hashtag2"]
}}"""
        
        # 1. Try Vault first
        vault_key = await get_active_api_key("gemini", db)
        key = vault_key.credentials_json.get("api_key") if vault_key else settings.GEMINI_API_KEY
        
        if not key:
            raise ValueError("No Gemini API key available")

        model = settings.GEMINI_MODEL or "gemini-2.0-flash"
        
        try:
            response = await asyncio.to_thread(_gemini_generate_sync, key, model, prompt)
            text = (getattr(response, "text", "") or "").strip()
            
            # 2. Cleanup JSON
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1] if lines[0].startswith("```") else lines)
                
            data = json.loads(text)
            
            # 3. Track usage
            if vault_key:
                await increment_usage(vault_key.id, db)
                
            return data
        except Exception as ai_err:
            # Handle rotation if quota hit
            err_msg = str(ai_err).lower()
            if ("429" in err_msg or "quota" in err_msg):
                key_to_lock = vault_key.id if vault_key else "00000000-0000-0000-0000-000000000001"
                await report_quota_exceeded(key_to_lock, db, reason="QuickGen 429")
            raise ai_err
    except Exception as e:
        logger.error(f"Quick Gen failed: {e}")
        # Fallback to a template if AI fails
        return {
            "title": f"Amazing {req.topic} Video!",
            "description": f"Check out our latest content about {req.topic}.",
            "tags": [req.topic, "viral"],
            "hashtags": [f"#{req.topic.replace(' ', '')}", "#trending"]
        }
