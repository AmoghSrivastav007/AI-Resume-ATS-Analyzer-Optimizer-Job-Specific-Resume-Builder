from dataclasses import dataclass
from typing import Any

from config import Settings
from services.file_validation import PDF_MIME
from services.parser.cross_validate import cross_validate
from services.parser.exceptions import NeedsOcrError, ParsePipelineError
from services.parser.intake import sanitize_file
from services.parser.llm_extract import extract_resume_with_llm
from services.parser.persist import persist_parse_result
from services.parser.structural import extract_structure
from services.parser.text_layer import require_pdf_text_layer
from services.supabase_client import create_service_client


@dataclass(frozen=True)
class ParseJobResult:
    status: str
    needs_ocr: bool
    error: str | None
    parsed: dict[str, Any] | None


class ResumeParsePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, *, user_id: str, resume_id: str, resume_version_id: str, access_token: str | None = None) -> ParseJobResult:
        del access_token
        client = create_service_client(self.settings)
        version = (
            client.table("resume_versions")
            .select("*")
            .eq("id", resume_version_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not version.data:
            raise ParsePipelineError("Resume version not found")

        version_row = version.data
        self._update_version(client, resume_version_id, {"status": "parsing", "parse_error": None, "needs_ocr": False})

        try:
            file_bytes = client.storage.from_("resumes").download(version_row["storage_path"])
            intake = sanitize_file(file_bytes, version_row["original_filename"], self.settings)

            if intake.mime_type == PDF_MIME:
                require_pdf_text_layer(intake.content)

            structural = extract_structure(intake.content, intake.mime_type)
            extraction = extract_resume_with_llm(structural.plain_text, self.settings)
            validation = cross_validate(extraction, structural.plain_text)
            persisted = persist_parse_result(
                settings=self.settings,
                user_id=user_id,
                resume_version_id=resume_version_id,
                extraction=extraction,
                validation=validation,
                structural=structural,
            )
            self._update_version(client, resume_version_id, {"status": "parsed", "parse_error": None, "needs_ocr": False})
            return ParseJobResult(status="parsed", needs_ocr=False, error=None, parsed=persisted)
        except NeedsOcrError as exc:
            self._update_version(
                client,
                resume_version_id,
                {"status": "error", "needs_ocr": True, "parse_error": exc.user_message},
            )
            return ParseJobResult(status="error", needs_ocr=True, error=exc.user_message, parsed=None)
        except Exception as exc:
            message = str(exc)
            self._update_version(
                client,
                resume_version_id,
                {"status": "error", "needs_ocr": False, "parse_error": message},
            )
            return ParseJobResult(status="error", needs_ocr=False, error=message, parsed=None)

    def _update_version(self, client, resume_version_id: str, values: dict[str, Any]) -> None:
        client.table("resume_versions").update(values).eq("id", resume_version_id).execute()
