import ast
from models import ExecuteToolInput, ToolCallResult, ParseFunctionCallInput, ParseFunctionCallOutput

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

def parse_function_call(input: ParseFunctionCallInput) -> ParseFunctionCallOutput: 
    """Parses FUNCTION_CALL string into tool name and arguments."""
    response = input.response
    try:
        if not response.startswith("FUNCTION_CALL:"):
            raise ValueError("Not a valid FUNCTION_CALL")

        _, function_info = response.split(":", 1)
        parts = [p.strip() for p in function_info.split("|")]
        func_name, param_parts = parts[0], parts[1:]

        result = {}
        for part in param_parts:
            if "=" not in part:
                raise ValueError(f"Invalid param: {part}")
            key, value = part.split("=", 1)

            try:
                parsed_value = ast.literal_eval(value)
            except Exception:
                parsed_value = value.strip()

            # Handle nested keys
            keys = key.split(".")
            current = result
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = parsed_value

        log("parser", f"Parsed: {func_name} → {result}")
        return ParseFunctionCallOutput(output=(func_name, result))

    except Exception as e:
        log("parser", f"❌ Failed to parse FUNCTION_CALL: {e}")
        raise


async def execute_tool(input: ExecuteToolInput) -> ToolCallResult:
    """Executes a FUNCTION_CALL via MCP tool session."""
    session = input.session
    tools = input.tools
    response = input.response
    try:
        parse_output = parse_function_call(ParseFunctionCallInput(response=response))
        tool_name, arguments = parse_output.output
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registered tools")

        log("tool", f"⚙️ Calling '{tool_name}' with: {arguments}")
        result = await session.call_tool(tool_name, arguments=arguments)

        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                out = [getattr(item, 'text', str(item)) for item in result.content]
            else:
                out = getattr(result.content, 'text', str(result.content))
        else:
            out = str(result)

        log("tool", f"✅ {tool_name} result: {out}")
        return ToolCallResult(
            tool_name=tool_name,
            arguments=arguments,
            result=out,
            raw_response=result
        )

    except Exception as e:
        log("tool", f"⚠️ Execution failed for '{response}': {e}")
        raise
