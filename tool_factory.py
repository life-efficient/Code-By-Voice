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
        param_lines.append(f"    {pname} ({pinfo.get('type', 'str')}): {pinfo.get('description', '')}")

    param_section = "\n".join(param_lines) if param_lines else "    None"

    docstring = f'''"""
{name}: {desc}

Args:
{param_section}

Returns:
    dict or str: The response from the HTTP request.
"""'''
    print(docstring + "\n\n")
    return docstring

from src.get_tools import get_tools
from agents.tool import function_tool
from run_tool_calls import run_http_tool_call

tools = get_tools()

generated_function_tools = []
# for tool_call_definition in tools:
#     if tool_call_definition['call']['type'] == 'http':
#         generated_function_tool = function_tool(
#             func=lambda params: run_http_tool_call(tool_call_definition, params),
#             name_override=tool_call_definition['name'],
#             description_override=generate_tool_docstring(tool_call_definition),
#             strict_mode=True,
#         )
#         generated_function_tools.append(generated_function_tool)
#     break

def get_people_tool():
    get_people_tool_definition = tools[0]
    generated_function_tool = function_tool(
        func=lambda params: run_http_tool_call(get_people_tool_definition, params),
        name_override=get_people_tool_definition['name'],
        description_override=generate_tool_docstring(get_people_tool_definition),
        strict_mode=True,
    )
    return generated_function_tool

def double_number(number: int):
    """
    Double a number.

    Args:
        number (int): The number to double.

    Returns:
        int: The doubled number.
    """
    return number * 2

def generate_dummy_tool():

    tool_def = tools[0]
    def wrapper(**parameterz):
        return run_http_tool_call(tool_def, parameterz)

    generated_function_tool = function_tool(
        func=lambda parameeters: wrapper(parameeters),
        description_override=generate_tool_docstring(tool_def),
        name_override=tool_def['name'],
        strict_mode=True,
    )
    return generated_function_tool

generated_function_tools.append(generate_dummy_tool())
print(generated_function_tools)

if __name__ == "__main__":
    print(get_people_tool())