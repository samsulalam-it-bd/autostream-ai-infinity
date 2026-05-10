import urllib.request
import urllib.error

with open("api_error.txt", "w", encoding="utf-8") as f:
    try:
        req = urllib.request.Request("http://localhost:8000/api/v1/dashboard/published-history?limit=15")
        with urllib.request.urlopen(req) as response:
            f.write("SUCCESS:\n")
            f.write(response.read().decode())
    except urllib.error.HTTPError as e:
        f.write(f"ERROR {e.code}:\n")
        f.write(e.read().decode())
    except Exception as e:
        f.write(f"OTHER ERROR: {e}\n")
