import google.generativeai as genai
import sys
import os

key = os.environ.get("GEMINI_API_KEY", "")
if not key:
    print("ERROR: GEMINI_API_KEY is not set.")
    sys.exit(1)
print("Testing Gemini API...")

try:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello! Are you Gemini? Say 'Yes, I am!' if you are.")
    
    print("\n--- Success ---")
    print(response.text)
except Exception as e:
    print(f"\n--- Error ---")
    print({e})
    sys.exit(1)
