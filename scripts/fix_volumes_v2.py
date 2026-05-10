path = r"f:\autostream-ai\docker-compose.yml"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_duplicate_volumes = False
for line in lines:
    if "volumes:" in line and ("autostream_worker" in "".join(new_lines[-20:]) or "autostream_beat" in "".join(new_lines[-20:])):
         # Check if we already added volumes:
         pass
    new_lines.append(line)

# Actually, I'll just rewrite the whole file with a cleaner approach
import yaml

with open(path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Backend
if 'volumes' not in data['services']['backend']: data['services']['backend']['volumes'] = []
v = data['services']['backend']['volumes']
if './backend/app:/app/app' not in v: v.append('./backend/app:/app/app')

# Worker
if 'volumes' not in data['services']['worker']: data['services']['worker']['volumes'] = []
v = data['services']['worker']['volumes']
if './backend/app:/app/app' not in v: v.append('./backend/app:/app/app')

# Beat
if 'volumes' not in data['services']['beat']: data['services']['beat']['volumes'] = []
v = data['services']['beat']['volumes']
if './backend/app:/app/app' not in v: v.append('./backend/app:/app/app')

with open(path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, sort_keys=False)
print("docker-compose.yml cleaned and updated.")
