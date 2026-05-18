import json
import logging
import mimetypes
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

# NOTE:
# We intentionally use the new unified Gemini SDK: `google-genai`
# (`google-generativeai` is deprecated).
def _guess_mime_type(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/jpeg"


def _gemini_generate_sync(api_key: str, model: str, contents):
    """
    Sync helper for running inside asyncio.to_thread.
    Ensures the underlying HTTP client is closed properly.
    """
    client = genai.Client(api_key=api_key)
    return client.models.generate_content(model=model, contents=contents)


# Fallback metadata in case the AI fails
def _fallback_metadata() -> dict:
    return {
        "title": "Must-Watch Video - You Won't Believe This!",
        "description": "Check out this amazing content. Don't forget to like and subscribe for more incredible videos like this one!",
        "tags": ["viral", "trending", "mustwatch", "amazing", "content", "video", "new", "2024"],
        "hashtags": ["#viral", "#trending", "#mustwatch", "#amazing", "#fyp", "#explore", "#content", "#video", "#new", "#reels"],
    }

async def analyze_video_with_gemini(
    frame_paths: list[str],
    platform: str = "general",
    provider: str = "gemini",
    api_key: Optional[str] = None,
) -> dict:
    """
    Use chosen AI to analyze video frames and generate viral metadata tailored for specific platforms.
    """
    response_text = ""

    # Platform-specific prompt logic
    if platform.lower() == "youtube":
        platform_rules = """
- Title: Catchy, curiosity-driven, max 100 chars, SEO optimized.
- Description: Detailed (200-400 words), use keywords naturally, add timestamps placeholder if needed.
- Tags: 15 relevant SEO tags, comma separated.
- Hashtags: 3 relevant hashtags.
"""
    elif platform.lower() == "instagram":
        platform_rules = """
- Title: Very short, punchy (max 50 chars), use 1-2 emojis.
- Description: Engaging short caption (max 100 words), focus on visual hook.
- Tags: Not needed (leave empty list).
- Hashtags: 10-15 trending Instagram hashtags, including #reels #fyp.
"""
    elif platform.lower() == "facebook":
        platform_rules = """
- Title: Engaging, emotional or relatable (max 80 chars).
- Description: Medium length (150-250 words), focus on community engagement and sharing.
- Tags: 10 general tags.
- Hashtags: 5-8 relevant hashtags.
"""
    else:
        platform_rules = """
- Title: Clean, max 90 chars.
- Description: Natural, engaging (150-300 words).
- Tags: 10-15 relevant tags.
- Hashtags: Exactly 10 hashtags.
"""

    prompt = f"""You are a professional social media content strategist specializing in {platform.upper()}. 
Analyze these video frames and generate viral metadata specifically for {platform.upper()}.

Return ONLY a valid JSON object (no markdown code blocks, no extra text, no explanations):

{{
  "title": "Clean, curiosity-driven title",
  "description": "Engaging description/caption",
  "tags": ["tag1", "tag2"],
  "hashtags": ["#hashtag1", "#hashtag2"]
}}

Strict Rules for {platform.upper()}:
{platform_rules}
- Return ONLY the JSON object, nothing else"""

    # --- GEMINI ---
    if provider == "gemini":
        from app.services.api_rotation import get_active_api_key, report_quota_exceeded, increment_usage
        from app.database import AsyncSessionLocal

        model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
        parts: list[object] = [prompt]
        
        # Prepare parts
        frames_added = 0
        for frame_path in frame_paths:
            if Path(frame_path).exists():
                with open(frame_path, "rb") as f:
                    image_bytes = f.read()
                parts.append(
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=_guess_mime_type(frame_path),
                    )
                )
                frames_added += 1

        if frames_added == 0:
            logger.warning("No valid frames found for Gemini analysis. Using generic metadata.")
            return _fallback_metadata()

        # Try multiple keys if needed
        async with AsyncSessionLocal() as db:
            for _retry in range(3): # Try up to 3 different keys
                vault_key = await get_active_api_key("gemini", db)
                key = vault_key.credentials_json.get("api_key") if vault_key else (api_key or settings.GEMINI_API_KEY)
                
                if not key:
                    logger.warning("No Gemini API key available in vault or config. Using fallback.")
                    return _fallback_metadata()

                try:
                    import asyncio
                    response = await asyncio.to_thread(_gemini_generate_sync, key, model_name, parts)
                    response_text = (getattr(response, "text", "") or "").strip()
                    
                    if vault_key:
                        await increment_usage(vault_key.id, db)
                    else:
                        await increment_usage("00000000-0000-0000-0000-000000000001", db)
                    
                    break # Success!
                except Exception as e:
                    err_msg = str(e).lower()
                    if "429" in err_msg or "quota" in err_msg:
                        logger.warning(f"Gemini Key Quota Exceeded. Reporting and rotating...")
                        if vault_key:
                            await report_quota_exceeded(vault_key.id, db, reason="429 Quota Exceeded")
                        continue # Try next key
                    else:
                        logger.error(f"Gemini AI analysis failed: {e}")
                        return _fallback_metadata()
            else:
                logger.error("All available Gemini keys exhausted or failed.")
                return _fallback_metadata()

    # --- GROK / OPENAI ---
    elif provider in ["grok", "openai"]:
        import httpx
        import base64
        
        base_url = "https://api.x.ai/v1/chat/completions" if provider == "grok" else "https://api.openai.com/v1/chat/completions"
        model_name = "grok-2-vision-latest" if provider == "grok" else "gpt-4o-mini"
        
        if not api_key:
            logger.warning(f"No {provider} key configured. Using fallback metadata.")
            return _fallback_metadata()

        content = [{"type": "text", "text": prompt}]
        for path in frame_paths:
            if Path(path).exists():
                with open(path, "rb") as image_file:
                    b64 = base64.b64encode(image_file.read()).decode('utf-8')
                    content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model_name, "messages": [{"role": "user", "content": content}], "max_tokens": 500}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(base_url, json=payload, headers=headers, timeout=30.0)
                res.raise_for_status()
                response_text = res.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"{provider} vision analysis failed: {e}")
            return _fallback_metadata()

    # --- ANTHROPIC ---
    elif provider == "anthropic":
        import httpx
        import base64
        
        if not api_key:
            logger.warning("No Anthropic key configured. Using fallback metadata.")
            return _fallback_metadata()

        content = []
        for path in frame_paths:
            if Path(path).exists():
                with open(path, "rb") as image_file:
                    b64 = base64.b64encode(image_file.read()).decode('utf-8')
                    content.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}
                    })
        content.append({"type": "text", "text": prompt})

        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {"model": "claude-3-haiku-20240307", "max_tokens": 500, "messages": [{"role": "user", "content": content}]}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=30.0)
                res.raise_for_status()
                response_text = res.json()["content"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Anthropic vision analysis failed: {e}")
            return _fallback_metadata()

    # --- JSON CLEANUP AND PARSE ---

    try:
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[0].startswith("```") else lines)

        metadata = json.loads(response_text)
        result = {
            "title": str(metadata.get("title", "Amazing Video You Must Watch!"))[:500],
            "description": str(metadata.get("description", "Watch this incredible video.")),
            "tags": list(metadata.get("tags", []))[:15],
            "hashtags": list(metadata.get("hashtags", []))[:10],
        }

        logger.info(f"Generated AI title [{provider}]: {result['title']}")
        return result

    except Exception as e:
        logger.error(f"AI JSON Parse failed [{provider}]: {e} | Raw: {response_text}")
        return _fallback_metadata()
