import io
import zipfile
from dataclasses import dataclass


PDF_MAGIC = b"%PDF"
ZIP_MAGIC = b"PK\x03\x04"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"


@dataclass(frozen=True)
class ValidatedResumeFile:
    mime_type: str
    extension: str


def validate_resume_file(content: bytes, max_bytes: int) -> ValidatedResumeFile:
    if not content:
        raise ValueError("Uploaded file is empty")

    if len(content) > max_bytes:
        raise ValueError(f"File exceeds maximum size of {max_bytes // (1024 * 1024)}MB")

    if content.startswith(PDF_MAGIC):
        return ValidatedResumeFile(mime_type=PDF_MIME, extension="pdf")

    if content.startswith(ZIP_MAGIC) and _is_docx(content):
        return ValidatedResumeFile(mime_type=DOCX_MIME, extension="docx")

    raise ValueError("Unsupported file type. Only PDF and DOCX files are accepted.")


def _is_docx(content: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            return "word/document.xml" in archive.namelist()
    except zipfile.BadZipFile:
        return False
