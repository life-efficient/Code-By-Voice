from pprint import pprint
from src.get_tools import get_tools
from agents import FunctionTool
from run_tool_calls import run_http_tool_call
from pydantic_model_utils import make_pydantic_model_from_schema

def generate_tool_docstring(tool):
    """
    Generate a docstring for a tool function based on its metadata.

    Args:
        tool (dict): Tool metadata, should include 'name', 'description', 'parameters', 'call' (with 'method' and 'path').

    Returns:
        str: A formatted docstring for the tool function.
    """
    name = tool.get('name', 'unknown_tool')
    desc = tool.get('description', '')
    params = tool.get('parameters', {}).get('properties', {})

    param_lines = []
    for pname, pinfo in params.items():
        param_lines.append(f"        {pname} ({pinfo.get('type', 'str')}): {pinfo.get('description', '')}")

    param_section = "\n".join(param_lines) if param_lines else "        None"

    docstring = f'''"""
{name}: {desc}

Args:
    params (dict): Dictionary of parameters for the tool. Keys:
{param_section}

Returns:
    dict or str: The response from the HTTP request.
"""'''
    print(docstring + "\n\n")
    return docstring

tools = get_tools()

generated_function_tools = []
for tool_def in tools:
    if tool_def['call']['type'] == 'http':
        ToolModel = make_pydantic_model_from_schema(tool_def['parameters'], name=tool_def['name'] + 'Params')
        async def on_invoke_tool(ctx, args: str, ToolModel=ToolModel):
            parsed = ToolModel.model_validate_json(args)
            print('tool params', parsed)
            return run_http_tool_call(tool_def, parsed)
        tool = FunctionTool(
            name=tool_def['name'],
            description=tool_def['description'],
            params_json_schema=tool_def['parameters'],
            on_invoke_tool=on_invoke_tool,
        )
        generated_function_tools.append(tool)


# def get_people_tool():
#     get_people_tool_definition = tools[0]
#     generated_function_tool = FunctionTool(
#         name=get_people_tool_definition['name'],
#         description=generate_tool_docstring(get_people_tool_definition),
#         params_json_schema=make_pydantic_model_from_tool(get_people_tool_definition).model_json_schema(),
#         on_invoke_tool=lambda ctx, args: run_http_tool_call(get_people_tool_definition, args),
#     )
#     return generated_function_tool

# def double_number(number: int):
#     """
#     Double a number.

#     Args:
#         number (int): The number to double.

#     Returns:
#         int: The doubled number.
#     """
#     return number * 2

double_number_tool_definition = {
    "name": "double_number",
    "description": "Double a number.",
    "parameters": {
        "number": {"type": "integer", "description": "The number to double."},
    }
}

# def generate_dummy_tool():
#     tool_def = double_number_tool_definition
#     # tool_def = tools[0]

#     return FunctionTool(
#         name=tool_def['name'],
#         description=generate_tool_docstring(tool_def),
#         params_json_schema=make_pydantic_model_from_tool(tool_def).model_json_schema(),
#         on_invoke_tool=lambda ctx, args: "Hello world",
#     )

# generated_function_tools.append(generate_dummy_tool())
# generated_function_tools.append(generate_double_number_tool())
pprint(generated_function_tools, indent=4)

if __name__ == "__main__":
    print(get_people_tool())