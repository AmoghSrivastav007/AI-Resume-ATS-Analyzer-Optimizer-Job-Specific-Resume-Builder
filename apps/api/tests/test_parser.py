import io
import zipfile

import fitz
import pytest

from models.extraction import ContactInfo, LlmResumeExtraction
from services.parser.cross_validate import cross_validate
from services.parser.exceptions import NeedsOcrError
from services.parser.intake import strip_docx_macros
from services.parser.text_layer import assess_pdf_text_layer, require_pdf_text_layer
from services.parser.virus_scanner import NoOpVirusScanner


def test_noop_virus_scanner_is_real_interface():
    result = NoOpVirusScanner().scan(b"%PDF-1.4", "resume.pdf")
    assert result.clean is True
    assert "skipped" in result.detail.lower()


def test_docx_macro_stripping_removes_vba_project():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<w:document />")
        archive.writestr("word/vbaProject.bin", b"macro-bytes")
        archive.writestr("[Content_Types].xml", "<Types />")

    stripped = strip_docx_macros(buffer.getvalue())
    with zipfile.ZipFile(io.BytesIO(stripped)) as archive:
        names = archive.namelist()
    assert "word/document.xml" in names
    assert "word/vbaProject.bin" not in names


def _pdf_with_text() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Jane Doe\nSoftware Engineer experience 2019 Present " * 8)
    data = document.tobytes()
    document.close()
    return data


def _pdf_without_text() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.draw_rect(page.rect, color=(0, 0, 0), fill=(0.9, 0.9, 0.9))
    data = document.tobytes()
    document.close()
    return data


def test_text_layer_accepts_digital_pdf():
    assessment = assess_pdf_text_layer(_pdf_with_text())
    assert assessment.needs_ocr is False
    assert assessment.total_chars > 50


def test_scanned_pdf_is_flagged_ocr():
    with pytest.raises(NeedsOcrError, match="scanned resume"):
        require_pdf_text_layer(_pdf_without_text())


def test_cross_validation_marks_email_disagreement_low_confidence():
    extraction = LlmResumeExtraction(
        contact=ContactInfo(email="wrong@example.com", phone="555-111-2222")
    )
    text = "Contact Jane at jane@example.com or +1 555 111 2222. Worked Jan 2020 - Present."
    validated = cross_validate(extraction, text)
    assert validated.field_confidence["contact.email"] == "low"
    assert any(item.field == "contact.email" for item in validated.disagreements)
    assert validated.field_confidence["contact.phone"] == "high"
