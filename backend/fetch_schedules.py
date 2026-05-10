import urllib.request
import json
import sys

try:
    req = urllib.request.Request("http://localhost:8000/api/v1/schedules/")
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        
        # Sort by creation time desc and take top 5
        schedules = sorted(data, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        with open("latest_schedules.json", "w") as f:
            json.dump(schedules, f, indent=2)
            
        print("Successfully fetched schedules from API.")
except Exception as e:
    with open("latest_schedules.json", "w") as f:
        f.write(f"API Error: {str(e)}")
    print(f"Failed to fetch: {e}")
