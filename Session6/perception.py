import os
from dotenv import load_dotenv
import google.generativeai as genai
import re
from models import PerceptionInput, PerceptionResult

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def extract_perception(input: PerceptionInput) -> PerceptionResult:
    """Extracts intent and entities using LLM"""
    user_input = input.user_input
    prompt = f"""
You are an AI that extracts structured facts from user input.

Input: "{user_input}"

Return the response as a Python dictionary with keys:
- intent: (brief phrase about what the user wants)
- entities: a list of strings representing keywords or values (e.g., ["INDIA", "ASCII"])

Output only the dictionary on a single line. Do NOT wrap it in ```json or other formatting. Ensure `entities` is a list of strings, not a dictionary.
    """

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        log("perception", f"LLM output: {raw}")

        # Strip Markdown backticks if present
        clean = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()

        try:
            parsed = eval(clean)
        except Exception as e:
            log("perception", f"⚠️ Failed to parse cleaned output: {e}")
            raise

        # # Fix common issues
        # if isinstance(parsed.get("entities"), dict):
        #     parsed["entities"] = list(parsed["entities"].values())

        return PerceptionResult(user_input=user_input, **parsed)

    except Exception as e:
        log("perception", f"⚠️ Extraction failed: {e}")
        return PerceptionResult(user_input=user_input)
