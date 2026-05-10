import subprocess

def run():
    print("Finding frontend container name...")
    result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
    names = result.stdout.strip().split('\n')
    frontend_name = next((name for name in names if "frontend" in name), None)
    
    if not frontend_name:
        print("Frontend container not found!")
        return

    print(f"Installing missing deps straight into {frontend_name}...")
    install_cmd = ["docker", "exec", frontend_name, "npm", "install", "react-rnd", "date-fns", "lodash.debounce", "lucide-react@latest"]
    
    res = subprocess.run(install_cmd, capture_output=True, text=True)
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    
    print("\nRestarting Vite container to clear cache...")
    subprocess.run(["docker", "restart", frontend_name], capture_output=True)
    print("Done!")

if __name__ == "__main__":
    run()
