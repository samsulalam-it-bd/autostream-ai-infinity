import os
import glob

files_to_remove = [
    'demo*.html', 'demo*.py', 'test_*.py', 'set_bot.py', 'fix_fernet.py', 
    'run_test.bat', '*.txt', 'backend/inject_meta.py', 'backend/test_enc.py', 
    'backend/test_keys.py'
]

count = 0
for pattern in files_to_remove:
    for filepath in glob.glob(pattern):
        try:
            os.remove(filepath)
            count += 1
            print(f"Removed: {filepath}")
        except Exception as e:
            print(f"Failed to remove {filepath}: {e}")

print(f"Total files removed: {count}")

# Remove self at the end
try:
    os.remove(__file__)
except:
    pass
