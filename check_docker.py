import subprocess

def run():
    result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    
    with open("docker_status.txt", "w") as f:
        f.write("=== DOCKER PS ===\n")
        f.write(result.stdout)
        
    result = subprocess.run(["docker", "logs", "--tail", "50", "autostream-ai-frontend-1"], capture_output=True, text=True)
    with open("docker_status.txt", "a") as f:
        f.write("\n=== DOCKER LOGS ===\n")
        f.write(result.stdout)
        f.write(result.stderr)

if __name__ == "__main__":
    run()
