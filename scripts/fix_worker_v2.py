path = r"f:\autostream-ai\backend\app\worker.py"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    
    if 'if not ig_folder_id:' in line and i + 1 < len(lines) and 'ig_folder_id = settings.GOOGLE_DRIVE_PUBLIC_FOLDER_ID' in lines[i+1]:
        new_lines.append('                    if not ig_folder_id:\n')
        new_lines.append('                        ig_folder_id = "" # Fixed by AI\n')
        skip_next = True
    elif 'if not ig_folder_id:' in line and i + 1 < len(lines) and 'raise RuntimeError("No Drive folder assigned to this Instagram account' in lines[i+1]:
        skip_next = True
        continue
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("File updated successfully.")
