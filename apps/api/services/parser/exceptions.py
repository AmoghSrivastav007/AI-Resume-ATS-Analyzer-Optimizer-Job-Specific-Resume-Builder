OCR_USER_MESSAGE = (
    "This looks like a scanned resume. OCR support is coming soon — "
    "please upload a text-based PDF or DOCX."
)


class ParsePipelineError(Exception):
    """Base class for parse pipeline failures."""


class NeedsOcrError(ParsePipelineError):
    def __init__(self, message: str = OCR_USER_MESSAGE) -> None:
        super().__init__(message)
        self.user_message = message
