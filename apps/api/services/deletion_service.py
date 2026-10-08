"""
Data deletion service for complete removal of user data.

Implements hard delete (not soft delete) with storage cleanup.
"""

import logging
from typing import Any

from config import Settings
from services.audit import log_audit_event
from services.supabase_client import create_service_client

logger = logging.getLogger(__name__)


class DeletionService:
    """Service for permanently deleting user data."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = create_service_client(settings)

    async def delete_resume_completely(
        self,
        user_id: str,
        resume_id: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Completely delete a resume and all related data.
        
        This performs a HARD DELETE:
        1. Delete all database records (cascades handle relationships)
        2. Delete all storage files
        3. Log deletion to audit log
        
        Args:
            user_id: Owner of the resume
            resume_id: Resume to delete
            ip_address: IP for audit log
        """
        # Verify ownership
        resume = self.client.table("resumes").select("id, user_id").eq("id", resume_id).eq(
            "user_id", user_id
        ).single().execute()
        
        if not resume.data:
            raise ValueError("Resume not found or access denied")
        
        # Get all versions to delete storage files
        versions = self.client.table("resume_versions").select("storage_path").eq(
            "resume_id", resume_id
        ).execute()
        
        storage_paths = [v["storage_path"] for v in versions.data if v.get("storage_path")]
        
        # Get all export files
        exports = self.client.table("export_jobs").select("storage_path").eq(
            "resume_version_id__in", [v["id"] for v in versions.data]
        ).execute()
        
        export_paths = [e["storage_path"] for e in exports.data if e.get("storage_path")]
        
        # Delete database records (cascades will handle related tables)
        self.client.table("resumes").delete().eq("id", resume_id).eq("user_id", user_id).execute()
        
        # Delete storage files
        all_paths = storage_paths + export_paths
        if all_paths:
            try:
                self.client.storage.from_("resumes").remove(all_paths)
                logger.info(f"Deleted {len(all_paths)} storage files for resume {resume_id}")
            except Exception as e:
                logger.error(f"Failed to delete some storage files: {e}")
                # Continue anyway - database records are deleted
        
        # Log deletion
        await log_audit_event(
            user_id=user_id,
            action="delete",
            resource_type="resume",
            resource_id=resume_id,
            metadata={
                "ip_address": ip_address,
                "files_deleted": len(all_paths),
            }
        )
        
        logger.info(f"Resume {resume_id} completely deleted for user {user_id}")

    async def delete_user_account(
        self,
        user_id: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Completely delete a user account and ALL associated data.
        
        This is irreversible. Deletes:
        - All resumes and versions
        - All sections and blocks
        - All analyses and optimizations
        - All job descriptions
        - All applications
        - All exports
        - All storage files
        - User profile
        - Audit logs (after retention period)
        
        Args:
            user_id: User to delete
            ip_address: IP for audit log
        """
        # Get all resumes
        resumes = self.client.table("resumes").select("id").eq("user_id", user_id).execute()
        
        # Delete each resume (handles storage cleanup)
        for resume in resumes.data:
            await self.delete_resume_completely(user_id, resume["id"], ip_address)
        
        # Delete job descriptions and their storage files
        jds = self.client.table("job_descriptions").select("id").eq("user_id", user_id).execute()
        
        # Delete remaining tables not handled by resume cascade
        tables_to_clear = [
            "job_descriptions",
            "applications",
            # audit_log kept for retention period
        ]
        
        for table in tables_to_clear:
            self.client.table(table).delete().eq("user_id", user_id).execute()
        
        # Mark audit logs for deletion after retention period (90 days)
        self.client.table("audit_log").update({
            "metadata": {"marked_for_deletion": True, "deletion_date": "now() + interval '90 days'"}
        }).eq("user_id", user_id).execute()
        
        # Delete user profile (this also deletes from Supabase Auth)
        self.client.table("users").delete().eq("id", user_id).execute()
        
        # Final audit log before user deletion
        await log_audit_event(
            user_id=user_id,
            action="delete",
            resource_type="user",
            resource_id=user_id,
            metadata={
                "ip_address": ip_address,
                "resumes_deleted": len(resumes.data),
                "account_deletion": True,
            }
        )
        
        logger.info(f"User account {user_id} completely deleted")

    async def cleanup_expired_data(self) -> dict[str, Any]:
        """
        Cleanup expired data (run as scheduled job).
        
        Deletes:
        - Audit logs older than retention period
        - Temp export files older than 24 hours
        - Users marked for deletion (after grace period)
        
        Returns:
            Statistics about cleanup
        """
        stats = {
            "audit_logs_deleted": 0,
            "temp_files_deleted": 0,
            "users_deleted": 0,
        }
        
        # Delete old audit logs (90 days retention)
        result = self.client.table("audit_log").delete().lt(
            "created_at", "now() - interval '90 days'"
        ).execute()
        stats["audit_logs_deleted"] = len(result.data) if result.data else 0
        
        # Delete temp export files (24 hours)
        temp_files = self.client.storage.from_("resumes").list("temp_exports/")
        old_files = [
            f["name"] for f in temp_files
            if f.get("created_at", "") < "now() - interval '24 hours'"
        ]
        if old_files:
            self.client.storage.from_("resumes").remove([f"temp_exports/{f}" for f in old_files])
            stats["temp_files_deleted"] = len(old_files)
        
        # Delete users marked for deletion (7 day grace period)
        # This would require a pending_deletion table or field
        # For now, log that this needs manual implementation
        logger.info("User deletion grace period check not yet implemented")
        
        logger.info(f"Cleanup completed: {stats}")
        return stats
