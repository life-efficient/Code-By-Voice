import requests
import json
import re
from urllib.parse import urlparse

def fetch_openapi_schema(url="http://localhost:3000/api/openapi"):
    response = requests.get(url)
    response.raise_for_status()
    return response.json(), url

def extract_tool_definitions(schema, schema_url):
    tools = []
    # Determine host from OpenAPI servers or schema_url
    servers = schema.get('servers', [])
    if servers:
        host = servers[0]['url']
    else:
        parsed = urlparse(schema_url)
        host = f"{parsed.scheme}://{parsed.netloc}"
    for path, methods in schema.get('paths', {}).items():
        for method, details in methods.items():
            # Tool name: method + path, e.g., get_people_id
            name = f"{method}_{re.sub(r'[^a-zA-Z0-9]', '_', path.strip('/'))}".lower()
            summary = details.get('summary')
            description = details.get('description')
            desc = summary or description or '(No description)'
            # Build OpenAI-compatible parameters schema
            properties = {}
            required = []
            for param in details.get('parameters', []):
                param_schema = param.get('schema', {})
                pname = param.get('name')
                properties[pname] = {
                    'type': param_schema.get('type', 'string'),
                    'description': param.get('description', '')
                }
                if param.get('required', False):
                    required.append(pname)
            # Handle requestBody parameters (for POST/PATCH)
            if 'requestBody' in details:
                req_body = details['requestBody']
                content = req_body.get('content', {})
                for content_type, content_schema in content.items():
                    schema_obj = content_schema.get('schema', {})
                    properties['body'] = {
                        'type': schema_obj.get('type', 'object'),
                        'description': f"Request body ({content_type})"
                    }
                    if req_body.get('required', False):
                        required.append('body')
            param_schema = {
                'type': 'object',
                'properties': properties,
                'required': required,
                'additionalProperties': False
            }
            tools.append({
                'name': name,
                'description': desc,
                'parameters': param_schema,
                'call': {
                    'type': 'http',
                    'host': host,
                    'method': method,
                    'path': path
                }
            })
    return tools

def extract_openai_tools(tools):
    """
    Extracts only the OpenAI-ready tool definitions (name, description, parameters) from the full tool list.
    """
    return [
        {
            'type': 'function',
            'name': tool['name'],
            'description': tool['description'],
            'parameters': tool['parameters']
        }
        for tool in tools
    ]

def main():
    schema, url = fetch_openapi_schema()
    tools = extract_tool_definitions(schema, url)
    with open('tools.json', 'w') as f:
        json.dump(tools, f, indent=2)
    print(f"Extracted {len(tools)} tool definitions. See tools.json for details.")
    # Uncomment the next line to print a summary for debugging
    # print_tools_summary(tools)
    # To get OpenAI-ready tools, use: openai_tools = extract_openai_tools(tools)

def print_tools_summary(tools):
    for tool in tools:
        print(f"\n{tool['name']} ({tool['call']['type']})")
        print(f"  Description: {tool['description']}")
        print(f"  Call: {tool['call']}")
        if tool['parameters']['properties']:
            print("  Parameters:")
            for pname, pinfo in tool['parameters']['properties'].items():
                print(f"    - {pname} (type: {pinfo['type']}): {pinfo['description']}")
        else:
            print("  Parameters: None")

if __name__ == "__main__":
    main() 