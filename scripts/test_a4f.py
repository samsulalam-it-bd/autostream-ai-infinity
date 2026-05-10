import asyncio
import os
from PIL import Image
from app.services.gemini import analyze_video_with_ai

async def test_ai():
    print("Testing A4F API with the provided key...")
    
    # Create a dummy image for testing
    img = Image.new('RGB', (100, 100), color = 'red')
    dummy_img_path = 'dummy_test.jpg'
    img.save(dummy_img_path)
    
    try:
        # Pass the dummy image
        print("Calling analyze_video_with_ai with timeout...")
        
        # Override the API key with the one provided by user (if not set in env)
        test_key = os.environ.get("A4F_API_KEY", "ddc-a4f-67aacd9fef244c039646390085e90cc0")
        
        # Use asyncio.wait_for to prevent hanging
        result = await asyncio.wait_for(
            analyze_video_with_ai([dummy_img_path], api_key=test_key),
            timeout=15.0
        )
        print("Result from A4F (gemini-2.5-flash):")
        print(result)
    except asyncio.TimeoutError:
        print("Error: The A4F API request timed out after 15 seconds! The key or endpoint might be invalid or very slow.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)

if __name__ == "__main__":
    asyncio.run(test_ai())
