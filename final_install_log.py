import subprocess

def run():
    print("Finding frontend container name...")
    result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
    names = result.stdout.strip().split('\n')
    frontend_name = next((name for name in names if "frontend" in name), None)
    
    if not frontend_name:
        with open("install_log.txt", "w") as f:
            f.write("Frontend container not found!")
        return

    install_cmd = ["docker", "exec", frontend_name, "npm", "install", "react-rnd", "date-fns", "lodash.debounce", "lucide-react@latest"]
    
    res = subprocess.run(install_cmd, capture_output=True, text=True)
    
    with open("install_log.txt", "w") as f:
        f.write("STDOUT:\n")
        f.write(res.stdout)
        f.write("\nSTDERR:\n")
        f.write(res.stderr)
    
    subprocess.run(["docker", "restart", frontend_name], capture_output=True)

if __name__ == "__main__":
    run()
