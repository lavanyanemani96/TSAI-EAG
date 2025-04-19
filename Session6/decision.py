from models import GeneratePlanInput, GeneratePlanOutput
from dotenv import load_dotenv
import google.generativeai as genai
import os

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

def generate_plan(input: GeneratePlanInput) -> GeneratePlanOutput: 
    """Generates a plan using LLM based on structured perception and memory."""
    perception = input.perception
    memory_items = input.memory_items
    tool_descriptions = input.tool_descriptions
    
    memory_texts = memory_items or "None"

    tool_context = f"\nYou have access to the following tools:\n{tool_descriptions}" if tool_descriptions else ""

    prompt = f"""
    You are a reasoning-driven AI agent with access to tools. {tool_context}. Your job is to solve the user's request step-by-step by:
    
    1. If using a tool, respond in this format:
        FUNCTION_CALL: tool_name|param1=value1|param2=value2
    2. After each step, self-verify your intermediate reasoning for sanity or consistency.
    3. If the result is final, respond in this format:
        FINAL_ANSWER: [your final result]
    4. If you're uncertain, a tool fails, or an answer cannot be computed reliably, explain why and stop with:
        ERROR: [explanation of the issue]
    5. Before solving, briefly identify the reasoning type involved (e.g., arithmetic, logic, lookup, planning, classification). This helps select the right tool or reasoning approach.

    Guidelines:
    - Respond using EXACTLY ONE of the formats above per step.
    - Do NOT include extra text, explanation, or formatting.
    - Use nested keys (e.g., input.string) and square brackets for lists.
    - You can reference these relevant memories:
    {memory_texts}
    
    Input Summary:
    - User input: "{perception.user_input}"
    - Intent: {perception.intent}
    - Entities: {', '.join(perception.entities)}
    
    ✅ Examples:
    - Reasoning Type: arithmetic  
    - FUNCTION_CALL: add|a=5|b=3
    - FUNCTION_CALL: strings_to_chars_to_int|input.string=INDIA
    - FUNCTION_CALL: int_list_to_exponential_sum|input.int_list=[73,78,68,73,65]
    - FINAL_ANSWER: [42]
    """

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        log("plan", f"LLM output: {raw}")

        for line in raw.splitlines():
            if line.strip().startswith("FUNCTION_CALL:") or line.strip().startswith("FINAL_ANSWER:"):
                return GeneratePlanOutput(output=line.strip())

        return GeneratePlanOutput(output=raw.strip())

    except Exception as e:
        log("plan", f"⚠️ Decision generation failed: {e}")
        return GeneratePlanOutput(output="FINAL_ANSWER: [unknown]")
