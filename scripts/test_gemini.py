import asyncio
import os
from PIL import Image
from app.services.gemini import analyze_video_with_gemini

async def test_gemini():
    print("Testing Gemini API with the provided key...")
    
    # Create a dummy image for testing
    img = Image.new('RGB', (100, 100), color = 'red')
    dummy_img_path = 'dummy_test.jpg'
    img.save(dummy_img_path)
    
    try:
        test_key = os.environ.get("GEMINI_API_KEY", "")
        if not test_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Export it or put it in your .env before testing.")
        print("Calling analyze_video_with_gemini...")
        
        # Use asyncio.wait_for to prevent hanging
        result = await asyncio.wait_for(
            analyze_video_with_gemini([dummy_img_path], api_key=test_key),
            timeout=25.0
        )
        print("Result from Gemini 1.5 Flash:")
        import json
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)

if __name__ == "__main__":
    asyncio.run(test_gemini())
