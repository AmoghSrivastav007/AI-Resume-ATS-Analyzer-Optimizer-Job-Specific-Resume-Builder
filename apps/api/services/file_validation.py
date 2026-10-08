import io
import zipfile
from dataclasses import dataclass


PDF_MAGIC = b"%PDF"
ZIP_MAGIC = b"PK\x03\x04"
TXT_MAGIC_PATTERNS = [b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff"]  # UTF-8 BOM, UTF-16 LE/BE
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"
TXT_MIME = "text/plain"


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


def validate_file_type(content: bytes, allowed_extensions: list[str], max_bytes: int = 10 * 1024 * 1024) -> ValidatedResumeFile:
    """
    Validate file type by magic bytes for multiple file types.
    
    Args:
        content: File bytes
        allowed_extensions: List of allowed extensions ('pdf', 'docx', 'txt')
        max_bytes: Maximum file size
    
    Returns:
        ValidatedResumeFile with mime_type and extension
    
    Raises:
        ValueError: If file invalid or not allowed
    """
    if not content:
        raise ValueError("Uploaded file is empty")

    if len(content) > max_bytes:
        raise ValueError(f"File exceeds maximum size of {max_bytes // (1024 * 1024)}MB")

    # Check PDF
    if "pdf" in allowed_extensions and content.startswith(PDF_MAGIC):
        return ValidatedResumeFile(mime_type=PDF_MIME, extension="pdf")

    # Check DOCX
    if "docx" in allowed_extensions and content.startswith(ZIP_MAGIC) and _is_docx(content):
        return ValidatedResumeFile(mime_type=DOCX_MIME, extension="docx")
    
    # Check TXT (must be valid UTF-8 text)
    if "txt" in allowed_extensions:
        try:
            content.decode("utf-8")
            return ValidatedResumeFile(mime_type=TXT_MIME, extension="txt")
        except UnicodeDecodeError:
            pass

    allowed_str = ", ".join(allowed_extensions).upper()
    raise ValueError(f"Unsupported file type. Only {allowed_str} files are accepted.")

