import uuid
from pathlib import Path

from dependencies.auth import CurrentUser
from models.resume import ResumeResponse, ResumeUploadResponse, ResumeVersionResponse
from services.audit import write_audit_log
from services.file_validation import validate_resume_file
from services.queue import enqueue_parse_job
from services.supabase_client import create_user_client

from config import Settings


class ResumeUploadService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def upload_resume(
        self,
        user: CurrentUser,
        filename: str,
        content: bytes,
    ) -> ResumeUploadResponse:
        validated = validate_resume_file(content, self.settings.max_upload_bytes)
        client = create_user_client(self.settings, user.token)

        safe_name = Path(filename or "resume").name
        title = Path(safe_name).stem or "Resume"
        object_id = uuid.uuid4()
        storage_path = f"{user.id}/{object_id}.{validated.extension}"

        storage = client.storage.from_("resumes")
        storage.upload(
            path=storage_path,
            file=content,
            file_options={"content-type": validated.mime_type, "upsert": "false"},
        )

        resume_insert = (
            client.table("resumes")
            .insert({"user_id": user.id, "title": title})
            .execute()
        )
        if not resume_insert.data:
            raise RuntimeError("Failed to create resume row")

        resume_row = resume_insert.data[0]
        resume_id = resume_row["id"]
        write_audit_log(client, user.id, "create", "resumes", resume_id, {"title": title})

        version_insert = (
            client.table("resume_versions")
            .insert(
                {
                    "resume_id": resume_id,
                    "user_id": user.id,
                    "version_number": 1,
                    "status": "parsing",
                    "storage_path": storage_path,
                    "original_filename": safe_name,
                    "mime_type": validated.mime_type,
                    "file_size_bytes": len(content),
                }
            )
            .execute()
        )
        if not version_insert.data:
            raise RuntimeError("Failed to create resume_version row")

        version_row = version_insert.data[0]
        version_id = version_row["id"]
        write_audit_log(
            client,
            user.id,
            "create",
            "resume_versions",
            version_id,
            {"status": "parsing"},
        )

        updated_resume = (
            client.table("resumes")
            .update({"current_version_id": version_id})
            .eq("id", resume_id)
            .execute()
        )
        resume_row = updated_resume.data[0] if updated_resume.data else resume_row

        job = enqueue_parse_job(
            self.settings,
            resume_id=str(resume_id),
            version_id=str(version_id),
            user_id=user.id,
            access_token=user.token,
        )

        return ResumeUploadResponse(
            data=ResumeResponse(
                id=resume_row["id"],
                title=resume_row["title"],
                current_version_id=resume_row.get("current_version_id"),
                created_at=resume_row["created_at"],
                updated_at=resume_row["updated_at"],
                job_id=job.id,
                version=ResumeVersionResponse(
                    id=version_row["id"],
                    resume_id=version_row["resume_id"],
                    version_number=version_row["version_number"],
                    status=version_row["status"],
                    storage_path=version_row["storage_path"],
                    original_filename=version_row["original_filename"],
                    mime_type=version_row["mime_type"],
                    file_size_bytes=version_row["file_size_bytes"],
                    needs_ocr=bool(version_row.get("needs_ocr") or False),
                    parse_error=version_row.get("parse_error"),
                    created_at=version_row["created_at"],
                    updated_at=version_row["updated_at"],
                ),
            )
        )
