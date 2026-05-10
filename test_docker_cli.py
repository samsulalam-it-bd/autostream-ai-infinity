import subprocess

print("Testing Docker CLI...")
try:
    result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
    print("STDOUT:", result.stdout[:200])
    print("STDERR:", result.stderr[:200])
    print("SUCCESS")
except subprocess.TimeoutExpired:
    print("TIMEOUT: docker info hung for 10 seconds.")
except Exception as e:
    print(f"ERROR: {e}")
