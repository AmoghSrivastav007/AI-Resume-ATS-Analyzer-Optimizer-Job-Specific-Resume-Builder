from dataclasses import dataclass

import fitz

from services.parser.exceptions import NeedsOcrError

MIN_CHARS_PER_PAGE = 50


@dataclass(frozen=True)
class TextLayerAssessment:
    page_count: int
    total_chars: int
    chars_per_page: float
    needs_ocr: bool


def assess_pdf_text_layer(content: bytes) -> TextLayerAssessment:
    document = fitz.open(stream=content, filetype="pdf")
    try:
        page_count = document.page_count
        if page_count == 0:
            return TextLayerAssessment(0, 0, 0.0, True)

        total_chars = 0
        for page_index in range(page_count):
            page_text = document.load_page(page_index).get_text("text")
            total_chars += len(page_text.strip())

        chars_per_page = total_chars / page_count
        needs_ocr = chars_per_page < MIN_CHARS_PER_PAGE
        return TextLayerAssessment(page_count, total_chars, chars_per_page, needs_ocr)
    finally:
        document.close()


def require_pdf_text_layer(content: bytes) -> TextLayerAssessment:
    assessment = assess_pdf_text_layer(content)
    if assessment.needs_ocr:
        raise NeedsOcrError()
    return assessment
