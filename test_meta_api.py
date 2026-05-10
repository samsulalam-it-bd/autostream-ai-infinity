import urllib.request
import json

try:
    req = urllib.request.Request("http://localhost:8000/api/v1/api-vault/?service_name=meta")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"Meta Keys Found: {len(data)}")
        for key in data:
            print(f"- {key['key_label']} (Locked: {key['is_locked']})")
except Exception as e:
    print(f"Error fetching API: {e}")
