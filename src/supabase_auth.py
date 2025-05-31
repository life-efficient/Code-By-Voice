import os

# NOTE: Requires 'supabase' package. Install with: pip install supabase

def get_supabase_access_token(url=None, key=None):
    """
    Obtain a Supabase JWT access token for a user, using credentials and config from environment variables.
    Environment variables required:
        SUPABASE_EMAIL
        SUPABASE_PASSWORD
        SUPABASE_URL
        SUPABASE_ANON_KEY
    Args:
        url (str): Supabase project URL (default: from env SUPABASE_URL).
        key (str): Supabase anon/public key (default: from env SUPABASE_ANON_KEY).
    Returns:
        str: The JWT access token, or None if login fails.
    """
    email = os.getenv("SUPABASE_EMAIL")
    password = os.getenv("SUPABASE_PASSWORD")
    if url is None:
        url = os.getenv("SUPABASE_URL")
    if key is None:
        key = os.getenv("SUPABASE_ANON_KEY")
    if not email or not password:
        print("Missing SUPABASE_EMAIL or SUPABASE_PASSWORD in environment variables.")
        return None
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment variables.")
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