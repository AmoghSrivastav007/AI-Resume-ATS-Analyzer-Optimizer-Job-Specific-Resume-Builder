from __future__ import annotations

from typing import Any

from models.parse import CrossValidationResult
from models.extraction import ResumeExtraction
from services.audit import write_audit_log
from services.parser.structural import StructuralDocument
from services.supabase_client import create_service_client

from config import Settings

SECTION_ORDER: list[tuple[str, str]] = [
    ("contact", "Contact"),
    ("summary", "Summary"),
    ("experience", "Experience"),
    ("education", "Education"),
    ("skills", "Skills"),
    ("projects", "Projects"),
    ("certifications", "Certifications"),
    ("languages", "Languages"),
]


def persist_parse_result(
    *,
    settings: Settings,
    user_id: str,
    resume_version_id: str,
    extraction: ResumeExtraction,
    validation: CrossValidationResult,
    structural: StructuralDocument,
) -> dict[str, Any]:
    client = create_service_client(settings)
    payload = validation.extraction

    _clear_previous(client, resume_version_id)

    sections: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    facts: list[dict[str, Any]] = []

    for sort_order, (section_type, title) in enumerate(SECTION_ORDER):
        section_row = (
            client.table("resume_sections")
            .insert(
                {
                    "resume_version_id": resume_version_id,
                    "user_id": user_id,
                    "section_type": section_type,
                    "title": title,
                    "sort_order": sort_order,
                }
            )
            .execute()
        )
        if not section_row.data:
            raise RuntimeError(f"Failed to insert resume_sections row for {section_type}")
        section = section_row.data[0]
        sections.append(section)
        created_blocks = _insert_section_blocks(
            client=client,
            user_id=user_id,
            resume_version_id=resume_version_id,
            section=section,
            payload=payload,
        )
        blocks.extend(created_blocks)
        facts.extend(
            _insert_section_facts(
                client=client,
                user_id=user_id,
                resume_version_id=resume_version_id,
                section_type=section_type,
                payload=payload,
                blocks=created_blocks,
            )
        )

    layout_meta = {
        "block_count": len(structural.blocks),
        "mime_type": structural.mime_type,
        "layout_blocks": [
            {
                "text": block.text,
                "page": block.page,
                "bbox": block.bbox,
                "font_name": block.font_name,
                "font_size": block.font_size,
                "sort_order": block.sort_order,
            }
            for block in structural.blocks[:500]
        ],
    }

    write_audit_log(
        client,
        user_id,
        "create",
        "resume_versions",
        resume_version_id,
        {"event": "parse_persist", "section_count": len(sections), "block_count": len(blocks)},
    )

    return {
        "extraction": payload,
        "disagreements": [item.model_dump() for item in validation.disagreements],
        "sections": sections,
        "blocks": blocks,
        "facts": facts,
        "layout": layout_meta,
    }


def _clear_previous(client, resume_version_id: str) -> None:
    client.table("fact_ledger_entries").delete().eq("resume_version_id", resume_version_id).execute()
    client.table("resume_blocks").delete().eq("resume_version_id", resume_version_id).execute()
    client.table("resume_sections").delete().eq("resume_version_id", resume_version_id).execute()


def _insert_section_blocks(
    *,
    client,
    user_id: str,
    resume_version_id: str,
    section: dict[str, Any],
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    section_type = section["section_type"]
    rows: list[dict[str, Any]] = []

    if section_type == "contact":
        contact = payload.get("contact") or {}
        text = _contact_text(contact)
        if text:
            rows.append(_block_payload(section, user_id, resume_version_id, "paragraph", text, 0, contact))
    elif section_type == "summary":
        summary = payload.get("summary")
        if summary:
            rows.append(_block_payload(section, user_id, resume_version_id, "paragraph", summary, 0, {}))
    elif section_type == "experience":
        for index, item in enumerate(payload.get("work_experience") or []):
            heading = f"{item.get('title', '')} — {item.get('company', '')}".strip(" —")
            rows.append(_block_payload(section, user_id, resume_version_id, "heading", heading, index * 10, item))
            for bullet_index, bullet in enumerate(item.get("bullets") or []):
                rows.append(
                    _block_payload(
                        section,
                        user_id,
                        resume_version_id,
                        "bullet",
                        bullet,
                        index * 10 + bullet_index + 1,
                        {"source": "work_experience", "index": index},
                    )
                )
    elif section_type == "education":
        for index, item in enumerate(payload.get("education") or []):
            heading = " — ".join(part for part in [item.get("degree"), item.get("institution")] if part)
            rows.append(_block_payload(section, user_id, resume_version_id, "heading", heading, index, item))
    elif section_type == "skills":
        for index, item in enumerate(payload.get("skills") or []):
            rows.append(
                _block_payload(section, user_id, resume_version_id, "list_item", item.get("name", ""), index, item)
            )
    elif section_type == "projects":
        for index, item in enumerate(payload.get("projects") or []):
            rows.append(_block_payload(section, user_id, resume_version_id, "heading", item.get("name", ""), index, item))
    elif section_type == "certifications":
        for index, item in enumerate(payload.get("certifications") or []):
            rows.append(_block_payload(section, user_id, resume_version_id, "list_item", item.get("name", ""), index, item))
    elif section_type == "languages":
        for index, item in enumerate(payload.get("languages") or []):
            label = item.get("name", "")
            if item.get("proficiency"):
                label = f"{label} ({item['proficiency']})"
            rows.append(_block_payload(section, user_id, resume_version_id, "list_item", label, index, item))

    created: list[dict[str, Any]] = []
    for row in rows:
        result = client.table("resume_blocks").insert(row).execute()
        if not result.data:
            raise RuntimeError("Failed to insert resume_blocks row")
        created.append(result.data[0])
    return created


def _insert_section_facts(
    *,
    client,
    user_id: str,
    resume_version_id: str,
    section_type: str,
    payload: dict[str, Any],
    blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    first_block_id = blocks[0]["id"] if blocks else None

    def add_fact(fact_type: str, fact_text: str, metadata: dict[str, Any], source_block_id: str | None = None) -> None:
        if not fact_text:
            return
        result = (
            client.table("fact_ledger_entries")
            .insert(
                {
                    "user_id": user_id,
                    "resume_version_id": resume_version_id,
                    "source_block_id": source_block_id or first_block_id,
                    "fact_type": fact_type,
                    "fact_text": fact_text,
                    "is_verified": False,
                    "metadata": metadata,
                }
            )
            .execute()
        )
        if result.data:
            created.append(result.data[0])

    if section_type == "contact":
        contact = payload.get("contact") or {}
        add_fact("other", contact.get("email") or "", {"field": "email"})
        add_fact("other", contact.get("phone") or "", {"field": "phone"})
        add_fact("title", contact.get("full_name") or "", {"field": "full_name"})
    elif section_type == "experience":
        for item in payload.get("work_experience") or []:
            add_fact("title", item.get("title") or "", {"company": item.get("company")})
            add_fact("date", item.get("start_date") or "", {"role": item.get("title"), "bound": "start"})
            add_fact("date", item.get("end_date") or "", {"role": item.get("title"), "bound": "end"})
            for bullet in item.get("bullets") or []:
                if any(char.isdigit() for char in bullet):
                    add_fact("metric", bullet, {"company": item.get("company")})
    elif section_type == "education":
        for item in payload.get("education") or []:
            add_fact("title", item.get("degree") or item.get("institution") or "", item)
            add_fact("date", item.get("start_date") or "", {"bound": "start"})
            add_fact("date", item.get("end_date") or "", {"bound": "end"})
    elif section_type == "skills":
        for item in payload.get("skills") or []:
            add_fact("skill", item.get("name") or "", item)
    elif section_type == "certifications":
        for item in payload.get("certifications") or []:
            add_fact("certification", item.get("name") or "", item)
            add_fact("date", item.get("issue_date") or "", {"certification": item.get("name")})
    elif section_type == "projects":
        for item in payload.get("projects") or []:
            add_fact("title", item.get("name") or "", item)
            add_fact("date", item.get("start_date") or "", {"project": item.get("name")})
    elif section_type == "languages":
        for item in payload.get("languages") or []:
            add_fact("skill", item.get("name") or "", {"kind": "language", **item})

    return created


def _block_payload(
    section: dict[str, Any],
    user_id: str,
    resume_version_id: str,
    block_type: str,
    text: str,
    sort_order: int,
    extra: dict[str, Any],
) -> dict[str, Any]:
    return {
        "resume_version_id": resume_version_id,
        "section_id": section["id"],
        "user_id": user_id,
        "block_type": block_type,
        "content": {"text": text, **extra},
        "sort_order": sort_order,
    }


def _contact_text(contact: dict[str, Any]) -> str:
    parts = [
        contact.get("full_name"),
        contact.get("email"),
        contact.get("phone"),
        contact.get("location"),
        contact.get("linkedin"),
        contact.get("website"),
    ]
    return " | ".join(part for part in parts if part)
