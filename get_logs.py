import subprocess

try:
    with open("backend_logs.txt", "w") as f:
        subprocess.run(["docker", "logs", "--tail", "100", "autostream-ai-backend-1"], stdout=f, stderr=subprocess.STDOUT, timeout=10)
    print("Logs extracted.")
except Exception as e:
    with open("backend_logs.txt", "w") as f:
        f.write(str(e))
    print("Failed.", e)
