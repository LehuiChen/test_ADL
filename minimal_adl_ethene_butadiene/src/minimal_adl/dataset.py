from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .geometry import load_geometry, load_manifest
from .io_utils import read_json, write_json


def load_label_result(label_json_path: str | Path) -> dict[str, Any]:
    """读取单个标注结果文件。"""

    payload = read_json(label_json_path)
    if not payload.get("success", False):
        raise RuntimeError(f"标注任务失败：{label_json_path}")
    return payload


def build_delta_dataset(
    *,
    manifest_path: str | Path,
    xtb_labels_dir: str | Path,
    gaussian_labels_dir: str | Path,
    npz_output_path: str | Path,
    metadata_output_path: str | Path,
) -> dict[str, Any]:
    """读取几何与标注结果，构建统一的 delta 数据集。"""

    manifest_entries = load_manifest(manifest_path)
    xtb_labels_dir = Path(xtb_labels_dir)
    gaussian_labels_dir = Path(gaussian_labels_dir)

    sample_ids: list[str] = []
    atomic_numbers: list[np.ndarray] = []
    coordinates: list[np.ndarray] = []
    baseline_energies: list[float] = []
    target_energies: list[float] = []
    delta_energies: list[float] = []
    baseline_forces: list[np.ndarray] = []
    target_forces: list[np.ndarray] = []
    delta_forces: list[np.ndarray] = []
    per_sample_metadata: list[dict[str, Any]] = []

    manifest_root = Path(manifest_path).resolve().parent.parent.parent

    for entry in manifest_entries:
        sample_id = entry["sample_id"]
        geometry_file = Path(entry["geometry_file"])
        if not geometry_file.is_absolute():
            geometry_file = manifest_root / geometry_file

        xtb_result = load_label_result(xtb_labels_dir / sample_id / "label.json")
        target_result = load_label_result(gaussian_labels_dir / sample_id / "label.json")
        geometry = load_geometry(geometry_file)

        baseline_force = np.asarray(xtb_result["forces"], dtype=float)
        target_force = np.asarray(target_result["forces"], dtype=float)
        delta_force = target_force - baseline_force

        baseline_energy = float(xtb_result["energy"])
        target_energy = float(target_result["energy"])
        delta_energy = target_energy - baseline_energy

        sample_ids.append(sample_id)
        atomic_numbers.append(geometry.atomic_numbers)
        coordinates.append(np.asarray(geometry.coordinates, dtype=float))
        baseline_energies.append(baseline_energy)
        target_energies.append(target_energy)
        delta_energies.append(delta_energy)
        baseline_forces.append(baseline_force)
        target_forces.append(target_force)
        delta_forces.append(delta_force)
        per_sample_metadata.append(
            {
                "sample_id": sample_id,
                "geometry_file": str(geometry_file.resolve()),
                "charge": geometry.charge,
                "multiplicity": geometry.multiplicity,
                "source": entry.get("source", ""),
                "source_kind": entry.get("source_kind", ""),
                "manifest_metadata": entry.get("metadata", {}),
                "round_index": entry.get("metadata", {}).get("round_index"),
                "parent_trajectory_id": entry.get("metadata", {}).get("parent_trajectory_id"),
                "frame_index": entry.get("metadata", {}).get("frame_index"),
                "time_fs": entry.get("metadata", {}).get("time_fs"),
                "initcond_id": entry.get("metadata", {}).get("initcond_id"),
                "uq_at_selection": entry.get("metadata", {}).get("uq_at_selection"),
                "baseline_label_file": str((xtb_labels_dir / sample_id / "label.json").resolve()),
                "target_label_file": str((gaussian_labels_dir / sample_id / "label.json").resolve()),
            }
        )

    np.savez_compressed(
        npz_output_path,
        sample_ids=np.asarray(sample_ids),
        atomic_numbers=np.asarray(atomic_numbers, dtype=int),
        coordinates=np.asarray(coordinates, dtype=float),
        E_baseline=np.asarray(baseline_energies, dtype=float),
        E_target=np.asarray(target_energies, dtype=float),
        delta_E=np.asarray(delta_energies, dtype=float),
        F_baseline=np.asarray(baseline_forces, dtype=float),
        F_target=np.asarray(target_forces, dtype=float),
        delta_F=np.asarray(delta_forces, dtype=float),
    )

    metadata = {
        "num_samples": len(sample_ids),
        "samples": per_sample_metadata,
        "notes": {
            "delta_E_definition": "E_target - E_baseline",
            "delta_F_definition": "F_target - F_baseline",
        },
    }
    write_json(metadata_output_path, metadata)
    return metadata


def load_delta_dataset(npz_path: str | Path, metadata_path: str | Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """读取之前保存的 delta 数据集。"""

    dataset = np.load(npz_path, allow_pickle=True)
    metadata = read_json(metadata_path)
    return {key: dataset[key] for key in dataset.files}, metadata
