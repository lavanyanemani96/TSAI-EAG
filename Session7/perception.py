import os
import google.generativeai as genai
import re
from models import PerceptionInput, PerceptionResult
import json 

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

from dotenv import load_dotenv
load_dotenv('paths.env')

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def extract_perception(input: PerceptionInput) -> PerceptionResult:
    """Extracts intent using LLM"""
    user_input = input.user_input
    prompt = f"""
You are an legal aid expert AI that extracts structured facts from user input.

Input: "{user_input}"

Return the response as a Python dictionary with keys:
- intent: String containing brief phrase about what the user wants

Output only the dictionary on a single line. Do NOT wrap it in ```json or other formatting. 
    """+"""
    Example: {"intent": "I want to take these steps next"}
    - ❌ Do NOT include ANY extra text, markers, or formatting such as: tool_code, json, function_call, or similar. Your output MUST be valid JSON starting directly with { at the top.
    - ❌ Do NOT provide result like this: I will do this: {"intent": "I want to take these steps next"}
    - ✅ Only provide the json object {"intent": "I want to take these steps next"}"""
    
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        clean = raw.replace('```json', '').replace('```', '').strip()
        log("perception", f"LLM output: {raw}")

        try:
            parsed = json.loads(clean)
        except Exception as e:
            log("perception", f"⚠️ Failed to parse cleaned output: {e}")
            raise

        return PerceptionResult(user_input=user_input, **parsed)

    except Exception as e:
        log("perception", f"⚠️ Extraction failed: {e}")
        return PerceptionResult(user_input=user_input)
