import logging
import httpx
import asyncio
from typing import Optional
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

def _gemini_generate_sync(api_key: str, model: str, contents: str):
    with genai.Client(api_key=api_key) as client:
        return client.models.generate_content(model=model, contents=contents)

async def generate_comment_reply(comment_text: str, persona: str, provider: str = "gemini", api_key: Optional[str] = None) -> Optional[str]:
    """Use AI to generate a contextual, human-like response to a user comment."""
    
    if provider == "gemini":
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            logger.warning("No Gemini API key configured for auto-reply.")
            return None

        model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"

        prompt = f"""You are an AI responding to comments on social media (Facebook/Instagram/YouTube).
Act naturally according to the following persona/instructions: "{persona}".
Do not sound like a bot. Keep your reply concise, engaging, and relevant to the user's comment.
If the language is Bengali or English, reply in the same language or a mix of both if appropriate.

User's Comment: "{comment_text}"

Your Reply (ONLY output the exact reply text, no quotes):"""

        try:
            response = await asyncio.to_thread(_gemini_generate_sync, key, model_name, prompt)
            reply = (getattr(response, "text", "") or "").strip()
            logger.info(f"Generated Gemini Reply: {reply}")
            return reply
        except Exception as e:
            logger.error(f"Gemini AI auto-reply generation failed: {e}")
            return None

    elif provider in ["grok", "openai"]:
        base_url = "https://api.x.ai/v1/chat/completions" if provider == "grok" else "https://api.openai.com/v1/chat/completions"
        model_name = "grok-2-latest" if provider == "grok" else "gpt-4o-mini"
        if not api_key:
            logger.warning(f"No {provider} API key configured.")
            return None
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": f"You are an AI responding to comments on social media. Act naturally according to: '{persona}'. Keep your reply concise, engaging, and relevant. Only output the exact reply text."},
                {"role": "user", "content": f"User's Comment: '{comment_text}'"}
            ]
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(base_url, json=payload, headers=headers, timeout=15.0)
                res.raise_for_status()
                reply = res.json()["choices"][0]["message"]["content"].strip()
                logger.info(f"Generated {provider} Reply: {reply}")
                return reply
        except Exception as e:
            logger.error(f"{provider} auto-reply failed: {e}")
            return None

    elif provider == "anthropic":
        if not api_key:
            logger.warning("No Anthropic API key configured.")
            return None
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 150,
            "system": f"You are an AI responding to comments on social media. Act naturally according to: '{persona}'. Keep your reply concise, engaging, and relevant. Only output the exact reply text.",
            "messages": [
                {"role": "user", "content": f"User's Comment: '{comment_text}'"}
            ]
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=15.0)
                res.raise_for_status()
                reply = res.json()["content"][0]["text"].strip()
                logger.info(f"Generated Anthropic Reply: {reply}")
                return reply
        except Exception as e:
            logger.error(f"Anthropic auto-reply failed: {e}")
            return None

    return None


async def post_reply_to_meta(comment_id: str, reply_text: str, page_token: str) -> bool:
    """Post a reply to a Facebook/Instagram comment using Meta Graph API."""
    url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
    params = {
        "message": reply_text,
        "access_token": page_token
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params)
            resp.raise_for_status()
            logger.info(f"Successfully posted reply to Meta comment {comment_id}")
            return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to post Meta reply: {e.response.text if hasattr(e, 'response') else e}")
        return False


async def send_dm_to_meta_user(user_id: str, dm_text: str, page_token: str, page_id: str) -> bool:
    """Send a private message to a user who commented (Message Tags/Private Replies)."""
    # Note: Private replies require specific Graph API endpoints. 
    # Usually: POST /{page_id}/messages format with recipient id=comment_id but FB API changes often.
    url = f"https://graph.facebook.com/v19.0/{page_id}/messages"
    payload = {
        "recipient": {"comment_id": user_id}, # using comment_id as recipient for private replies
        "message": {"text": dm_text}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, params={"access_token": page_token})
            resp.raise_for_status()
            logger.info(f"Successfully sent DM to Meta user via comment {user_id}")
            return True
    except httpx.HTTPError as e:
        logger.error(f"Failed to send Meta DM: {e.response.text if hasattr(e, 'response') else e}")
        return False
