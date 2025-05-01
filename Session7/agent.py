import asyncio
import time
import os
import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from perception import extract_perception
from decision import generate_plan
from action import execute_tool
from memory import get_memory
from models import * 
import sys 

max_steps = 5

def log(stage: str, msg: str):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

async def main(user_input: str):
    try:
        print("[agent] Starting agent...")
        print(f"[agent] Current working directory: {os.getcwd()}")
        
        server_params = StdioServerParameters(
            command="python",
            args=["tools.py"],
            cwd="/home/lavanya/Downloads/Industry/TSAI/TSAI-EAG/Session7"
        )
        
        try:
            async with stdio_client(server_params) as (read, write):
                print("Connection established, creating session...")
                try:
                    async with ClientSession(read, write) as session:
                        print("[agent] Session created, initializing...")
 
                        try:
                            await session.initialize()
                            print("[agent] MCP session initialized")

                            # Your reasoning, planning, perception etc. would go here
                            tools = await session.list_tools()
                            print("Available tools:", [t.name for t in tools.tools])
                            
                            # Get available tools
                            print("Requesting tool list...")
                            tools_result = await session.list_tools()
                            tools = tools_result.tools
                            tool_descriptions = "\n".join(
                                f"- {tool.name}: {getattr(tool, 'description', 'No description')}" 
                                for tool in tools
                            )
                            log("agent", f"{len(tools)} tools loaded")
                            
                            query = user_input   
                            step = 0
                            
                            retrieved = get_memory(MemoryInput(iteration=step, function_name='', arguments={}, result=''))

                            while step < max_steps:
                                log("loop", f"Step {step + 1} started")

                                perception = extract_perception(PerceptionInput(user_input=query))
                                log("perception", f"Intent: {perception.intent}")

                                plan = generate_plan(GeneratePlanInput(perception=perception, 
                                                                       memory_items=retrieved, 
                                                                       tool_descriptions=tool_descriptions))
                                log("plan", f"Plan generated: {plan}")
                                plan_output_dict = plan.output if isinstance(plan.output, dict) else plan.output.dict()
                                if "FINAL_ANSWER" in plan_output_dict:
                                    log("agent", f'✅ FINAL RESULT: {plan_output_dict["FINAL_ANSWER"]}')
                                    break
                                
                                try:
                                    result = await execute_tool(ExecuteToolInput(session=session, tools=tools, response=plan.output))
                                    # log("tool", f"{result.tool_name} returned: {result.result}")

                                    retrieved = get_memory(MemoryInput(iteration=step, function_name=result.tool_name, arguments=result.arguments, result=result.result))
                                    query = f"Original task: {query}\nPrevious output: {result.result}\nWhat should I do next?"
                                
                                except Exception as e:
                                    log("error", f"Tool execution failed: {e}")
                                    break

                                step += 1
                
                        except Exception as e:
                            print(f"[agent] Session initialization error: {str(e)}")
                            
                except Exception as e:
                    print(f"[agent] Session creation error: {str(e)}")
                    
        except Exception as e:
            print(f"[agent] Connection error: {str(e)}")     
               
    except Exception as e:
        print(f"[agent] Overall error: {str(e)}")

    log("agent", "Agent session complete.")

if __name__ == "__main__":
    query = input("🧑 What legal advice do you require? → ")
    email_to = input("🧑 Email your answer to: → ")
    query = f"You are a law expert, your goal is to find relevant acts / judgements and inform the user about their query in a holistic manner. Provide as many relevant facts as possible. First email the answer to: {email_to}. Answer the query:{query}, in a summarized manner. "
    asyncio.run(main(query))

# query = "What are some legal considerations to keep in mind in relation to organ transplant for a foriegn national living in India?"
# query = "What is the criteria for being eligible for maternity leave in India?"
