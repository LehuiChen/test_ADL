from __future__ import annotations

from pathlib import Path
from typing import Any

from .io_utils import read_json, write_json


def _payload_from_md_frame_manifest(manifest_payload: dict[str, Any]) -> dict[str, Any]:
    frames = manifest_payload.get("frames", manifest_payload.get("samples", []))
    samples = []
    for frame in frames:
        uq_value = frame.get("uncertainty")
        samples.append(
            {
                "sample_id": frame.get("sample_id"),
                "predicted_delta_E_main": frame.get("predicted_delta_E_main"),
                "predicted_delta_E_aux": frame.get("predicted_delta_E_aux"),
                "predicted_total_energy": frame.get("predicted_total_energy"),
                "uncertainty": uq_value,
                "exceeds_threshold": frame.get("exceeds_threshold"),
                "round_index": frame.get("round_index"),
                "trajectory_id": frame.get("trajectory_id"),
                "frame_index": frame.get("frame_index"),
                "time_fs": frame.get("time_fs"),
                "source_kind": frame.get("source_kind", "md_frame"),
            }
        )
    return {
        "uq_threshold": manifest_payload.get("uq_threshold"),
        "num_samples": len(samples),
        "samples": samples,
        "source_manifest_type": "md_frame_manifest",
    }


def evaluate_uncertainty_for_manifest(
    *,
    config: dict,
    manifest_path: str | Path,
    output_path: str | Path,
) -> dict:
    manifest_path = Path(manifest_path).resolve()
    manifest_payload = read_json(manifest_path)

    if isinstance(manifest_payload, dict) and ("frames" in manifest_payload or "samples" in manifest_payload and manifest_payload.get("source_manifest_type") == "md_frame_manifest"):
        payload = _payload_from_md_frame_manifest(manifest_payload)
        write_json(output_path, payload)
        return payload

    from .mlatom_bridge import build_molecular_database_from_geometry_manifest
    from .training import create_delta_model_bundle, load_training_state

    state = load_training_state(config)
    model = create_delta_model_bundle(config, config["paths"]["models_dir"])
    model.load_trained_models(config["paths"]["models_dir"], load_main=True, load_aux=True)
    model.uq_threshold = state.get("uq_threshold")

    molecular_database = build_molecular_database_from_geometry_manifest(manifest_path, project_root=config["project_root"])
    model.predict(molecular_database=molecular_database)

    samples = []
    for molecule in molecular_database:
        uq_value = float(molecule.uq)
        samples.append(
            {
                "sample_id": molecule.id,
                "predicted_delta_E_main": float(molecule.delta_energy),
                "predicted_delta_E_aux": float(molecule.aux_delta_energy),
                "predicted_total_energy": float(molecule.energy),
                "uncertainty": uq_value,
                "exceeds_threshold": model.uq_threshold is not None and uq_value > model.uq_threshold,
            }
        )

    payload = {
        "uq_threshold": model.uq_threshold,
        "num_samples": len(samples),
        "samples": samples,
        "source_manifest_type": "geometry_manifest",
    }
    write_json(output_path, payload)
    return payload


def select_next_round_samples(
    *,
    uncertainty_payload: dict,
    max_new_points: int,
    convergence_ratio: float,
) -> dict:
    threshold = uncertainty_payload.get("uq_threshold")
    sorted_samples = sorted(
        uncertainty_payload.get("samples", []),
        key=lambda item: item["uncertainty"],
        reverse=True,
    )

    if threshold is None:
        uncertain_samples = sorted_samples[:max_new_points]
    else:
        uncertain_samples = [item for item in sorted_samples if item["uncertainty"] > threshold]

    selected = uncertain_samples[:max_new_points]
    total = max(len(sorted_samples), 1)
    ratio = len(uncertain_samples) / total

    return {
        "uq_threshold": threshold,
        "num_pool_samples": len(sorted_samples),
        "num_uncertain_samples": len(uncertain_samples),
        "selected_samples": selected,
        "selected_sample_ids": [item["sample_id"] for item in selected],
        "uncertain_ratio": ratio,
        "converged": ratio < convergence_ratio,
    }

