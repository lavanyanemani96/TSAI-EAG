from models import MemoryInput, MemoryOutput

def get_memory(input: MemoryInput) -> MemoryOutput:
    """Summarizes the memory for an iteration and returns a MemoryOutput object."""
    if input.iteration == 0:
        return MemoryOutput(result='')
    past_interaction = f"In the {input.iteration + 1} iteration you called {input.function_name} with {input.arguments} parameters, and the function returned {input.result}."
    return MemoryOutput(result=past_interaction)