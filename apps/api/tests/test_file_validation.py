import pytest

from services.file_validation import PDF_MIME, DOCX_MIME, validate_resume_file


def test_rejects_empty_file():
    with pytest.raises(ValueError, match="empty"):
        validate_resume_file(b"", max_bytes=1024)


def test_accepts_pdf_magic_bytes():
    result = validate_resume_file(b"%PDF-1.4 fake", max_bytes=1024)
    assert result.mime_type == PDF_MIME
    assert result.extension == "pdf"


def test_rejects_non_resume_zip():
    with pytest.raises(ValueError, match="Unsupported"):
        validate_resume_file(b"PK\x03\x04" + b"\x00" * 20, max_bytes=1024)


def test_rejects_oversized_file():
    with pytest.raises(ValueError, match="maximum size"):
        validate_resume_file(b"%PDF" + b"x" * 20, max_bytes=10)
