import requests

payload = {
    "targets": ["8ff3cf7f-5839-4cc6-8468-060e487872e6"],
    "media_pool": ["d995967c-adbc-4857-afbe-e221b9cb3f50"],
    "schedule_config": {
        "timezone": "Asia/Dhaka",
        "frequency": 1,
        "time_slots": None,
        "comment_mode": "auto",
        "manual_comment": ""
    },
    "metadata_overrides": {
        "mode": "auto",
        "custom_title_append": "",
        "custom_description": "",
        "tags": "",
        "editor_elements": [],
        "add_watermark": False
    }
}

try:
    res = requests.post("http://localhost:8000/api/v1/schedules/auto-drip", json=payload)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
except Exception as e:
    print("ERROR:", e)
