import requests
import json

api_key = "ddc-a4f-67aacd9fef244c039646390085e90cc0"
url = "https://api.a4f.co/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "provider-7/claude-sonnet-4-20250514",
    "messages": [
        {"role": "user", "content": "Hello, are you Claude Sonnet? Just say 'Yes, I am Claude Sonnet!' if you are."}
    ]
}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Request failed: {e}")
