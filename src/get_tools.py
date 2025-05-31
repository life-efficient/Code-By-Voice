import requests
import json
import re

def fetch_openapi_schema(url="http://localhost:3000/api/openapi"):
    response = requests.get(url)
    response.raise_for_status()
    return response.json(), url

def resolve_ref(ref, root_schema):
    """Resolve a $ref string like '#/components/schemas/PersonUpdate'."""
    parts = ref.lstrip('#/').split('/')
    obj = root_schema
    for part in parts:
        obj = obj[part]
    return obj

def expand_refs(obj, root_schema):
    """Recursively expand $ref in a schema object."""
    if isinstance(obj, dict):
        if '$ref' in obj:
            resolved = resolve_ref(obj['$ref'], root_schema)
            # Recursively expand in case the resolved object also contains $ref
            return expand_refs(resolved, root_schema)
        else:
            return {k: expand_refs(v, root_schema) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [expand_refs(item, root_schema) for item in obj]
    else:
        return obj

def remove_nullable(obj):
    """Recursively remove 'nullable' keys from schema objects."""
    if isinstance(obj, dict):
        obj = dict(obj)  # shallow copy
        obj.pop('nullable', None)
        for k, v in obj.items():
            obj[k] = remove_nullable(v)
        return obj
    elif isinstance(obj, list):
        return [remove_nullable(item) for item in obj]
    else:
        return obj

def filter_required(properties, required):
    """Remove nullable properties from the required list."""
    return [
        pname for pname in required
        if not (properties.get(pname, {}).get("nullable", False))
    ]

def ensure_required_on_objects(schema):
    """
    Recursively ensure every object schema has a 'required' key (even if empty),
    and that it only includes non-nullable properties.
    """
    if isinstance(schema, dict):
        if schema.get('type') == 'object' and 'properties' in schema:
            properties = schema['properties']
            # Use the schema's own 'required' if present, else empty list
            required = schema.get('required', list(properties.keys()))
            # Filter out nullable properties
            filtered_required = filter_required(properties, required)
            schema['required'] = filtered_required
            # Recurse into each property
            for pname, pinfo in properties.items():
                schema['properties'][pname] = ensure_required_on_objects(pinfo)
        elif schema.get('type') == 'array' and 'items' in schema:
            schema['items'] = ensure_required_on_objects(schema['items'])
        else:
            for k, v in schema.items():
                schema[k] = ensure_required_on_objects(v)
        return schema
    elif isinstance(schema, list):
        return [ensure_required_on_objects(item) for item in schema]
    else:
        return schema

def transform_schema_strict_mode(schema, original_required=None):
    """
    Recursively transform schema for OpenAI strict mode:
    - required: all property names
    - additionalProperties: false
    - optional/nullable fields: type includes 'null'
    """
    if isinstance(schema, dict):
        if schema.get('type') == 'object' and 'properties' in schema:
            properties = schema['properties']
            # Use the schema's own 'required' if present, else from argument, else all keys
            orig_required = schema.get('required', original_required if original_required is not None else list(properties.keys()))
            new_properties = {}
            for pname, pinfo in properties.items():
                # Determine if this property is nullable or not required
                is_nullable = pinfo.get('nullable', False)
                is_required = pname in orig_required
                # Remove nullable key
                pinfo = dict(pinfo)
                pinfo.pop('nullable', None)
                # If not required or nullable, add 'null' to type
                if not is_required or is_nullable:
                    # If type is already a list, add 'null' if not present
                    if isinstance(pinfo.get('type'), list):
                        if 'null' not in pinfo['type']:
                            pinfo['type'].append('null')
                    else:
                        pinfo['type'] = [pinfo.get('type', 'string'), 'null']
                # Recurse
                new_properties[pname] = transform_schema_strict_mode(pinfo)
            schema['properties'] = new_properties
            # All properties are required in strict mode
            schema['required'] = list(properties.keys())
            schema['additionalProperties'] = False
            return schema
        elif schema.get('type') == 'array' and 'items' in schema:
            schema['items'] = transform_schema_strict_mode(schema['items'])
            return schema
        else:
            for k, v in schema.items():
                schema[k] = transform_schema_strict_mode(v)
            return schema
    elif isinstance(schema, list):
        return [transform_schema_strict_mode(item) for item in schema]
    else:
        return schema

def extract_tool_definitions(schema, host):
    tools = []
    for path, methods in schema.get('paths', {}).items():
        for method, details in methods.items():
            name = f"{method}_{re.sub(r'[^a-zA-Z0-9]', '_', path.strip('/'))}".lower()
            summary = details.get('summary')
            description = details.get('description')
            desc = summary or description or '(No description)'
            properties = {}
            required = set()
            # Collect parameters (path, query, etc.)
            for param in details.get('parameters', []):
                param_schema = expand_refs(param.get('schema', {}), schema)
                cleaned_param_schema = remove_nullable(param_schema)
                pname = param.get('name')
                properties[pname] = {
                    'type': cleaned_param_schema.get('type', 'string'),
                    'description': param.get('description', '')
                }
                if param.get('required', False):
                    required.add(pname)
            # Merge requestBody properties at the top level if present
            if 'requestBody' in details:
                req_body = details['requestBody']
                content = req_body.get('content', {})
                for content_type, content_schema in content.items():
                    schema_obj = expand_refs(content_schema.get('schema', {}), schema)
                    if schema_obj.get('type') == 'object':
                        for pname, pinfo in schema_obj.get('properties', {}).items():
                            properties[pname] = remove_nullable(pinfo)
                        # Filter required for nullable
                        filtered_required = filter_required(schema_obj.get('properties', {}), schema_obj.get('required', []))
                        for req in filtered_required:
                            required.add(req)
                    else:
                        properties['body'] = remove_nullable(schema_obj)
                        if req_body.get('required', False):
                            required.add('body')
            # Filter required for nullable at the top level
            filtered_required = filter_required(properties, list(required))
            # Remove nullable from all properties recursively
            cleaned_properties = {k: remove_nullable(v) for k, v in properties.items()}
            param_schema = {
                'type': 'object',
                'properties': cleaned_properties,
                'required': filtered_required,
                'additionalProperties': False
            }
            # Ensure every object (including nested) has a required key
            param_schema = ensure_required_on_objects(param_schema)
            # Transform for OpenAI strict mode
            param_schema = transform_schema_strict_mode(param_schema, original_required=filtered_required)
            # Ensure path is prefixed with /api
            api_path = path if path.startswith('/api') else '/api' + (path if path.startswith('/') else '/' + path)
            tools.append({
                'name': name,
                'description': desc,
                'parameters': param_schema,
                'call': {
                    'type': 'http',
                    'host': host,
                    'method': method,
                    'path': api_path
                }
            })
    return tools

def extract_openai_tools(tools):
    """
    Extracts only the OpenAI-ready tool definitions (name, description, parameters, type) from the full tool list.
    Dumps the result to openai_tools.json for inspection.
    """
    openai_tools = [
        {
            'type': 'function',
            'name': tool['name'],
            'description': tool['description'],
            'parameters': tool['parameters']
        }
        for tool in tools
    ]
    with open('openai_tools.json', 'w') as f:
        json.dump(openai_tools, f, indent=4)
    return openai_tools

def get_tools(host="http://localhost:3000"):
    openapi_url = host.rstrip('/') + "/api/openapi"
    schema, _ = fetch_openapi_schema(openapi_url)
    tools = extract_tool_definitions(schema, host)
    with open('tools.json', 'w') as f:
        json.dump(tools, f, indent=4)
    print(f"Extracted {len(tools)} tool definitions. See tools.json for details.")
    # Uncomment the next line to print a summary for debugging
    # print_tools_summary(tools)
    # To get OpenAI-ready tools, use: openai_tools = extract_openai_tools(tools)
    return tools

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
    get_tools() 