from pydantic import BaseModel
from typing import List, Any, Dict, Optional, Union
from pydantic import BaseModel
from mcp import ClientSession


# Input/Output models for perception
class PerceptionInput(BaseModel):
    user_input: str

class PerceptionResult(BaseModel):
    user_input: str
    intent: str

# Input/Output models for memory
class MemoryInput(BaseModel):
    iteration: int
    function_name: str
    arguments: Dict[str, Any]
    result: Any

class MemoryOutput(BaseModel):
    result: str

# Input/Output models for tools    
class EmailResultInput(BaseModel): 
    recipient_email: str
    answer: float
    
class EmailResultOutput(BaseModel): 
    status: str

# Input/Output models for decision
class GeneratePlanInput(BaseModel): 
    perception: PerceptionResult
    memory_items: MemoryOutput
    tool_descriptions: Optional[str] = None
    
class GeneratePlanOutput(BaseModel): 
    output: Dict[str, Any]

# Input/Output models for action
class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any

class ExecuteToolInput(BaseModel): 
    session: Any
    tools: list[Any]
    response: Dict[str, Any]
    
class ParseFunctionCallInput(BaseModel):
    response: Dict[str, Any]

class ParseFunctionCallOutput(BaseModel):
    output: tuple[str, Dict[str, Any]]
    