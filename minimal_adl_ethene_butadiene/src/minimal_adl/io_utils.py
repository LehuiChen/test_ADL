from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


class NumpyJSONEncoder(json.JSONEncoder):
    """把 numpy 标量和数组安全地写入 JSON。"""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)


def ensure_dir(path: Path | str) -> Path:
    """确保目录存在，并返回 Path 对象。"""

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path | str) -> Any:
    """读取 JSON 文件。"""

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path | str, payload: Any, indent: int = 2) -> None:
    """写入 JSON 文件。"""

    path = Path(path)
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=indent, ensure_ascii=False, cls=NumpyJSONEncoder)


def write_text(path: Path | str, text: str) -> None:
    """写入普通文本文件。"""

    path = Path(path)
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def write_csv_rows(
    path: Path | str,
    rows: list[dict[str, Any]],
    *,
    fieldnames: list[str] | None = None,
) -> None:
    """把样本级结果写成 CSV，便于 notebook 直接读取。"""

    path = Path(path)
    ensure_dir(path.parent)

    if fieldnames is None:
        ordered_fields: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in ordered_fields:
                    ordered_fields.append(key)
        fieldnames = ordered_fields

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def timestamp_string() -> str:
    """返回统一格式的时间戳字符串。"""

    return datetime.now().isoformat(timespec="seconds")
