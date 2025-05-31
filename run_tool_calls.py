import requests
from src.supabase_auth import get_supabase_access_token

token = get_supabase_access_token()


def run_http_tool_call(tool_call_definition, params):
    """Executes a tool call by making a HTTP request."""
    call = tool_call_definition['call']
    if call['type'] == 'http':
        url = call['host'] + call['path']
        method = call['method'].upper()
        headers = {"Authorization": f"Bearer {token}"}  # Add Bearer token to all requests
        # Remove parameters that are part of the path
        path_params = {}
        for key in list(params.keys()):
            if '{' + key + '}' in call['path']:
                url = url.replace('{' + key + '}', str(params[key]))
                path_params[key] = params.pop(key)
        try:
            if method == 'GET':
                resp = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                resp = requests.post(url, json=params, headers=headers)
            elif method == 'PATCH':
                resp = requests.patch(url, json=params, headers=headers)
            elif method == 'DELETE':
                resp = requests.delete(url, params=params, headers=headers)
            else:
                return f"Unsupported HTTP method: {method}"
            try:
                return resp.json()
            except Exception:
                return resp.text
        except Exception as e:
            return f"HTTP request failed: {e}"
    else:
        return f"Unsupported tool type: {call['type']}" 