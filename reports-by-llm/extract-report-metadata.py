#!/usr/bin/env python3

"""
Extract strict metadata from reports-by-llm using a local Ollama server.

The extractor:
- knows the five report types and their metadata schemas
- sends one extraction request per document
- asks the LLM only for fields requiring language understanding
- supplies document/document_type itself
- validates returned JSON
- normalizes simple values
- retries failed requests
- writes one metadata.json per document type
- supports interrupted/resumed runs
- never silently converts extraction failures into null metadata

Requires:
    pip install requests

Example:
    python extract-report-metadata.py \
        --input ./reports-by-llm \
        --output ./reports-by-llm-metadata \
        --model qwen2.5:3b

For a sample:
    python extract-report-metadata.py \
        --input ./reports-sample \
        --output ./reports-sample-metadata \
        --model qwen2.5:3b

Set --ollama-url if Ollama is not at http://localhost:11434.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


# ---------------------------------------------------------------------------
# Metadata definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Field:
    type: str
    description: str


@dataclass(frozen=True)
class DocumentType:
    document_type: str
    fields: dict[str, Field]


DOCUMENT_TYPES: dict[str, DocumentType] = {
    "building_inspections": DocumentType(
        document_type="building_inspection",
        fields={
            "inspection_date": Field(
                "date",
                "Date on which the building inspection occurred. "
                "Do not use report, signing, construction, renovation, "
                "or other dates.",
            ),
            "country": Field(
                "string",
                "Explicitly stated country containing the inspected property. "
                "Do not infer it from municipality, address, postal code, "
                "language, or other context.",
            ),
            "municipality": Field(
                "string",
                "Explicitly stated municipality, city, town, or equivalent "
                "locality containing the inspected building.",
            ),
            "address": Field(
                "string",
                "Explicit address of the inspected building.",
            ),
            "inspector_name": Field(
                "string",
                "Person explicitly identified as conducting or being "
                "responsible for the inspection.",
            ),
            "building_type": Field(
                "string",
                "Explicitly stated building type or use. Do not classify "
                "the building yourself.",
            ),
            "construction_year": Field(
                "integer",
                "Explicitly stated year of original construction. "
                "Do not calculate it from building age or use a renovation year.",
            ),
            "number_of_floors": Field(
                "integer",
                "Explicitly stated number of floors or storeys. "
                "Do not count floors from narrative descriptions.",
            ),
            "primary_materials": Field(
                "string",
                "Explicitly stated primary building or construction materials.",
            ),
        },
    ),

    "doctor_visits": DocumentType(
        document_type="doctor_visit",
        fields={
            "visit_date": Field(
                "date",
                "Date on which the medical visit occurred. Do not use report, "
                "symptom onset, previous treatment, laboratory, or follow-up dates.",
            ),
            "location": Field(
                "string",
                "Explicitly identified location or facility of the visit.",
            ),
            "patient_age": Field(
                "integer",
                "Explicitly stated patient age in years. "
                "Do not calculate age from date of birth.",
            ),
            "patient_gender": Field(
                "string",
                "Explicitly stated patient gender or sex. "
                "Do not infer it from name, pronouns, diagnosis, or context.",
            ),
            "severity_level": Field(
                "integer",
                "Explicit numeric severity level associated with the visit. "
                "Do not determine severity from symptoms, diagnosis, urgency, "
                "treatment, or narrative.",
            ),
        },
    ),

    "project_updates": DocumentType(
        document_type="project_update",
        fields={
            "project_title": Field(
                "string",
                "Explicitly stated project name or title.",
            ),
            "company_name": Field(
                "string",
                "Explicitly identified company or organization responsible "
                "for the project.",
            ),
            "report_date": Field(
                "date",
                "Explicit date assigned to the project update or report. "
                "Do not use milestone, meeting, deadline, or reporting-period dates.",
            ),
            "reporting_period": Field(
                "string",
                "Explicitly stated reporting period. Preserve the source wording. "
                "Do not derive it from another date.",
            ),
            "quarter": Field(
                "string",
                "Explicitly stated reporting quarter, such as Q2 2026. "
                "Do not calculate the quarter from a date.",
            ),
            "project_manager": Field(
                "string",
                "Person explicitly identified as project manager. "
                "Do not treat 'Prepared by', author, sponsor, or technical lead "
                "as project manager unless explicitly identified as such.",
            ),
            "percentage_complete": Field(
                "number",
                "Explicit overall project completion percentage, represented "
                "as a number from 0 to 100. Do not calculate it from tasks "
                "or milestones.",
            ),
        },
    ),

    "social_services_visit": DocumentType(
        document_type="social_services_visit",
        fields={
            "visit_date": Field(
                "date",
                "Date on which the social services visit occurred.",
            ),
            "location": Field(
                "string",
                "Explicitly identified location of the visit.",
            ),
            "address": Field(
                "string",
                "Explicit street or postal address associated with the visit.",
            ),
            "visit_type": Field(
                "string",
                "Explicitly stated type of social services visit. "
                "Do not classify it from the narrative.",
            ),
            "client_name": Field(
                "string",
                "Person explicitly identified as the client or service recipient.",
            ),
            "case_severity": Field(
                "string",
                "Explicitly stated case severity or category. "
                "Do not assess severity from circumstances in the report.",
            ),
            "next_follow_up_date": Field(
                "date",
                "Explicit concrete date for the next follow-up. "
                "Do not calculate dates from relative expressions such as "
                "'next week' or 'in three months'.",
            ),
        },
    ),

    "traffic_incidents": DocumentType(
        document_type="traffic_incident",
        fields={
            "incident_date": Field(
                "date",
                "Explicit date on which the traffic incident occurred.",
            ),
            "incident_time": Field(
                "time",
                "Explicit time at which the incident occurred. "
                "Do not substitute dispatch, arrival, interview, or report times.",
            ),
            "location": Field(
                "string",
                "Explicitly stated incident location.",
            ),
            "municipality": Field(
                "string",
                "Explicitly stated municipality, city, or town of the incident. "
                "Do not infer it from roads or geographical knowledge.",
            ),
            "incident_number": Field(
                "string",
                "Explicitly identified incident, report, or case identifier.",
            ),
            "incident_type": Field(
                "string",
                "Explicitly stated incident type or category. "
                "Do not classify the incident from its narrative.",
            ),
            "reporting_officer": Field(
                "string",
                "Person explicitly identified as the reporting or investigating officer.",
            ),
            "number_of_vehicles": Field(
                "integer",
                "Explicitly stated number of vehicles involved. "
                "Do not count vehicles mentioned in the narrative.",
            ),
            "weather_conditions": Field(
                "string",
                "Explicitly stated weather conditions at the incident.",
            ),
            "road_conditions": Field(
                "string",
                "Explicitly stated road or surface conditions. "
                "Do not infer them from weather.",
            ),
        },
    ),
}


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You extract one metadata value from a document.

Rules:
1. Extract only information explicitly supported by the document.
2. Never guess, infer, calculate, classify, summarize, or invent.
3. If the requested value is absent or ambiguous, return null.
4. Preserve the extracted value as written in the document.
5. Return JSON only in exactly this form:
   {"value": value}

It is better to return null than an uncertain value.
""".strip()


def build_field_prompt(
    document_type: DocumentType,
    field_name: str,
    field: Field,
    document_text: str,
) -> str:

    return f"""
Document type: {document_type.document_type}

Field to extract: {field_name}

Definition:
{field.description}

Extract ONLY this field.

Important:
- Look specifically for information matching the field definition.
- Explicit labels such as "Visit Date:", "Inspection Date:",
  "Location:", etc. are strong evidence.
- Preserve the value as written in the document.
- Do not normalize dates, times, numbers, names, or other values.
- Do not derive the value from another field.
- If the value is not explicitly supported, return null.

Return exactly:

{{"value": value}}

DOCUMENT START
----------------
{document_text}
----------------
DOCUMENT END
""".strip()

def build_prompt(document_type: DocumentType, document_text: str) -> str:
    field_lines = []

    for name, field in document_type.fields.items():
        field_lines.append(
            f'- "{name}" ({field.type} or null): {field.description}'
        )

    fields = "\n".join(field_lines)

    example_object = {
        name: None
        for name in document_type.fields
    }

    return f"""
Document type: {document_type.document_type}

Extract these metadata fields:

{fields}

Required JSON shape:

{json.dumps(example_object, indent=2)}

Remember:
- Every field above must be present.
- Use null when an explicitly supported value cannot be found.
- Do not add fields.
- Do not infer missing values.

DOCUMENT START
----------------
{document_text}
----------------
DOCUMENT END
""".strip()


# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------

class ExtractionError(RuntimeError):
    pass

def call_ollama(
    session: requests.Session,
    base_url: str,
    model: str,
    prompt: str,
    timeout: int,
) -> Any:

    url = base_url.rstrip("/") + "/api/chat"

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "seed": 42,
        },
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        #response = session.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExtractionError(f"Ollama request failed: {exc}") from exc

    try:
        outer = response.json()
    except ValueError as exc:
        raise ExtractionError(
            "Ollama returned invalid HTTP JSON"
        ) from exc

    try:
        content = outer["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise ExtractionError(
            "Ollama response does not contain message.content"
        ) from exc

    try:
        result = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ExtractionError(
            f"Model returned invalid JSON: {content[:500]}"
        ) from exc

    if not isinstance(result, dict):
        raise ExtractionError(
            f"Model result is not a JSON object: {result!r}"
        )

    if set(result.keys()) != {"value"}:
        raise ExtractionError(
            f"Expected exactly {{'value': ...}}, got: {result!r}"
        )

    return result["value"]


def call_ollama_old(
    session: requests.Session,
    base_url: str,
    model: str,
    prompt: str,
    timeout: int,
) -> dict[str, Any]:

    url = base_url.rstrip("/") + "/api/chat"

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "seed": 42,
        },
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    try:
        response = session.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExtractionError(f"Ollama request failed: {exc}") from exc

    try:
        outer = response.json()
    except ValueError as exc:
        raise ExtractionError("Ollama returned invalid HTTP JSON") from exc

    try:
        content = outer["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise ExtractionError(
            "Ollama response does not contain message.content"
        ) from exc

    try:
        result = json.loads(content)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ExtractionError(
            f"Model returned invalid JSON: {content[:500]}"
        ) from exc

    if not isinstance(result, dict):
        raise ExtractionError("Model result is not a JSON object")

    return result


# ---------------------------------------------------------------------------
# Validation and normalization
# ---------------------------------------------------------------------------
def normalize_date(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(
            f"Expected date string, got {value!r}"
        )

    value = value.strip()

    # Remove ordinal suffixes.
    value = re.sub(
        r"\b(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        value,
        flags=re.IGNORECASE,
    )

    relative_date_patterns = (
        r"\bwithin\b",
        r"\bnext\s+(day|week|month|year)\b",
        r"\bin\s+\d+\s+(day|days|week|weeks|month|months|year|years)\b",
        r"\bafter\s+\d+\s+(day|days|week|weeks|month|months|year|years)\b",
        r"\b\d+\s+(day|days|week|weeks|month|months|year|years)\s+from\s+today\b",
    )

    for pattern in relative_date_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return None

    # Extract leading numeric date from a combined date/time value.
    match = re.match(
        r"^\s*(\d{1,4}[./-]\d{1,2}[./-]\d{1,4})",
        value,
    )

    if match:
        value = match.group(1)

    formats = (
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    )

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

    raise ExtractionError(
        f"Unrecognized date format: {value!r}"
    )


def extract_summary(
    *,
    session: requests.Session,
    document_type: DocumentType,
    document_text: str,
    ollama_url: str,
    model: str,
    timeout: int,
    retries: int,
) -> str | None:
    """
    Generate a short factual summary of the document.

    Unlike normal metadata extraction, this intentionally allows
    summarization, but must not introduce information that is not
    supported by the source document.
    """

    system_prompt = """You create concise factual document summaries.

Rules:
1. Summarize only information supported by the document.
2. Do not guess, infer, or invent facts.
3. Write 1-2 concise sentences.
4. Describe the main subject and the most important information,
   findings, events, or outcome.
5. Do not start with phrases such as "This document", "This report",
   "The document", or "The report".
6. Do not simply repeat the document type.
7. Return JSON only in exactly this form:
   {"value": "summary"}
"""

    user_prompt = f"""Document type: {document_type.document_type}

Write a concise factual summary of the following document.

DOCUMENT START
----------------
{document_text}
----------------
DOCUMENT END
"""

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            raw_value = call_ollama(
                session=session,
                base_url=ollama_url,
                model=model,
                prompt=system_prompt + "\n\n" +user_prompt,
                timeout=timeout,
            )

            return normalize_string(raw_value)

        except ExtractionError as exc:
            last_error = exc

            if attempt < retries:
                print(
                    f"        retry {attempt}/{retries}: {exc}",
                    file=sys.stderr,
                )

    raise ExtractionError(
        f"Summary failed after {retries} attempts: {last_error}"
    )


def extract_field(
    session: requests.Session,
    document_type: DocumentType,
    field_name: str,
    field: Field,
    document_text: str,
    ollama_url: str,
    model: str,
    timeout: int,
    retries: int,
) -> Any:

    prompt = build_field_prompt(
        document_type=document_type,
        field_name=field_name,
        field=field,
        document_text=document_text,
    )

    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            raw_value = call_ollama(
                session=session,
                base_url=ollama_url,
                model=model,
                prompt=prompt,
                timeout=timeout,
            )

            return normalize_value(
                field_name,
                field,
                raw_value,
            )

        except ExtractionError as exc:
            last_error = exc

            if attempt < retries:
                print(
                    f"        retry {attempt}/{retries}: {exc}",
                    file=sys.stderr,
                )
                time.sleep(min(attempt * 2, 10))

    raise ExtractionError(
        f"Field {field_name!r} failed after "
        f"{retries} attempts: {last_error}"
    )

def generate_title(
    document_type: str,
    metadata: dict[str, Any],
) -> str:
    """
    Generate a deterministic human-readable title from extracted metadata.

    Missing values are simply omitted.
    """

    if document_type == "building_inspection":
        parts = [
            metadata.get("building_type"),
            metadata.get("municipality"),
            metadata.get("inspection_date"),
        ]

    elif document_type == "doctor_visit":
        parts = [
            metadata.get("location"),
            metadata.get("visit_date"),
        ]

    elif document_type == "project_update":
        period = (
            metadata.get("quarter")
            or metadata.get("reporting_period")
            or metadata.get("report_date")
        )

        parts = [
            metadata.get("project_title"),
            period,
        ]

    elif document_type == "social_services_visit":
        parts = [
            metadata.get("visit_type"),
            metadata.get("location"),
            metadata.get("visit_date"),
        ]

    elif document_type == "traffic_incident":
        parts = [
            metadata.get("incident_type"),
            metadata.get("municipality"),
            metadata.get("incident_date"),
        ]

    else:
        parts = []

    parts = [
        str(value).strip()
        for value in parts
        if value is not None and str(value).strip()
    ]

    if parts:
        return " - ".join(parts)

    # Very unlikely, but title should always exist.
    return document_type.replace("_", " ").title()

def normalize_value(
    field_name: str,
    field: Field,
    value: Any,
) -> Any:

    if field.type == "string":
        value = normalize_string(value)

    elif field.type == "date":
        value = normalize_date(value)

    elif field.type == "time":
        value = normalize_time(value)

    elif field.type == "integer":
        value = normalize_integer(value)

    elif field.type == "number":
        value = normalize_number(value)

    else:
        raise RuntimeError(
            f"Unknown field type: {field.type}"
        )

    # Deterministic field-specific validation.

    if field_name == "construction_year":
        if value is not None and not 1000 <= value <= 2100:
            raise ExtractionError(
                f"Invalid construction year: {value}"
            )

    elif field_name == "number_of_floors":
        if value is not None and value < 1:
            raise ExtractionError(
                f"Invalid number of floors: {value}"
            )

    elif field_name == "patient_age":
        if value is not None and not 0 <= value <= 130:
            raise ExtractionError(
                f"Invalid patient age: {value}"
            )

    elif field_name == "severity_level":
        if value is not None and value < 0:
            raise ExtractionError(
                f"Invalid severity level: {value}"
            )

    elif field_name == "percentage_complete":
        if value is not None and not 0 <= value <= 100:
            raise ExtractionError(
                f"Invalid completion percentage: {value}"
            )

    elif field_name == "number_of_vehicles":
        if value is not None and value < 0:
            raise ExtractionError(
                f"Invalid vehicle count: {value}"
            )

    return value


def normalize_date_old(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(f"Expected date string, got {value!r}")

    value = value.strip()

    formats = (
        "%Y-%m-%d",   # 2025-06-25
        "%d.%m.%Y",   # 25.06.2025
        "%d/%m/%Y",   # 25/06/2025
        "%d-%m-%Y",   # 25-06-2025
        "%Y/%m/%d",   # 2025/06/25
        "%B %d, %Y",  # June 25, 2025
        "%b %d, %Y",  # Jun 25, 2025
        "%d %B %Y",   # 25 June 2025
        "%d %b %Y",   # 25 Jun 2025
    )

    for fmt in formats:
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

    raise ExtractionError(f"Unrecognized date format: {value!r}")


def normalize_date_old1(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(f"Expected date string, got {value!r}")

    value = value.strip()

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ExtractionError(f"Invalid ISO date: {value!r}") from exc

    return parsed.strftime("%Y-%m-%d")

def normalize_time(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(f"Expected time string, got {value!r}")

    text = value.strip()

    # 24-hour time :
    # "20:48 hours"
    match = re.search(
        r"\b(\d{1,2}):(\d{2})(?::\d{2})?\b",
        text,
    )
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))

        # Check whether AM/PM follows.
        ampm = re.search(r"\b(AM|PM)\b", text, re.IGNORECASE)

        if ampm:
            if not 1 <= hour <= 12:
                raise ExtractionError(f"Invalid 12-hour time: {value!r}")

            marker = ampm.group(1).upper()

            if marker == "AM":
                hour = 0 if hour == 12 else hour
            else:
                hour = 12 if hour == 12 else hour + 12

        elif not 0 <= hour <= 23:
            raise ExtractionError(f"Invalid hour: {value!r}")

        if not 0 <= minute <= 59:
            raise ExtractionError(f"Invalid minute: {value!r}")

        return f"{hour:02d}:{minute:02d}"

    raise ExtractionError(
        f"Cannot normalize time: {value!r}"
    )


def normalize_time_old(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(f"Expected time string, got {value!r}")

    value = value.strip()

    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.strftime("%H:%M")
        except ValueError:
            pass

    raise ExtractionError(f"Invalid time: {value!r}")


def normalize_string(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(f"Expected string, got {value!r}")

    value = value.strip()

    if not value:
        return None

    # Small LLMs occasionally return textual null values instead
    # of the JSON null value.
    if value.lower() in {
        "null",
        "none",
        "n/a",
        "na",
        "not available",
        "not specified",
        "unknown",
    }:
        return None

    return value

def normalize_string_old(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ExtractionError(f"Expected string, got {value!r}")

    value = value.strip()

    if not value:
        return None

    return value


NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def normalize_integer(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise ExtractionError(f"Expected integer, got {value!r}")

    if isinstance(value, int):
        return value

    if not isinstance(value, str):
        raise ExtractionError(f"Expected integer, got {value!r}")

    text = value.strip()

    # Exact integer
    if re.fullmatch(r"-?\d+", text):
        return int(text)

    # One integer in text
    numbers = re.findall(r"(?<!\d)[+-]?\d+(?!\d)", text)
    if len(numbers) == 1:
        return int(numbers[0])

    # Leading numeric value:
    # "4 (Less-urgent – stable, 1 resource)" -> 4
    match = re.match(r"^\s*(-?\d+)\b", text)
    if match:
        return int(match.group(1))

    # Explicit parenthesized number:
    # "Three (3)" -> 3
    match = re.search(r"\((-?\d+)\)", text)
    if match:
        return int(match.group(1))

    # Number word at beginning:
    # "Two-story building..." -> 2
    match = re.match(r"^\s*([A-Za-z]+)", text)
    if match:
        word = match.group(1).lower()
        if word in NUMBER_WORDS:
            return NUMBER_WORDS[word]

    raise ExtractionError(
        f"Cannot unambiguously normalize integer: {value!r}"
    )


def normalize_integer_old(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise ExtractionError(f"Expected integer, got {value!r}")

    if isinstance(value, int):
        return value

    # Small models occasionally return "42" despite instructions.
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value.strip()):
        return int(value.strip())

    raise ExtractionError(f"Expected integer, got {value!r}")


def normalize_number(value: Any) -> int | float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        raise ExtractionError(f"Expected number, got {value!r}")

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        text = value.strip().rstrip("%").strip()

        try:
            number = float(text)
        except ValueError as exc:
            raise ExtractionError(f"Expected number, got {value!r}") from exc

        return int(number) if number.is_integer() else number

    raise ExtractionError(f"Expected number, got {value!r}")


def validate_result(
    definition: DocumentType,
    result: dict[str, Any],
) -> dict[str, Any]:

    expected = set(definition.fields)
    actual = set(result)

    missing = expected - actual
    extra = actual - expected

    if missing:
        raise ExtractionError(
            f"Model omitted fields: {', '.join(sorted(missing))}"
        )

    if extra:
        raise ExtractionError(
            f"Model added unexpected fields: {', '.join(sorted(extra))}"
        )

    normalized: dict[str, Any] = {}

    for name, field in definition.fields.items():
        value = result[name]

        if field.type == "string":
            value = normalize_string(value)

        elif field.type == "date":
            value = normalize_date(value)

        elif field.type == "time":
            value = normalize_time(value)

        elif field.type == "integer":
            value = normalize_integer(value)

        elif field.type == "number":
            value = normalize_number(value)

        else:
            raise RuntimeError(f"Unknown field type: {field.type}")

        normalized[name] = value

    # Field-specific deterministic checks.

    if "construction_year" in normalized:
        year = normalized["construction_year"]
        if year is not None and not 1000 <= year <= 2100:
            raise ExtractionError(
                f"Invalid construction year: {year}"
            )

    if "number_of_floors" in normalized:
        floors = normalized["number_of_floors"]
        if floors is not None and floors < 1:
            raise ExtractionError(
                f"Invalid number of floors: {floors}"
            )

    if "patient_age" in normalized:
        age = normalized["patient_age"]
        if age is not None and not 0 <= age <= 130:
            raise ExtractionError(
                f"Invalid patient age: {age}"
            )

    if "severity_level" in normalized:
        severity = normalized["severity_level"]
        if severity is not None and severity < 0:
            raise ExtractionError(
                f"Invalid severity level: {severity}"
            )

    if "percentage_complete" in normalized:
        percentage = normalized["percentage_complete"]
        if percentage is not None and not 0 <= percentage <= 100:
            raise ExtractionError(
                f"Invalid completion percentage: {percentage}"
            )

    if "number_of_vehicles" in normalized:
        vehicles = normalized["number_of_vehicles"]
        if vehicles is not None and vehicles < 0:
            raise ExtractionError(
                f"Invalid vehicle count: {vehicles}"
            )

    return normalized


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_existing(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Cannot read existing metadata file {path}: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise RuntimeError(f"{path} must contain a JSON array")

    result = {}

    for item in data:
        if not isinstance(item, dict):
            raise RuntimeError(f"Invalid metadata record in {path}")

        document = item.get("document")

        if not isinstance(document, str):
            raise RuntimeError(
                f"Metadata record without valid document in {path}"
            )

        if document in result:
            raise RuntimeError(
                f"Duplicate document {document!r} in {path}"
            )

        result[document] = item

    return result


def write_metadata(
    path: Path,
    records: dict[str, dict[str, Any]],
) -> None:

    path.parent.mkdir(parents=True, exist_ok=True)

    ordered = [
        records[name]
        for name in sorted(records)
    ]

    temporary = path.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(
            ordered,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def extract_document(
    session: requests.Session,
    source: Path,
    definition: DocumentType,
    ollama_url: str,
    model: str,
    timeout: int,
    retries: int,
) -> dict[str, Any]:

    text = source.read_text(encoding="utf-8")

    result: dict[str, Any] = {
        "document": source.name,
        "document_type": definition.document_type,
    }

    # for field_name, field in definition.fields.items():

    #     print(f"    {field_name}...", end="", flush=True)

    #     value = extract_field(
    #         session=session,
    #         document_type=definition,
    #         field_name=field_name,
    #         field=field,
    #         document_text=text,
    #         ollama_url=ollama_url,
    #         model=model,
    #         timeout=timeout,
    #         retries=retries,
    #     )

    #     result[field_name] = value

    #     if value is None:
    #         print(" null")
    #     else:
    #         print(f" {value!r}")

    for field_name, field in definition.fields.items():

        print(f"    {field_name}...", end="", flush=True)

        try:
            value = extract_field(
                session=session,
                document_type=definition,
                field_name=field_name,
                field=field,
                document_text=text,
                ollama_url=ollama_url,
                model=model,
                timeout=timeout,
                retries=retries,
            )
        except (ExtractionError, requests.RequestException, TimeoutError, OSError) as exc:
            print(
                f" ERROR: {type(exc).__name__}: {exc} -> null",
                file=sys.stderr,
            )
            value = None
    
        # except ExtractionError as exc:
        #     print(
        #         f" ERROR: {exc} -> null",
        #         file=sys.stderr,
        #     )
        #     value = None

        result[field_name] = value

        if value is None:
            print(" null")
        else:
            print(f" {value!r}")

    # Generate deterministic title from the normalized metadata.
    result["title"] = generate_title(
        definition.document_type,
        result,
    )

    print(f"    title... {result['title']!r}")

    # Generate short semantic summary from the original document.
    print("    summary...", end="", flush=True)

    try:
        summary = extract_summary(
            session=session,
            document_type=definition,
            document_text=text,
            ollama_url=ollama_url,
            model=model,
            timeout=timeout,
            retries=retries,
        )

    except (ExtractionError, requests.RequestException, TimeoutError, OSError) as exc:
        print(
            f" ERROR: {type(exc).__name__}: {exc} -> null",
            file=sys.stderr,
        )
        summary = None

    result["summary"] = summary

    if summary is None:
        print(" null")
    else:
        print(f" {summary!r}")

    return result


def extract_document_old(
    session: requests.Session,
    source: Path,
    definition: DocumentType,
    ollama_url: str,
    model: str,
    timeout: int,
    retries: int,
) -> dict[str, Any]:

    text = source.read_text(encoding="utf-8")

    prompt = build_prompt(definition, text)

    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            raw = call_ollama(
                session=session,
                base_url=ollama_url,
                model=model,
                prompt=prompt,
                timeout=timeout,
            )

            extracted = validate_result(definition, raw)

            return {
                "document": source.name,
                "document_type": definition.document_type,
                **extracted,
            }

        except ExtractionError as exc:
            last_error = exc

            if attempt < retries:
                print(
                    f"    retry {attempt}/{retries}: {exc}",
                    file=sys.stderr,
                )
                time.sleep(min(attempt * 2, 10))

    raise ExtractionError(
        f"Extraction failed after {retries} attempts: {last_error}"
    )


def process_directory(
    session: requests.Session,
    input_dir: Path,
    output_dir: Path,
    directory_name: str,
    definition: DocumentType,
    ollama_url: str,
    model: str,
    timeout: int,
    retries: int,
    force: bool,
    limit: int | None,
) -> tuple[int, int, int]:

    source_dir = input_dir / directory_name

    if not source_dir.is_dir():
        print(
            f"WARNING: source directory does not exist: {source_dir}",
            file=sys.stderr,
        )
        return 0, 0, 0

    metadata_path = output_dir / directory_name / "metadata.json"

    records = load_existing(metadata_path)

    documents = sorted(source_dir.glob("*.md"))

    if limit is not None:
        documents = random.sample(documents,limit)#documents[:limit]

    completed = 0
    skipped = 0
    failed = 0

    print()
    print(
        f"{directory_name}: "
        f"{len(documents)} document(s), "
        f"{len(records)} existing record(s)"
    )

    for index, document in enumerate(documents, start=1):

        if not force and document.name in records:
            skipped += 1
            print(
                f"[{index}/{len(documents)}] "
                f"{document.name} - already extracted"
            )
            continue

        print(
            f"[{index}/{len(documents)}] "
            f"{document.name}"
        )

        try:
            record = extract_document(
                session=session,
                source=document,
                definition=definition,
                ollama_url=ollama_url,
                model=model,
                timeout=timeout,
                retries=retries,
            )

        except (ExtractionError, OSError) as exc:
            failed += 1
            print(
                f"    ERROR: {exc}",
                file=sys.stderr,
            )
            continue

        records[document.name] = record

        # Save after every successful document. This makes the run resumable
        # even if it is interrupted immediately afterwards.
        write_metadata(metadata_path, records)

        completed += 1

    return completed, skipped, failed


# ---------------------------------------------------------------------------
# Final dataset validation
# ---------------------------------------------------------------------------

def validate_dataset(
    input_dir: Path,
    output_dir: Path,
) -> bool:

    valid = True

    print()
    print("Dataset validation")
    print("------------------")

    total_documents = 0
    total_records = 0

    for directory_name, definition in DOCUMENT_TYPES.items():

        source_dir = input_dir / directory_name
        metadata_path = output_dir / directory_name / "metadata.json"

        if not source_dir.is_dir():
            print(f"{directory_name}: source directory missing")
            valid = False
            continue

        documents = {
            path.name
            for path in source_dir.glob("*.md")
        }

        total_documents += len(documents)

        if not metadata_path.exists():
            print(f"{directory_name}: metadata.json missing")
            valid = False
            continue

        try:
            records = load_existing(metadata_path)
        except RuntimeError as exc:
            print(f"{directory_name}: INVALID: {exc}")
            valid = False
            continue

        total_records += len(records)

        record_names = set(records)

        missing = documents - record_names
        extra = record_names - documents

        if missing:
            print(
                f"{directory_name}: "
                f"{len(missing)} document(s) missing metadata"
            )
            valid = False

        if extra:
            print(
                f"{directory_name}: "
                f"{len(extra)} metadata record(s) without source document"
            )
            valid = False

        expected_fields = {
            "document",
            "document_type",
            "title",
            "summary",
            *definition.fields.keys(),
        }

        for filename, record in records.items():

            actual_fields = set(record)

            if actual_fields != expected_fields:
                print(
                    f"{directory_name}/{filename}: "
                    f"incorrect field set"
                )
                valid = False

            if record.get("document_type") != definition.document_type:
                print(
                    f"{directory_name}/{filename}: "
                    f"incorrect document_type"
                )
                valid = False

        if not missing and not extra:
            print(
                f"{directory_name}: "
                f"{len(documents)} documents / "
                f"{len(records)} records - OK"
            )

    print()
    print(f"Source documents: {total_documents}")
    print(f"Metadata records: {total_records}")

    if valid and total_documents == total_records:
        print("Validation: OK")
    else:
        print("Validation: FAILED")

    return valid


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description="Extract metadata from reports-by-llm using Ollama."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input directory containing report-type subdirectories.",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory for metadata.",
    )

    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434).",
    )

    parser.add_argument(
        "--model",
        default="qwen2.5:3b",
        help="Ollama model name.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Request timeout in seconds (default: 180).",
    )

    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Attempts per document (default: 3).",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-extract documents that already have metadata.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Process at most N documents per document type.",
    )

    parser.add_argument(
        "--type",
        choices=sorted(DOCUMENT_TYPES),
        help="Process only one document type directory.",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Do not run extraction; validate existing metadata.",
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    input_dir = args.input.resolve()
    output_dir = args.output.resolve()

    if not input_dir.is_dir():
        print(
            f"Input directory does not exist: {input_dir}",
            file=sys.stderr,
        )
        return 2

    if args.validate_only:
        return 0 if validate_dataset(input_dir, output_dir) else 1

    selected = DOCUMENT_TYPES

    if args.type:
        selected = {
            args.type: DOCUMENT_TYPES[args.type]
        }

    print(f"Input:      {input_dir}")
    print(f"Output:     {output_dir}")
    print(f"Ollama:     {args.ollama_url}")
    print(f"Model:      {args.model}")

    total_completed = 0
    total_skipped = 0
    total_failed = 0

    with requests.Session() as session:

        for directory_name, definition in selected.items():

            completed, skipped, failed = process_directory(
                session=session,
                input_dir=input_dir,
                output_dir=output_dir,
                directory_name=directory_name,
                definition=definition,
                ollama_url=args.ollama_url,
                model=args.model,
                timeout=args.timeout,
                retries=args.retries,
                force=args.force,
                limit=args.limit,
            )

            total_completed += completed
            total_skipped += skipped
            total_failed += failed

    print()
    print("Extraction complete")
    print("-------------------")
    print(f"Extracted: {total_completed}")
    print(f"Skipped:   {total_skipped}")
    print(f"Failed:    {total_failed}")

    if total_failed:
        print()
        print(
            "Some documents failed. Run the same command again; "
            "successful documents will be skipped."
        )
        return 1

    # Only perform full dataset validation when the run wasn't deliberately
    # restricted.
    if args.limit is None and args.type is None:
        return 0 if validate_dataset(input_dir, output_dir) else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())