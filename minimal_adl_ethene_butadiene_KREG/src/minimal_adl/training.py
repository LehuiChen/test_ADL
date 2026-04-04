from __future__ import annotations

from pathlib import Path

from .config import get_method_config
from .delta_model import DeltaMLModel
from .io_utils import read_json
from .mlatom_bridge import build_molecular_database_from_dataset, create_mlatom_method


def create_delta_model_bundle(config: dict, workdir: str | Path) -> DeltaMLModel:
    training_cfg = config.get("training", {})
    baseline_method = create_mlatom_method(get_method_config(config, "baseline"))
    model = DeltaMLModel(
        model_file=training_cfg.get("model_name", "delta_bundle"),
        ml_model_type=training_cfg.get("ml_model_type", "KREG"),
        baseline=baseline_method,
        validation_set_fraction=float(training_cfg.get("validation_set_fraction", 0.1)),
        device=training_cfg.get("device"),
        verbose=True,
        main_model_stem=training_cfg.get("main_model_stem", "delta_main_model"),
        aux_model_stem=training_cfg.get("aux_model_stem", "delta_aux_model"),
    )
    model.prepare_model_paths(workdir)
    return model


def train_delta_bundle(
    *,
    config: dict,
    train_main: bool,
    train_aux: bool,
) -> dict:
    paths_cfg = config["paths"]
    workdir = Path(paths_cfg["models_dir"])
    workdir.mkdir(parents=True, exist_ok=True)

    molecular_database = build_molecular_database_from_dataset(
        npz_path=paths_cfg["delta_dataset_npz"],
        metadata_path=paths_cfg["delta_dataset_metadata"],
    )

    model = create_delta_model_bundle(config, workdir)
    return model.train(
        molecular_database=molecular_database,
        al_info={
            "working_directory": str(workdir),
            "threshold_metric": config.get("active_learning", {}).get("threshold_metric", "m+3mad"),
            **(
                {"uq_threshold": config["active_learning"]["uncertainty_threshold"]}
                if config.get("active_learning", {}).get("uncertainty_threshold") is not None
                else {}
            ),
        },
        train_main=train_main,
        train_aux=train_aux,
        summary_filename=config["training"].get("summary_filename", "training_summary.json"),
        state_filename=config["training"].get("state_filename", "training_state.json"),
    )


def load_training_state(config: dict) -> dict:
    state_path = Path(config["paths"]["models_dir"]) / config["training"].get("state_filename", "training_state.json")
    return read_json(state_path)