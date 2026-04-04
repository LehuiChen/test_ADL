from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


def _json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:  # noqa: BLE001
        return None


def _numeric_fields(rows: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    if not rows:
        return fields
    for key in rows[0].keys():
        values = [_safe_float(row.get(key)) for row in rows]
        if any(value is not None for value in values):
            fields.append(key)
    return fields


def _stats(values: Iterable[float]) -> dict[str, float] | None:
    values = [float(value) for value in values]
    if not values:
        return None
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
    }


def summarize_rows(
    rows: list[dict[str, Any]],
    *,
    top_k: int = 10,
    sort_key_candidates: tuple[str, ...] = ("uncertainty", "uq_at_selection", "abs_error", "time_fs"),
    raw_details_file: str | None = None,
) -> dict[str, Any]:
    numeric_stats: dict[str, dict[str, float]] = {}
    for field in _numeric_fields(rows):
        stats = _stats(value for value in (_safe_float(row.get(field)) for row in rows) if value is not None)
        if stats is not None:
            numeric_stats[field] = stats

    chosen_sort_key = None
    for candidate in sort_key_candidates:
        if any(_safe_float(row.get(candidate)) is not None for row in rows):
            chosen_sort_key = candidate
            break

    representative_rows = rows[:top_k]
    if chosen_sort_key is not None:
        representative_rows = sorted(
            rows,
            key=lambda row: _safe_float(row.get(chosen_sort_key)) if _safe_float(row.get(chosen_sort_key)) is not None else float("-inf"),
            reverse=True,
        )[:top_k]

    time_values = [value for value in (_safe_float(row.get("time_fs")) for row in rows) if value is not None]
    sample_ids = [str(row.get("sample_id")) for row in rows if row.get("sample_id") is not None]
    summary = {
        "count": len(rows),
        "time_range_fs": None if not time_values else {"min": min(time_values), "max": max(time_values)},
        "sample_id_examples": sample_ids[:top_k],
        "numeric_stats": numeric_stats,
        "representative_rows": representative_rows,
    }
    if chosen_sort_key is not None:
        summary["representative_sort_key"] = chosen_sort_key
    if raw_details_file:
        summary["raw_details_file"] = raw_details_file
    return summary


def compress_background_section(
    payload: dict[str, Any],
    *,
    section_key: str,
    threshold: float,
    top_k: int,
    raw_details_file: str | None = None,
    sort_key_candidates: tuple[str, ...] = ("uncertainty", "uq_at_selection", "abs_error", "time_fs"),
) -> dict[str, Any]:
    if section_key not in payload or not isinstance(payload[section_key], list):
        return payload

    section_value = payload[section_key]
    original_size = _json_size(payload)
    section_size = _json_size(section_value)
    if original_size <= 0:
        return payload

    share = section_size / original_size
    if share < threshold:
        return payload

    compressed = dict(payload)
    compressed[section_key] = summarize_rows(
        section_value,
        top_k=top_k,
        raw_details_file=raw_details_file,
        sort_key_candidates=sort_key_candidates,
    )
    compressed.setdefault("background_compression", {})[section_key] = {
        "applied": True,
        "threshold": threshold,
        "estimated_share": share,
    }
    return compressed


def compress_id_list(
    values: list[Any],
    *,
    threshold: float,
    top_k: int,
    raw_details_file: str | None = None,
    enclosing_payload: dict[str, Any] | None = None,
) -> list[Any] | dict[str, Any]:
    if enclosing_payload is None:
        share = 1.0
    else:
        enclosing_size = max(_json_size(enclosing_payload), 1)
        share = _json_size(values) / enclosing_size
    if share < threshold:
        return values
    compressed = {
        "count": len(values),
        "examples": [str(item) for item in values[:top_k]],
    }
    if raw_details_file:
        compressed["raw_details_file"] = raw_details_file
    return compressed


def write_compact_json(
    path: str | Path,
    payload: dict[str, Any],
    *,
    io_write_json,
    section_keys: tuple[str, ...] = (),
    threshold: float = 0.70,
    top_k: int = 10,
    raw_details_file_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    compact_payload = dict(payload)
    raw_details_file_map = raw_details_file_map or {}
    for section_key in section_keys:
        compact_payload = compress_background_section(
            compact_payload,
            section_key=section_key,
            threshold=threshold,
            top_k=top_k,
            raw_details_file=raw_details_file_map.get(section_key),
        )
    io_write_json(path, compact_payload)
    return compact_payload
