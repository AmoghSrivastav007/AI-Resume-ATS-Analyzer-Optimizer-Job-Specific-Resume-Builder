from supabase import Client, create_client

from config import Settings


def create_user_client(settings: Settings, access_token: str) -> Client:
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    client.storage.auth(access_token)
    return client


def create_service_client(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


# Compatibility alias for legacy code
def get_supabase_client(settings: Settings, access_token: str) -> Client:
    """
    Compatibility function for legacy imports.
    Use create_user_client or create_service_client directly in new code.
    """
    return create_user_client(settings, access_token)

