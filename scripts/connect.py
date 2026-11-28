from supabase import Client, create_client

SUPABASE_URL = ...
SUPABASE_PUBLISHABLE_KEY = ...


def connect(
    email: str,
    password: str,
    *,
    url: str = SUPABASE_URL,
    key: str = SUPABASE_PUBLISHABLE_KEY,
) -> Client:
    client = create_client(url, key)
    client.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })
    return client