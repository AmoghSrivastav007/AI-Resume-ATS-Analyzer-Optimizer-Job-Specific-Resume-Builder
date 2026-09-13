import io
import zipfile
from dataclasses import dataclass

from services.file_validation import validate_resume_file
from services.parser.virus_scanner import VirusScanner, get_virus_scanner

from config import Settings

MACRO_PATH_PREFIXES = ("word/vba", "word/activeX", "word/_rels/vba")
MACRO_EXACT_PATHS = {"word/vbaProject.bin", "word/vbaData.xml"}


@dataclass(frozen=True)
class IntakeResult:
    content: bytes
    mime_type: str
    extension: str
    virus_scan_detail: str


def sanitize_file(
    content: bytes,
    filename: str,
    settings: Settings,
    scanner: VirusScanner | None = None,
) -> IntakeResult:
    validated = validate_resume_file(content, settings.max_upload_bytes)
    active_scanner = scanner or get_virus_scanner(settings)
    scan_result = active_scanner.scan(content, filename)
    if not scan_result.clean:
        raise ValueError(f"File failed virus scan: {scan_result.detail}")

    sanitized = content
    if validated.extension == "docx":
        sanitized = strip_docx_macros(content)

    return IntakeResult(
        content=sanitized,
        mime_type=validated.mime_type,
        extension=validated.extension,
        virus_scan_detail=scan_result.detail,
    )


def strip_docx_macros(content: bytes) -> bytes:
    input_buffer = io.BytesIO(content)
    if not zipfile.is_zipfile(input_buffer):
        return content

    input_buffer.seek(0)
    output_buffer = io.BytesIO()

    with zipfile.ZipFile(input_buffer, "r") as source:
        with zipfile.ZipFile(output_buffer, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for item in source.infolist():
                name_lower = item.filename.lower()
                if name_lower in MACRO_EXACT_PATHS:
                    continue
                if any(name_lower.startswith(prefix) for prefix in MACRO_PATH_PREFIXES):
                    continue
                if name_lower.startswith("activex/"):
                    continue
                target.writestr(item, source.read(item.filename))

    return output_buffer.getvalue()
