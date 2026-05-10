path = r"f:\autostream-ai\docker-compose.yml"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add volume to backend
content = content.replace("- ./scripts:/app/scripts", "- ./backend/app:/app/app\n      - ./scripts:/app/scripts")

# Add volume to worker
content = content.replace("container_name: autostream_worker\n    restart: always", "container_name: autostream_worker\n    restart: always\n    volumes:\n      - ./backend/app:/app/app")

# Add volume to beat
content = content.replace("container_name: autostream_beat\n    restart: always", "container_name: autostream_beat\n    restart: always\n    volumes:\n      - ./backend/app:/app/app")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("docker-compose.yml updated.")
