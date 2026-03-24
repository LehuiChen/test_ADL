from __future__ import annotations

from pathlib import Path

from .io_utils import write_json
from .mlatom_bridge import build_molecular_database_from_geometry_manifest
from .training import create_delta_model_bundle, load_training_state


def evaluate_uncertainty_for_manifest(
    *,
    config: dict,
    manifest_path: str | Path,
    output_path: str | Path,
) -> dict:
    """对一个几何池做不确定性评估。"""

    state = load_training_state(config)
    model = create_delta_model_bundle(config, config["paths"]["models_dir"])
    model.load_trained_models(config["paths"]["models_dir"], load_main=True, load_aux=True)
    model.uq_threshold = state.get("uq_threshold")

    molecular_database = build_molecular_database_from_geometry_manifest(manifest_path)
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
    }
    write_json(output_path, payload)
    return payload


def select_next_round_samples(
    *,
    uncertainty_payload: dict,
    max_new_points: int,
    convergence_ratio: float,
) -> dict:
    """根据不确定性结果选择下一轮需要标注的样本。"""

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
