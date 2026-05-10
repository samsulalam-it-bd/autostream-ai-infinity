path = r"f:\autostream-ai\docker-compose.yml"
import re

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any existing ./backend/app:/app/app to avoid duplicates
content = content.replace("      - ./backend/app:/app/app\n", "")

# Add it to backend
content = re.sub(r"(backend:.*?volumes:.*?\n)", r"\1      - ./backend/app:/app/app\n", content, flags=re.DOTALL)

# Add it to worker
content = re.sub(r"(worker:.*?volumes:.*?\n)", r"\1      - ./backend/app:/app/app\n", content, flags=re.DOTALL)

# Add it to beat
# Beat doesn't have volumes usually, so we add the section
if "beat:" in content and "volumes:" not in content.split("beat:")[1].split("frontend:")[0]:
    content = content.replace("container_name: autostream_beat\n    restart: always", "container_name: autostream_beat\n    restart: always\n    volumes:\n      - ./backend/app:/app/app")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("docker-compose.yml updated with regex.")
