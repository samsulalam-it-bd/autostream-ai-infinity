import urllib.request
import json
import traceback

try:
    req = urllib.request.Request("http://localhost:8000/api/v1/accounts/")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"Total accounts fetched: {len(data)}")
        for acc in data:
            print(f"- [{acc.get('platform')}] {acc.get('channel_name')} (ID: {acc.get('channel_id')})")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
