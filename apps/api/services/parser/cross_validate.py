import re

from models.extraction import ResumeExtraction
from models.parse import CrossValidationResult, FieldConfidence

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,4}"
)
DATE_RE = re.compile(
    r"\b(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)[.\-]?\s+\d{4}|"
    r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|"
    r"\d{4}(?:[-/]\d{2})?(?:[-/]\d{2})?|"
    r"Present|Current)\b",
    re.IGNORECASE,
)


def extract_regex_facts(plain_text: str) -> dict[str, list[str]]:
    emails = _unique(EMAIL_RE.findall(plain_text))
    phones = _unique(_normalize_phone(match) for match in PHONE_RE.findall(plain_text) if _looks_like_phone(match))
    dates = _unique(match.strip() for match in DATE_RE.findall(plain_text))
    return {"emails": emails, "phones": phones, "dates": dates}


def cross_validate(extraction: ResumeExtraction, plain_text: str) -> CrossValidationResult:
    regex_facts = extract_regex_facts(plain_text)
    disagreements: list[FieldConfidence] = []
    payload = extraction.model_dump()

    disagreements.extend(_reconcile_contact_field(payload, "email", regex_facts["emails"]))
    disagreements.extend(
        _reconcile_contact_field(
            payload,
            "phone",
            regex_facts["phones"],
            normalize=_normalize_phone,
        )
    )
    disagreements.extend(_reconcile_dates(payload, regex_facts["dates"]))

    field_confidence = {item.field: item.confidence for item in disagreements}
    contact = payload.get("contact") or {}
    for field in ("email", "phone"):
        key = f"contact.{field}"
        stored = contact.get(f"{field}_confidence")
        if stored and key not in field_confidence:
            field_confidence[key] = stored

    return CrossValidationResult(
        extraction=payload,
        disagreements=disagreements,
        field_confidence=field_confidence,
    )


def _reconcile_contact_field(
    payload: dict,
    field: str,
    regex_values: list[str],
    normalize=lambda value: value.lower().strip(),
) -> list[FieldConfidence]:
    llm_value = (payload.get("contact") or {}).get(field)
    if not llm_value and not regex_values:
        return []

    llm_normalized = normalize(llm_value) if llm_value else None
    regex_normalized = [normalize(value) for value in regex_values]

    if llm_normalized and regex_normalized and llm_normalized not in regex_normalized:
        payload["contact"][f"{field}_confidence"] = "low"
        payload["contact"][f"{field}_regex_candidates"] = regex_values
        return [
            FieldConfidence(
                field=f"contact.{field}",
                llm_value=llm_value,
                regex_values=regex_values,
                confidence="low",
                reason="LLM value not found among regex matches",
            )
        ]

    if not llm_normalized and regex_normalized:
        payload["contact"][f"{field}_confidence"] = "low"
        payload["contact"][f"{field}_regex_candidates"] = regex_values
        return [
            FieldConfidence(
                field=f"contact.{field}",
                llm_value=None,
                regex_values=regex_values,
                confidence="low",
                reason="Regex found values the LLM did not extract",
            )
        ]

    if llm_normalized:
        payload["contact"][f"{field}_confidence"] = "high"
    return []


def _reconcile_dates(payload: dict, regex_dates: list[str]) -> list[FieldConfidence]:
    disagreements: list[FieldConfidence] = []
    llm_dates: list[tuple[str, str | None]] = []

    for index, item in enumerate(payload.get("work_experience") or []):
        llm_dates.append((f"work_experience[{index}].start_date", item.get("start_date")))
        llm_dates.append((f"work_experience[{index}].end_date", item.get("end_date")))
    for index, item in enumerate(payload.get("education") or []):
        llm_dates.append((f"education[{index}].start_date", item.get("start_date")))
        llm_dates.append((f"education[{index}].end_date", item.get("end_date")))
    for index, item in enumerate(payload.get("certifications") or []):
        llm_dates.append((f"certifications[{index}].issue_date", item.get("issue_date")))
        llm_dates.append((f"certifications[{index}].expiry_date", item.get("expiry_date")))
    for index, item in enumerate(payload.get("projects") or []):
        llm_dates.append((f"projects[{index}].start_date", item.get("start_date")))
        llm_dates.append((f"projects[{index}].end_date", item.get("end_date")))

    regex_normalized = {_normalize_date_token(value) for value in regex_dates}

    for path, llm_value in llm_dates:
        if not llm_value:
            continue
        if _normalize_date_token(llm_value) not in regex_normalized and not _date_loosely_matches(
            llm_value, regex_dates
        ):
            _set_nested_confidence(payload, path, regex_dates)
            disagreements.append(
                FieldConfidence(
                    field=path,
                    llm_value=llm_value,
                    regex_values=regex_dates,
                    confidence="low",
                    reason="LLM date not found in regex date matches",
                )
            )
        else:
            _set_nested_confidence(payload, path, regex_dates, confidence="high")

    return disagreements


def _set_nested_confidence(
    payload: dict,
    path: str,
    regex_values: list[str],
    confidence: str = "low",
) -> None:
    # path format: collection[index].field
    collection_name, rest = path.split("[", 1)
    index_str, field = rest.split("].", 1)
    item = payload[collection_name][int(index_str)]
    item[f"{field}_confidence"] = confidence
    if confidence == "low":
        item[f"{field}_regex_candidates"] = regex_values


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


def _looks_like_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 10 <= len(digits) <= 15


def _phones_match(llm_digits: str, regex_digits: list[str]) -> bool:
    if not llm_digits:
        return False
    for candidate in regex_digits:
        if not candidate:
            continue
        if llm_digits == candidate:
            return True
        if llm_digits[-10:] == candidate[-10:] and min(len(llm_digits), len(candidate)) >= 10:
            return True
    return False


def _normalize_phone(value: str | None) -> str:
    if not value:
        return ""
    digits = re.sub(r"\D", "", value)
    if len(digits) > 10 and digits.startswith("1"):
        digits = digits[-10:]
    return digits[-10:] if len(digits) >= 10 else digits


def _normalize_date_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _date_loosely_matches(llm_value: str, regex_dates: list[str]) -> bool:
    llm_digits = re.sub(r"\D", "", llm_value)
    if len(llm_digits) >= 4:
        year = llm_digits[:4]
        return any(year in re.sub(r"\D", "", candidate) for candidate in regex_dates)
    llm_norm = _normalize_date_token(llm_value)
    return any(llm_norm in _normalize_date_token(candidate) for candidate in regex_dates)
