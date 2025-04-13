import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial
import json 

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

max_iterations = 10

last_response = None
iteration = 0
iteration_response = []

import warnings
import asyncio
import re

def extract_json_from_llm_response(response_text: str):
    # Remove markdown code block if present
    cleaned = re.sub(r"^```json\s*|```$", "", response_text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    return json.loads(cleaned)

# Silence asyncio subprocess cleanup error
def silence_asyncio_close_warning():
    def no_op(*args, **kwargs): pass
    asyncio.base_subprocess.BaseSubprocessTransport.__del__ = no_op

silence_asyncio_close_warning()

async def generate_with_timeout(prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:

                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                    print(tools_description)
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a mathematical reasoning agent that solves problems step by step. You have access to various mathematical tools.

Available tools:
{tools_description}""" + """
Your behavior must follow these rules:
- You must reason step-by-step before taking any action.
- Before calling a function, **verify that all inputs are present and logically valid**.
- In every REASONING field, **include a reasoning type tag** such as [arithmetic], [logic], [tool-use], [visual], or [error].
- If any step fails due to uncertainty or missing/invalid input, **call `report_error`** with a helpful message and do not proceed further.
- After all calculations, **email the result and display it in Pinta** by emailing results and then opening Pinta, drawing a rectangle in Pinta, and writing the answer as text inside it.


You must respond with EXACTLY ONE line in the following format (no additional text), structured as JSON:
1. For function calls:
   {
     "FUNCTION_CALL": {
       "FUNCTION_NAME": {
         "ARGUMENT_1": VALUE_ARGUMENT_1,
         "ARGUMENT_2": VALUE_ARGUMENT_2
       }
     },
     "REASONING": "[reasoning_type] Step X. explanation of what this function does, validation of inputs, and why it's appropriate to call."
   }

2. For error handling:
   {
     "FUNCTION_CALL": {
       "report_error": {
         "message": "Description of the problem or missing information."
       }
     },
     "REASONING": "[error] explanation of why the error was triggered."
   }

3. For finishing the job:
   {
     "FINISHED_JOB": [boolean],
     "REASONING": "[logic] Final validation that all steps were completed and results were successfully delivered."
   }

Examples:
- {"FUNCTION_CALL": {"add": {"a":5, "b":3}}, 
   "REASONING": "[arithmetic] Step 1. Adding a=5 and b=3. Both are valid integers."}

- {"FUNCTION_CALL": {"email_result": {"result":8}}, 
   "REASONING": "[tool-use] Step 2. Emailing result=8, confirmed to be a valid numeric output from previous step."}

- {"FUNCTION_CALL": {"open_pinta": null}, 
   "REASONING": "[tool-use] Step 3. Opening Pinta to begin visual display of the result."}

- {"FUNCTION_CALL": {"draw_rectangle_in_pinta": null}, 
   "REASONING": "[visual] Step 4. Drawing a rectangle to hold the result display area."}

- {"FUNCTION_CALL": {"add_text_in_pinta": {"text":1140}}, 
   "REASONING": "[visual] Step 5. Writing final result '1140' into the rectangle at the correct location."}

- {"FUNCTION_CALL": {"report_error": {"message": "Missing value for 'b' in add operation."}}, 
   "REASONING": "[error] Cannot perform addition because 'b' is undefined."}

- {"FINISHED_JOB": true, 
   "REASONING": "[logic] All steps completed successfully, ending task."}

Note in relation to displaying results on Pinta:
1. Open pinta
2. Draw rectangle in pinta
3. Add text in pinta
"""

                # query = """Find the ASCII values of characters in INDIA and then display the sum of exponentials of those values. """
                query = """Find the ASCII values of characters in 'INDIA'. Calculate the sum of their exponentials."""
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(prompt)
                        response_text = response.text.strip() 
                        response_json = extract_json_from_llm_response(response_text)     
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break
                    
                    if "FINISHED_JOB" in response_json.keys():
                        break 

                    if "REASONING" in response_json.keys(): 
                        result_reasoning = await session.call_tool("show_reasoning", arguments={"reasoning":response_json["REASONING"]})
                        
                    if "FUNCTION_CALL" in response_json.keys():
                        func_name = list(response_json["FUNCTION_CALL"].keys())[0]
                        arguments_func = response_json["FUNCTION_CALL"][func_name]
                        
                        print("FUNC_NAME, ARGUMNETS_FUNC", func_name, arguments_func)
                        
                        result = await session.call_tool(func_name, arguments=arguments_func)
                        
                        # Get the full result content
                        if hasattr(result, 'content'):
                            if isinstance(result.content, list):
                                iteration_result = [
                                    item.text if hasattr(item, 'text') else str(item)
                                    for item in result.content
                                ]
                            else:
                                iteration_result = str(result.content)
                        else:
                            print(f"DEBUG: Result has no content attribute")
                            iteration_result = str(result)
                                                    
                        # Format the response based on result type
                        if isinstance(iteration_result, list):
                            result_str = f"[{', '.join(iteration_result)}]"
                        else:
                            result_str = str(iteration_result)
                                                
                        iteration_response.append(
                            f"In the {iteration + 1} iteration you called {func_name} with {arguments_func} parameters, "
                            f"and the function returned {result_str}."
                        )
                        print(f"{iteration_response=}")
                        last_response = iteration_result
                    
                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
