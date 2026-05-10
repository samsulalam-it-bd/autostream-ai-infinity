import subprocess

def run():
    print("Installing react-rnd inside frontend container...")
    result = subprocess.run(
        ["docker", "compose", "exec", "frontend", "npm", "install", "react-rnd", "date-fns", "lodash.debounce", "lucide-react"],
        cwd=r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai",
        capture_output=True,
        text=True
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    print("\nRestarting frontend container...")
    subprocess.run(
        ["docker", "compose", "restart", "frontend"],
        cwd=r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai",
        capture_output=True,
        text=True
    )
    print("Done")

if __name__ == "__main__":
    run()
