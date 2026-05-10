import io
import sys

def patch():
    try:
        with open(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\UploadZone.jsx", "r", encoding="utf-8") as f:
            content = f.read()

        with open(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\new_UploadZone_render.jsx", "r", encoding="utf-8") as f:
            custom_render = f.read()

        # Step 1
        if "const [currentStep, setCurrentStep] = useState(1)" not in content:
            content = content.replace(
                "const [targetGroupId, setTargetGroupId] = useState('')              // group",
                "const [targetGroupId, setTargetGroupId] = useState('')              // group\n    const [currentStep, setCurrentStep] = useState(1)"
            )
            print("Injected useState")

        # Step 2
        split_token = '    return (\n        <div className="space-y-6">'
        if split_token not in content:
            split_token = split_token.replace('\n', '\r\n')
        
        if split_token in content:
            parts = content.split(split_token)
            new_content = parts[0] + custom_render
            with open(r"c:\Users\Got it Target\.gemini\antigravity\scratch\autostream-ai\frontend\src\pages\UploadZone.jsx", "w", encoding="utf-8") as f:
                f.write(new_content)
            print("Successfully replaced render block!")
        else:
            print("Failed to find split token. Here is a snippet around line 437:")
            lines = content.splitlines()
            for i in range(430, 445):
                print(f"{i}: {repr(lines[i])}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    patch()
