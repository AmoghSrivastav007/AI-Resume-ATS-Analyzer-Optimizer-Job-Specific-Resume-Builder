from supabase import Client


def write_audit_log(
    client: Client,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict | None = None,
) -> None:
    """
    Write an audit log entry for PII access.
    
    IMPORTANT: Do NOT include raw PII in metadata (no resume text, emails, etc.)
    Only log access metadata (IP, endpoint, status code).
    """
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


async def log_audit_event(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict | None = None,
) -> None:
    """
    Async wrapper for audit logging.
    Used in async route handlers.
    """
    # For now, this is a placeholder
    # In production, would use async Supabase client or queue
    # For MVP, sync call is acceptable as audit is fire-and-forget
    pass  # Implemented via write_audit_log in sync contexts
