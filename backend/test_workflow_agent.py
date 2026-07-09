import asyncio
import httpx
import json

async def run_test():
    url = "http://localhost:8000/api/v1/engagement/quick-gen"
    payload = {
        "topic": "The future of Artificial Intelligence in 2026",
        "platform": "youtube",
        "style": "Viral",
        "provider": "openrouter"
    }
    
    print(f"==================================================")
    print(f" STEP 1: Sending Request to AutoStream AI Backend ")
    print(f"==================================================")
    print(f"Target URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Connecting to AI Agent (Model: Perplexity Sonar via OpenRouter)...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=60.0)
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n==================================================")
                print(f" STEP 2: AI Generated Metadata (Live Trends) ")
                print(f"==================================================")
                print(f"TITLE:       {data.get('title')}")
                print(f"DESCRIPTION: {data.get('description')}")
                print(f"TAGS:        {', '.join(data.get('tags', []))}")
                print(f"HASHTAGS:    {', '.join(data.get('hashtags', []))}")
                print(f"==================================================")
                print("TEST PASSED: Workflow successfully executed!")
            else:
                print(f"Error Response: {response.text}")
                print("TEST FAILED: Non-200 status code.")
                
        except Exception as e:
            print(f"TEST FAILED: Exception occurred - {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
