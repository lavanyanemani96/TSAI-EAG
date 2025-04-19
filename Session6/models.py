from pydantic import BaseModel
from typing import List, Any, Dict, Optional, Union
from pydantic import BaseModel
from mcp import ClientSession


# Input/Output models for perception
class PerceptionInput(BaseModel):
    user_input: str

class PerceptionResult(BaseModel):
    user_input: str
    intent: Optional[str]
    entities: List[str] = []

# Input/Output models for memory
class MemoryInput(BaseModel):
    iteration: int
    function_name: str
    arguments: Dict[str, Any]
    result: Any

class MemoryOutput(BaseModel):
    result: str

# Input/Output models for tools
class AddInput(BaseModel):
    a: int
    b: int

class AddOutput(BaseModel):
    result: int

class SqrtInput(BaseModel):
    a: int

class SqrtOutput(BaseModel):
    result: float

class StringsToIntsInput(BaseModel):
    string: str

class StringsToIntsOutput(BaseModel):
    ascii_values: List[int]

class ExpSumInput(BaseModel):
    int_list: List[int]

class ExpSumOutput(BaseModel):
    result: float

class AddListInput(BaseModel): 
    l: List[float]

class AddListOutput(BaseModel): 
    result: float
    
class FibonacciNumbersInput(BaseModel): 
    n: int
    
class FibonacciNumbersOutput(BaseModel): 
    l: List[int]
    
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
    output: str

# Input/Output models for action
class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any

class ExecuteToolInput(BaseModel): 
    session: Any
    tools: list[Any]
    response: str
    
class ParseFunctionCallInput(BaseModel):
    response: str

class ParseFunctionCallOutput(BaseModel):
    output: tuple[str, Dict[str, Any]]
    