"""
Version Service (Step 8)

Handles version control operations:
- Restore previous version
- Duplicate version
- Version history management
"""

from typing import Dict, Any, Optional
from uuid import uuid4
from supabase import Client


class VersionService:
    """
    Service for managing resume version history.
    
    Provides:
    - Restore previous version (creates new version from old one)
    - Duplicate version (creates new resume from version)
    - Version comparison (future)
    """
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def restore_version(
        self,
        version_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Restore a previous version.
        
        Process:
        1. Fetch the old version and all its content (sections, blocks)
        2. Create a new version with incremented version_number
        3. Copy all sections and blocks to the new version
        4. Set as current version
        
        Args:
            version_id: Version to restore
            user_id: User ID
            
        Returns:
            New version dict
        """
        # Fetch old version
        old_version_response = self.supabase.table("resume_versions").select(
            "*"
        ).eq("id", version_id).eq("user_id", user_id).execute()
        
        if not old_version_response.data:
            raise ValueError("Version not found")
        
        old_version = old_version_response.data[0]
        resume_id = old_version["resume_id"]
        
        # Get max version number for this resume
        versions_response = self.supabase.table("resume_versions").select(
            "version_number"
        ).eq("resume_id", resume_id).order(
            "version_number", desc=True
        ).limit(1).execute()
        
        max_version = versions_response.data[0]["version_number"] if versions_response.data else 0
        new_version_number = max_version + 1
        
        # Create new version
        new_version_id = str(uuid4())
        new_version = {
            "id": new_version_id,
            "resume_id": resume_id,
            "user_id": user_id,
            "version_number": new_version_number,
            "status": old_version["status"],
            "storage_path": old_version["storage_path"],  # Same file
            "original_filename": old_version["original_filename"],
            "mime_type": old_version["mime_type"],
            "file_size_bytes": old_version["file_size_bytes"],
            "needs_ocr": old_version["needs_ocr"],
            "parse_error": old_version.get("parse_error")
        }
        
        new_version_response = self.supabase.table("resume_versions").insert(
            new_version
        ).execute()
        
        if not new_version_response.data:
            raise ValueError("Failed to create new version")
        
        # Copy sections
        await self._copy_sections_and_blocks(
            source_version_id=version_id,
            target_version_id=new_version_id,
            user_id=user_id
        )
        
        # Copy fact ledger
        await self._copy_fact_ledger(
            source_version_id=version_id,
            target_version_id=new_version_id,
            user_id=user_id
        )
        
        # Set as current version
        self.supabase.table("resumes").update({
            "current_version_id": new_version_id,
            "updated_at": "now()"
        }).eq("id", resume_id).eq("user_id", user_id).execute()
        
        return new_version_response.data[0]
    
    async def duplicate_version(
        self,
        version_id: str,
        new_title: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Duplicate a version as a new resume.
        
        Creates a completely new resume with content from the specified version.
        Useful for creating variations (e.g., different job targets).
        
        Args:
            version_id: Version to duplicate
            new_title: Title for new resume (defaults to "Copy of [original]")
            user_id: User ID
            
        Returns:
            New version dict (version 1 of new resume)
        """
        # Fetch old version
        old_version_response = self.supabase.table("resume_versions").select(
            "*"
        ).eq("id", version_id).eq("user_id", user_id).execute()
        
        if not old_version_response.data:
            raise ValueError("Version not found")
        
        old_version = old_version_response.data[0]
        
        # Get original resume for title
        old_resume_response = self.supabase.table("resumes").select(
            "title"
        ).eq("id", old_version["resume_id"]).execute()
        
        original_title = old_resume_response.data[0]["title"] if old_resume_response.data else "Resume"
        
        if not new_title:
            new_title = f"Copy of {original_title}"
        
        # Create new resume
        new_resume_id = str(uuid4())
        new_resume = {
            "id": new_resume_id,
            "user_id": user_id,
            "title": new_title
        }
        
        resume_response = self.supabase.table("resumes").insert(new_resume).execute()
        
        if not resume_response.data:
            raise ValueError("Failed to create new resume")
        
        # Create new version (version 1 of new resume)
        new_version_id = str(uuid4())
        new_version = {
            "id": new_version_id,
            "resume_id": new_resume_id,
            "user_id": user_id,
            "version_number": 1,
            "status": old_version["status"],
            "storage_path": old_version["storage_path"],
            "original_filename": old_version["original_filename"],
            "mime_type": old_version["mime_type"],
            "file_size_bytes": old_version["file_size_bytes"],
            "needs_ocr": old_version["needs_ocr"],
            "parse_error": old_version.get("parse_error")
        }
        
        new_version_response = self.supabase.table("resume_versions").insert(
            new_version
        ).execute()
        
        if not new_version_response.data:
            raise ValueError("Failed to create new version")
        
        # Copy sections and blocks
        await self._copy_sections_and_blocks(
            source_version_id=version_id,
            target_version_id=new_version_id,
            user_id=user_id
        )
        
        # Copy fact ledger
        await self._copy_fact_ledger(
            source_version_id=version_id,
            target_version_id=new_version_id,
            user_id=user_id
        )
        
        # Set as current version for new resume
        self.supabase.table("resumes").update({
            "current_version_id": new_version_id,
            "updated_at": "now()"
        }).eq("id", new_resume_id).eq("user_id", user_id).execute()
        
        return new_version_response.data[0]
    
    async def _copy_sections_and_blocks(
        self,
        source_version_id: str,
        target_version_id: str,
        user_id: str
    ):
        """Copy all sections and blocks from source to target version."""
        # Fetch all sections
        sections_response = self.supabase.table("resume_sections").select(
            "*"
        ).eq("resume_version_id", source_version_id).eq(
            "user_id", user_id
        ).order("sort_order").execute()
        
        if not sections_response.data:
            return
        
        # Map old section IDs to new ones
        section_id_map = {}
        
        # Copy sections
        for old_section in sections_response.data:
            new_section_id = str(uuid4())
            section_id_map[old_section["id"]] = new_section_id
            
            new_section = {
                "id": new_section_id,
                "resume_version_id": target_version_id,
                "user_id": user_id,
                "section_type": old_section["section_type"],
                "title": old_section.get("title"),
                "sort_order": old_section["sort_order"]
            }
            
            self.supabase.table("resume_sections").insert(new_section).execute()
        
        # Fetch all blocks
        blocks_response = self.supabase.table("resume_blocks").select(
            "*"
        ).eq("resume_version_id", source_version_id).eq(
            "user_id", user_id
        ).order("section_id, sort_order").execute()
        
        if not blocks_response.data:
            return
        
        # Copy blocks
        for old_block in blocks_response.data:
            new_section_id = section_id_map.get(old_block["section_id"])
            if not new_section_id:
                continue  # Skip if section wasn't copied
            
            new_block = {
                "id": str(uuid4()),
                "resume_version_id": target_version_id,
                "section_id": new_section_id,
                "user_id": user_id,
                "block_type": old_block["block_type"],
                "content": old_block["content"],
                "sort_order": old_block["sort_order"],
                "embedding": None  # Don't copy embeddings, regenerate if needed
            }
            
            self.supabase.table("resume_blocks").insert(new_block).execute()
    
    async def _copy_fact_ledger(
        self,
        source_version_id: str,
        target_version_id: str,
        user_id: str
    ):
        """Copy fact ledger entries from source to target version."""
        # Fetch all facts
        facts_response = self.supabase.table("fact_ledger_entries").select(
            "*"
        ).eq("resume_version_id", source_version_id).eq("user_id", user_id).execute()
        
        if not facts_response.data:
            return
        
        # Copy facts (note: source_block_id won't be valid in new version)
        for old_fact in facts_response.data:
            new_fact = {
                "id": str(uuid4()),
                "user_id": user_id,
                "resume_version_id": target_version_id,
                "source_block_id": None,  # Don't link to old blocks
                "fact_type": old_fact["fact_type"],
                "fact_text": old_fact["fact_text"],
                "is_verified": old_fact["is_verified"],
                "metadata": old_fact["metadata"],
                "embedding": None  # Don't copy embeddings
            }
            
            self.supabase.table("fact_ledger_entries").insert(new_fact).execute()


def get_version_service(supabase_client: Client) -> VersionService:
    """Get or create version service instance."""
    return VersionService(supabase_client)
