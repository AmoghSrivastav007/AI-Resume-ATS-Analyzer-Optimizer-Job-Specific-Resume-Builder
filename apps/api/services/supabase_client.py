from supabase import Client, create_client

from config import Settings


def create_user_client(settings: Settings, access_token: str) -> Client:
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    client.storage.auth(access_token)
    return client


def create_service_client(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
