"""Data cleaning and export utilities."""

import csv
import io
import json


def clean_data(raw: list[dict]) -> list[dict]:
    """Strip whitespace from values and remove duplicates."""
    seen = set()
    cleaned = []
    for item in raw:
        trimmed = {k: v.strip() if isinstance(v, str) else v for k, v in item.items()}
        key = tuple(sorted(trimmed.items()))
        if key not in seen:
            seen.add(key)
            cleaned.append(trimmed)
    return cleaned


def export_data(data: list[dict], fmt: str) -> str:
    """Export data as JSON or CSV string."""
    fmt = fmt.upper()
    if fmt == "JSON":
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif fmt == "CSV":
        if not data:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    else:
        raise ValueError(f"Unsupported format: {fmt}")
