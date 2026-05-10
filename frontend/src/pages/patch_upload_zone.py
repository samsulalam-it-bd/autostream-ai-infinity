import re
from pathlib import Path

target_file = Path(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\UploadZone.jsx")
new_render_file = Path(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\new_UploadZone_render.jsx")

content = target_file.read_text(encoding="utf-8")
new_render_content = new_render_file.read_text(encoding="utf-8")

# Handle Windows newlines
content = content.replace('\r\n', '\n')

# 1. Add currentStep to useState declarations
if "const [currentStep, setCurrentStep] = useState(1)" not in content:
    content = content.replace(
        "const [targetGroupId, setTargetGroupId] = useState('')              // group",
        "const [targetGroupId, setTargetGroupId] = useState('')              // group\n    const [currentStep, setCurrentStep] = useState(1)"
    )

# 2. Add currentStep to MODE_TABS if it was replaced or add it properly
search_pattern = r"    return \(\n        <div className=\"space-y-6\">\n            <Toast"
match = re.search(search_pattern, content)

if match:
    old_render_start = match.start()
    content = content[:old_render_start] + new_render_content
    target_file.write_text(content, encoding="utf-8")
    print("Successfully patched UploadZone.jsx!")
else:
    print("Could not find the return statement to replace.")
