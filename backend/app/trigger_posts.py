import asyncio
import httpx

ACCOUNTS = {
    "YouTube (Fajle Rabbi)": "a7426582-2a3c-4706-bac6-a544165a3b4d",
    "Instagram (@trusted.overseas.ltd)": "9cfb547c-d1f3-41fd-92ad-03214ae247dc",
    "Facebook Reels (AutoStream AI Infinity)": "dd84348e-1450-4231-9f99-1fd8c4aecff6",
    "Facebook Images (Reya mone)": "b6af06bc-4320-4e4a-9fd7-b0ee028c5c15"
}

async def trigger_instant_post(name, acc_id):
    url = f"http://localhost:8000/api/v1/schedules/instant-post-next"
    print(f"Triggering instant post for {name} ({acc_id})...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, json={"account_id": acc_id})
            print(f"Response for {name}: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Failed to trigger for {name}: {e}")

async def main():
    for name, acc_id in ACCOUNTS.items():
        await trigger_instant_post(name, acc_id)
        await asyncio.sleep(2)  # Short delay between triggers

if __name__ == "__main__":
    asyncio.run(main())
