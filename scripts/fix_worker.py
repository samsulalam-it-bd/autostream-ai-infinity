path = r"f:\autostream-ai\backend\app\worker.py"
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'raise RuntimeError("No Drive folder assigned to this Instagram account' in line:
        new_lines.append('                        ig_folder_id = "" # Fixed by AI\n')
    elif 'ig_folder_id = settings.GOOGLE_DRIVE_PUBLIC_FOLDER_ID' in line:
        continue
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("File updated successfully.")
