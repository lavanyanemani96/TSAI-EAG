from models import GeneratePlanInput, GeneratePlanOutput
import google.generativeai as genai
import os
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

def generate_plan(input: GeneratePlanInput) -> GeneratePlanOutput: 
    """Generates a plan using LLM based on structured perception and memory."""
    perception = input.perception
    memory_items = input.memory_items
    tool_descriptions = input.tool_descriptions
    
    memory_texts = memory_items or "None"

    tool_context = f"\nYou have access to the following tools:\n{tool_descriptions}" if tool_descriptions else ""

    prompt = f"""
    You are a reasoning-driven AI agent with access to tools. {tool_context}The tool descriptions include both the tool names and their required parameter names. These are the ONLY allowed names. Your job is to solve the user's request step-by-step by:"""+"""
    
    1. If using a tool, respond in this format:
        {"FUNCTION_CALL": {"TOOL_NAME": tool_name, 
                            param_name_1:  value1, 
                            param_name_2:  value2}}
    2. If the result is final, respond in this format:
        {"FINAL_ANSWER": "Final result"}
    3. If you're uncertain, a tool fails, or an answer cannot be computed reliably, explain why and stop with:
        {"ERROR": "Explanation of the issue"}"""+f"""

    Guidelines:
    - Respond using EXACTLY ONE of the formats above per step.
    - You can reference these relevant memories:
    {memory_texts}
    
    Input Summary:
    - User input: "{perception.user_input}"
    - Intent: {perception.intent}"""+"""
    
    ✅ Examples:
    {"FUNCTION_CALL": {"TOOL_NAME": "search_legal_documents", 
                        "query":  "maternity leave criteria in India"}}
    {"FUNCTION_CALL": {"TOOL_NAME": "email_result", 
                        "recipient_email":  "user@email.com", 
                        "answer": "The criteria for maternity leave in India is as follows: .."}}
    {"FINAL_ANSWER": "The criteria for maternity leave in India is as follows: ..."}
    
    IMPORTANT:
    - 🚫 Do NOT invent tools. Use only the tools listed below.
    - 📄 If the question may relate to factual knowledge, use the 'search_documents' tool to look for the answer.
    - 🤖 If the previous tool output already contains factual information, DO NOT search again. Instead, consolidate all the relevant facts (Do NOT skimp out on facts provided to the user) and respond with: {"FINAL_ANSWER": "your final answer"} 
    - ❌ Do NOT use `search_legal_documents` multiple times. 
    - ❌ Do NOT repeat function calls with the same parameters.
    - ❌ Do NOT output unstructured responses.
    - ❌ There must NOT be a comma after the last item in the JSON output object. 
    - ❌ Do NOT include ANY extra text, markers, or formatting such as: tool_code, json, function_call, or similar. 
    - ✅ Use exactly the parameter names as listed in the tool descriptions. Do NOT invent or change parameter names.
    - ✅ Only provide a FINAL_ANSWER if all parts of the user’s request are fully satisfied (for example emailing the results) and no further action is required. If any part is incomplete or uncertain, proceed with a FUNCTION_CALL instead.
    - ✅ Your output MUST be valid JSON starting directly with { at the top.
    """

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        index_of_first_brace = raw.find('{')
        index_of_last_brace = raw.rfind('}')
        if len(raw) == (index_of_last_brace+1): 
            raw = raw[index_of_first_brace:None]
        else: 
            raw = raw[index_of_first_brace:index_of_last_brace+1]
        log("plan", f"LLM output: {raw}")
        
        parsed_output = json.loads(raw)
        return GeneratePlanOutput(output=parsed_output)

    except Exception as e:
        log("plan", f"⚠️ Decision generation failed: {e}")
        return GeneratePlanOutput(output={"ERROR": f"{e}"})
