import requests
import json

def print_openapi_endpoints(url="http://localhost:3000/api/openapi"):
    response = requests.get(url)
    response.raise_for_status()
    schema = response.json()

    print("Available Endpoints:")
    for path, methods in schema.get('paths', {}).items():
        for method, details in methods.items():
            print(f"\n{method.upper()} {path}")
            description = details.get('description', '(No description)')
            print(f"  Description: {description}")
            parameters = details.get('parameters', [])
            if parameters:
                print("  Parameters:")
                for param in parameters:
                    name = param.get('name', '(no name)')
                    param_in = param.get('in', '(no location)')
                    required = param.get('required', False)
                    param_desc = param.get('description', '(no description)')
                    print(f"    - {name} (in: {param_in}, required: {required}): {param_desc}")
            else:
                print("  Parameters: None")

if __name__ == "__main__":
    print_openapi_endpoints() 