from dataclasses import dataclass
from typing import Protocol

import httpx

from config import Settings


@dataclass(frozen=True)
class VirusScanResult:
    clean: bool
    detail: str


class VirusScanner(Protocol):
    def scan(self, content: bytes, filename: str) -> VirusScanResult: ...


class NoOpVirusScanner:
    """
    No-op scanner for development only.
    WARNING: This should NEVER be used in production!
    """

    def scan(self, content: bytes, filename: str) -> VirusScanResult:
        import logging
        logging.warning(
            "SECURITY WARNING: Virus scanning is disabled. "
            "Set VIRUS_SCAN_URL in production to enable ClamAV scanning."
        )
        return VirusScanResult(clean=True, detail="Virus scan skipped (no scanner configured - DEVELOPMENT ONLY)")


class HttpVirusScanner:
    def __init__(self, scan_url: str, timeout_seconds: float = 30.0) -> None:
        self.scan_url = scan_url
        self.timeout_seconds = timeout_seconds

    def scan(self, content: bytes, filename: str) -> VirusScanResult:
        response = httpx.post(
            self.scan_url,
            files={"file": (filename, content)},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        clean = bool(payload.get("clean", False))
        detail = str(payload.get("detail", "Scan completed"))
        return VirusScanResult(clean=clean, detail=detail)


def get_virus_scanner(settings: Settings) -> VirusScanner:
    if settings.virus_scan_url:
        return HttpVirusScanner(settings.virus_scan_url)
    return NoOpVirusScanner()
