import subprocess
import time

def run():
    print("Stopping frontend container...")
    subprocess.run(["docker", "compose", "stop", "frontend"], check=True)
    
    print("Removing frontend container and its anonymous volumes (-v)...")
    subprocess.run(["docker", "compose", "rm", "-f", "-v", "frontend"], check=True)
    
    print("Building frontend (using normal cache, but package.json changed so npm install will run)...")
    subprocess.run(["docker", "compose", "build", "frontend"], check=True)
    
    print("Starting frontend up...")
    subprocess.run(["docker", "compose", "up", "-d", "frontend"], check=True)
    
    print("DONE! The anonymous volume is now seeded with the new node_modules!")

if __name__ == "__main__":
    run()
