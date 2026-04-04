from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .io_utils import ensure_dir, read_json, write_json

SYMBOL_TO_ATOMIC_NUMBER = {
    "H": 1,
    "C": 6,
    "N": 7,
    "O": 8,
}


@dataclass
class GeometryRecord:
    sample_id: str
    symbols: list[str]
    coordinates: np.ndarray
    charge: int = 0
    multiplicity: int = 1
    source: str = ""
    source_kind: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def atomic_numbers(self) -> np.ndarray:
        return np.asarray([SYMBOL_TO_ATOMIC_NUMBER[symbol] for symbol in self.symbols], dtype=int)

    def to_manifest_entry(self, geometry_path: Path, project_root: Path) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "geometry_file": str(geometry_path.resolve().relative_to(project_root.resolve())),
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "num_atoms": len(self.symbols),
            "source": self.source,
            "source_kind": self.source_kind,
            "metadata": self.metadata,
        }


def _load_xyz(path: Path) -> GeometryRecord:
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError(f"XYZ file is too short: {path}")

    num_atoms = int(lines[0])
    comment = lines[1]
    body = lines[2 : 2 + num_atoms]

    symbols: list[str] = []
    coords: list[list[float]] = []
    for line in body:
        fields = line.split()
        if len(fields) < 4:
            raise ValueError(f"Invalid XYZ row: {line}")
        symbols.append(fields[0])
        coords.append([float(fields[1]), float(fields[2]), float(fields[3])])

    return GeometryRecord(
        sample_id=path.stem,
        symbols=symbols,
        coordinates=np.asarray(coords, dtype=float),
        source=comment,
        source_kind="xyz_geometry",
    )


def _load_json(path: Path) -> GeometryRecord:
    payload = read_json(path)
    if "atoms" not in payload:
        raise ValueError(f"Geometry JSON is missing `atoms`: {path}")

    symbols = [atom["element_symbol"] for atom in payload["atoms"]]
    coords = [atom["xyz_coordinates"] for atom in payload["atoms"]]

    return GeometryRecord(
        sample_id=payload.get("id", path.stem),
        symbols=symbols,
        coordinates=np.asarray(coords, dtype=float),
        charge=int(payload.get("charge", 0)),
        multiplicity=int(payload.get("multiplicity", 1)),
        source=payload.get("source_log", path.name),
        source_kind=payload.get("source_kind", "mlatom_json"),
        metadata={
            "source_format": "mlatom_json",
            **({"frequencies": payload.get("frequencies")} if payload.get("frequencies") is not None else {}),
        },
    )


def load_geometry(path: str | Path) -> GeometryRecord:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".xyz":
        return _load_xyz(path)
    if suffix == ".json":
        return _load_json(path)
    raise ValueError(f"Unsupported geometry format: {path}")


def save_xyz(record: GeometryRecord, path: str | Path, comment: str | None = None) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    lines = [str(len(record.symbols)), comment or record.source or record.sample_id]
    for symbol, coord in zip(record.symbols, record.coordinates, strict=True):
        lines.append(f"{symbol} {coord[0]: .10f} {coord[1]: .10f} {coord[2]: .10f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(entries: list[dict[str, Any]], path: str | Path) -> None:
    write_json(path, {"samples": entries})


def load_manifest(path: str | Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    return payload.get("samples", [])
