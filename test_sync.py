import httpx
import asyncio

async def main():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("http://localhost:8000/api/v1/accounts/sync-meta")
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
            
            # Now fetch all accounts
            resp2 = await client.get("http://localhost:8000/api/v1/accounts/")
            data2 = resp2.json()
            print(f"\nAll Accounts in DB: {len(data2)}")
            for a in data2:
                print(f"- [{a.get('platform')}] {a.get('channel_name')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
