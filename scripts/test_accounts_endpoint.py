import asyncio
import sys
import httpx

async def main():
    url = "http://localhost:8000/api/v1/accounts/"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                accounts = resp.json()
                for a in accounts:
                    print(f"\nAccount: {a.get('channel_name')}")
                    print(f"  Platform: {a.get('platform')}")
                    print(f"  Next Publish Time: {a.get('next_publish_time')}")
                    print(f"  Stats: {a.get('stats')}")
            else:
                print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Failed to connect to backend: {e}")

if __name__ == "__main__":
    asyncio.run(main())
