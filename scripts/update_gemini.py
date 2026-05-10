path = r"f:\autostream-ai\backend\app\services\gemini.py"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_signature = """async def analyze_video_with_gemini(
    frame_paths: list[str],
    provider: str = "gemini",
    api_key: Optional[str] = None,
) -> dict:"""

new_content = """async def analyze_video_with_gemini(
    frame_paths: list[str],
    platform: str = "general",
    provider: str = "gemini",
    api_key: Optional[str] = None,
) -> dict:
    \"\"\"
    Use chosen AI to analyze video frames and generate viral metadata tailored for specific platforms.
    \"\"\"
    response_text = ""

    # Platform-specific prompt logic
    if platform.lower() == "youtube":
        platform_rules = \"\"\"
- Title: Catchy, curiosity-driven, max 100 chars, SEO optimized.
- Description: Detailed (200-400 words), use keywords naturally, add timestamps placeholder if needed.
- Tags: 15 relevant SEO tags, comma separated.
- Hashtags: 3 relevant hashtags.
\"\"\"
    elif platform.lower() == "instagram":
        platform_rules = \"\"\"
- Title: Very short, punchy (max 50 chars), use 1-2 emojis.
- Description: Engaging short caption (max 100 words), focus on visual hook.
- Tags: Not needed (leave empty list).
- Hashtags: 10-15 trending Instagram hashtags, including #reels #fyp.
\"\"\"
    elif platform.lower() == "facebook":
        platform_rules = \"\"\"
- Title: Engaging, emotional or relatable (max 80 chars).
- Description: Medium length (150-250 words), focus on community engagement and sharing.
- Tags: 10 general tags.
- Hashtags: 5-8 relevant hashtags.
\"\"\"
    else:
        platform_rules = \"\"\"
- Title: Clean, max 90 chars.
- Description: Natural, engaging (150-300 words).
- Tags: 10-15 relevant tags.
- Hashtags: Exactly 10 hashtags.
\"\"\"

    prompt = f\"\"\"You are a professional social media content strategist specializing in {platform.upper()}. 
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
- Return ONLY the JSON object, nothing else\"\"\""""

# We need to find the prompt part and replace it.
import re
pattern = re.compile(r"async def analyze_video_with_gemini\(.*?\).*?prompt = \"\"\"(.*?)\"\"\"", re.DOTALL)
content = pattern.sub(new_content, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("gemini.py updated via regex.")
