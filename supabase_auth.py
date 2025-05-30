import os

# NOTE: Requires 'supabase' package. Install with: pip install supabase

def get_supabase_access_token(url="http://127.0.0.1:54321", key="YOUR_LOCAL_ANON_KEY"):
    """
    Obtain a Supabase JWT access token for a user, using credentials from environment variables.
    Environment variables required:
        SUPABASE_EMAIL
        SUPABASE_PASSWORD
    Args:
        url (str): Supabase project URL (default: local dev).
        key (str): Supabase anon/public key.
    Returns:
        str: The JWT access token, or None if login fails.
    """
    email = os.getenv("SUPABASE_EMAIL")
    password = os.getenv("SUPABASE_PASSWORD")
    if not email or not password:
        print("Missing SUPABASE_EMAIL or SUPABASE_PASSWORD in environment variables.")
        return None
    try:
        from supabase import create_client, Client
    except ImportError:
        raise ImportError("You must install the 'supabase' package: pip install supabase")
    supabase: Client = create_client(url, key)
    auth_response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    if hasattr(auth_response, 'session') and hasattr(auth_response.session, 'access_token'):
        return auth_response.session.access_token
    else:
        print("Failed to obtain access token. Check credentials.")
        return None 