from cryptography.fernet import Fernet
import os
import re

env_path = r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\.env"
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate 100% valid key
    valid_key = Fernet.generate_key().decode('utf-8')
    print("New key:", valid_key)
    
    # Replace in file
    new_content = re.sub(r'FERNET_KEY=.*', f'FERNET_KEY={valid_key}', content)
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully replaced FERNET_KEY in .env with a valid 32-byte Fernet key.")
else:
    print("Could not find .env file.")
