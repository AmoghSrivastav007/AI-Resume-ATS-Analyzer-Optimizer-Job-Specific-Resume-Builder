from supabase import Client


def write_audit_log(
    client: Client,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict | None = None,
) -> None:
    payload = {
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "metadata": metadata or {},
    }
    result = client.table("audit_log").insert(payload).execute()
    if not result.data:
        raise RuntimeError(f"Failed to write audit_log for {resource_type}:{resource_id}")
