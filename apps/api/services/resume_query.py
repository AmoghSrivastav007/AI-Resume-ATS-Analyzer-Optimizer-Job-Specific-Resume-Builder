from models.resume import (
    FactLedgerEntryResponse,
    ResumeBlockResponse,
    ResumeDetailData,
    ResumeDetailResponse,
    ResumeSectionResponse,
    ResumeVersionResponse,
)
from services.audit import write_audit_log
from supabase import Client


def _version_from_row(row: dict) -> ResumeVersionResponse:
    return ResumeVersionResponse(
        id=row["id"],
        resume_id=row["resume_id"],
        version_number=row["version_number"],
        status=row["status"],
        storage_path=row["storage_path"],
        original_filename=row["original_filename"],
        mime_type=row["mime_type"],
        file_size_bytes=row["file_size_bytes"],
        needs_ocr=bool(row.get("needs_ocr") or False),
        parse_error=row.get("parse_error"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_resume_detail(client: Client, user_id: str, resume_id: str) -> ResumeDetailResponse:
    resume_result = (
        client.table("resumes").select("*").eq("id", resume_id).eq("user_id", user_id).single().execute()
    )
    if not resume_result.data:
        raise KeyError("Resume not found")
    resume = resume_result.data

    version_id = resume.get("current_version_id")
    if not version_id:
        raise KeyError("Resume has no current version")

    version_result = (
        client.table("resume_versions")
        .select("*")
        .eq("id", version_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not version_result.data:
        raise KeyError("Resume version not found")
    version = version_result.data

    write_audit_log(client, user_id, "read", "resumes", resume_id, {"version_id": version_id})

    sections_result = (
        client.table("resume_sections")
        .select("*")
        .eq("resume_version_id", version_id)
        .eq("user_id", user_id)
        .order("sort_order")
        .execute()
    )
    blocks_result = (
        client.table("resume_blocks")
        .select("*")
        .eq("resume_version_id", version_id)
        .eq("user_id", user_id)
        .order("sort_order")
        .execute()
    )
    facts_result = (
        client.table("fact_ledger_entries")
        .select("*")
        .eq("resume_version_id", version_id)
        .eq("user_id", user_id)
        .execute()
    )

    blocks_by_section: dict[str, list[ResumeBlockResponse]] = {}
    for block in blocks_result.data or []:
        blocks_by_section.setdefault(block["section_id"], []).append(
            ResumeBlockResponse(
                id=block["id"],
                block_type=block["block_type"],
                content=block.get("content") or {},
                sort_order=block["sort_order"],
            )
        )

    sections = [
        ResumeSectionResponse(
            id=section["id"],
            section_type=section["section_type"],
            title=section.get("title"),
            sort_order=section["sort_order"],
            blocks=sorted(blocks_by_section.get(section["id"], []), key=lambda item: item.sort_order),
        )
        for section in (sections_result.data or [])
    ]

    facts = [
        FactLedgerEntryResponse(
            id=fact["id"],
            fact_type=fact["fact_type"],
            fact_text=fact["fact_text"],
            is_verified=bool(fact.get("is_verified")),
            source_block_id=fact.get("source_block_id"),
            metadata=fact.get("metadata") or {},
        )
        for fact in (facts_result.data or [])
    ]

    return ResumeDetailResponse(
        data=ResumeDetailData(
            id=resume["id"],
            title=resume["title"],
            current_version_id=resume.get("current_version_id"),
            created_at=resume["created_at"],
            updated_at=resume["updated_at"],
            version=_version_from_row(version),
            sections=sections,
            facts=facts,
        )
    )
