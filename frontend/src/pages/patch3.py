import re

def patch():
    target = r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\UploadZone.jsx"
    with open(target, "r", encoding="utf-8") as f:
        content = f.read()

    with open(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\new_UploadZone_render.jsx", "r", encoding="utf-8") as f:
        new_render = f.read()

    # Add state
    if "const [currentStep, setCurrentStep] = useState(1)" not in content:
        content = content.replace(
            "const [targetGroupId, setTargetGroupId] = useState('')              // group",
            "const [targetGroupId, setTargetGroupId] = useState('')              // group\n    const [currentStep, setCurrentStep] = useState(1)"
        )

    # Use regex to match "return (" down to the end of the file.
    # Note: We assume "return (" inside the main component is the LAST "return (" at that indentation level, 
    # but to be safe we match exactly "    return (\n        <div className=\"space-y-6\">" or similar using regex.
    
    # Let's just find "    return (" and slice.
    # We know what line it's on roughly (line 437)
    
    match = re.search(r'    return \(\s*<div className="space-y-6">', content)
    if match:
        start_idx = match.start()
        new_content = content[:start_idx] + new_render + "\n}\n"
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Success!")
    else:
        print("Still didn't match!")

if __name__ == "__main__":
    patch()
