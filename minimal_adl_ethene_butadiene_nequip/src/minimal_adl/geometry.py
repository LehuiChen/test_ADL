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
    """描述一个几何结构样本。"""

    sample_id: str
    symbols: list[str]
    coordinates: np.ndarray
    charge: int = 0
    multiplicity: int = 1
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def atomic_numbers(self) -> np.ndarray:
        return np.asarray([SYMBOL_TO_ATOMIC_NUMBER[symbol] for symbol in self.symbols], dtype=int)

    def to_manifest_entry(self, geometry_path: Path, project_root: Path) -> dict[str, Any]:
        """把样本转成 manifest 条目。"""

        return {
            "sample_id": self.sample_id,
            "geometry_file": str(geometry_path.resolve().relative_to(project_root.resolve())),
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "num_atoms": len(self.symbols),
            "source": self.source,
            "metadata": self.metadata,
        }


def _load_xyz(path: Path) -> GeometryRecord:
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 3:
        raise ValueError(f"XYZ 文件内容过短：{path}")

    num_atoms = int(lines[0])
    comment = lines[1]
    body = lines[2 : 2 + num_atoms]

    symbols: list[str] = []
    coords: list[list[float]] = []
    for line in body:
        fields = line.split()
        if len(fields) < 4:
            raise ValueError(f"XYZ 行格式不正确：{line}")
        symbols.append(fields[0])
        coords.append([float(fields[1]), float(fields[2]), float(fields[3])])

    return GeometryRecord(
        sample_id=path.stem,
        symbols=symbols,
        coordinates=np.asarray(coords, dtype=float),
        source=comment,
    )


def _load_json(path: Path) -> GeometryRecord:
    payload = read_json(path)
    if "atoms" not in payload:
        raise ValueError(f"JSON 几何文件不包含 atoms 字段：{path}")

    symbols = [atom["element_symbol"] for atom in payload["atoms"]]
    coords = [atom["xyz_coordinates"] for atom in payload["atoms"]]

    return GeometryRecord(
        sample_id=payload.get("id", path.stem),
        symbols=symbols,
        coordinates=np.asarray(coords, dtype=float),
        charge=int(payload.get("charge", 0)),
        multiplicity=int(payload.get("multiplicity", 1)),
        source=path.name,
        metadata={"source_format": "mlatom_json"},
    )


def load_geometry(path: str | Path) -> GeometryRecord:
    """读取单个几何文件，支持 xyz 和原仓库中的单分子 json。"""

    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".xyz":
        return _load_xyz(path)
    if suffix == ".json":
        return _load_json(path)
    raise ValueError(f"暂不支持的几何格式：{path}")


def save_xyz(record: GeometryRecord, path: str | Path, comment: str | None = None) -> None:
    """保存为标准 xyz 文件。"""

    path = Path(path)
    ensure_dir(path.parent)
    lines = [str(len(record.symbols)), comment or record.source or record.sample_id]
    for symbol, coord in zip(record.symbols, record.coordinates):
        lines.append(f"{symbol} {coord[0]: .10f} {coord[1]: .10f} {coord[2]: .10f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_perturbed_geometries(
    seed: GeometryRecord,
    num_samples: int,
    displacement_std: float,
    max_abs_displacement: float,
    rng_seed: int,
    prefix: str = "geom",
) -> list[GeometryRecord]:
    """围绕种子结构生成一批随机微扰几何。

    这是为了教学和最小跑通而使用的工程简化版采样。
    """

    rng = np.random.default_rng(rng_seed)
    samples: list[GeometryRecord] = []
    for index in range(num_samples):
        displacement = rng.normal(loc=0.0, scale=displacement_std, size=seed.coordinates.shape)
        displacement = np.clip(displacement, -max_abs_displacement, max_abs_displacement)
        samples.append(
            GeometryRecord(
                sample_id=f"{prefix}_{index:04d}",
                symbols=list(seed.symbols),
                coordinates=seed.coordinates + displacement,
                charge=seed.charge,
                multiplicity=seed.multiplicity,
                source="random_displacement_from_seed",
                metadata={
                    "seed_sample_id": seed.sample_id,
                    "displacement_std_angstrom": displacement_std,
                    "max_abs_displacement_angstrom": max_abs_displacement,
                },
            )
        )
    return samples


def write_manifest(entries: list[dict[str, Any]], path: str | Path) -> None:
    """把几何列表写入 manifest。"""

    write_json(path, {"samples": entries})


def load_manifest(path: str | Path) -> list[dict[str, Any]]:
    """读取 manifest 中的样本列表。"""

    payload = read_json(path)
    return payload.get("samples", [])

