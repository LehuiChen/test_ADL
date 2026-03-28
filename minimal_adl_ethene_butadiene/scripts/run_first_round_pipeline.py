from __future__ import annotations

import argparse
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.geometry import load_manifest, write_manifest
from minimal_adl.io_utils import read_json, timestamp_string, write_json


StageCheck = Callable[[], bool]
StageRun = Callable[[], dict[str, Any]]


def safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def label_success(label_file: Path) -> bool:
    payload = safe_read_json(label_file)
    return bool(payload.get("success", False))


def manifest_sample_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [str(item["sample_id"]) for item in load_manifest(path)]


def count_successful_labels(labels_root: Path, sample_ids: list[str]) -> int:
    return sum(1 for sample_id in sample_ids if label_success(labels_root / sample_id / "label.json"))


def run_python_script(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    base_stage_names = [
        "check_environment",
        "sample_initial_geometries",
        "initial_selection",
        "run_xtb_labels",
        "run_target_labels",
        "build_delta_dataset",
        "train_main_model",
        "train_aux_model",
        "export_training_diagnostics",
        "evaluate_uncertainty",
        "select_round_001",
    ]
    parser = argparse.ArgumentParser(description="一键编排最小版 ADL 第一轮主线，并支持恢复执行。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    parser.add_argument("--from-stage", choices=base_stage_names + ["smoke_test_labels"], default=None)
    parser.add_argument("--to-stage", choices=base_stage_names + ["smoke_test_labels"], default=None)
    parser.add_argument("--resume", dest="resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--force", action="store_true", help="忽略已完成状态并强制重跑选定阶段。")
    parser.add_argument("--submit-mode-labels", choices=["local", "pbs"], default="pbs")
    parser.add_argument("--submit-mode-train", choices=["local", "pbs"], default="pbs")
    parser.add_argument("--submit-mode-uq", choices=["local", "pbs"], default="pbs")
    parser.add_argument("--with-smoke-tests", action="store_true", help="在完整标注前先对少量样本做联通测试。")
    args = parser.parse_args()

    config = load_config(args.config)
    project_root = Path(config["project_root"]).resolve()
    config_path = Path(config["config_path"]).resolve()
    paths_cfg = config["paths"]
    results_dir = Path(paths_cfg["results_dir"]).resolve()
    models_dir = Path(paths_cfg["models_dir"]).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    geometry_manifest_path = Path(paths_cfg["geometry_pool_manifest"]).resolve()
    initial_manifest_path = Path(paths_cfg["initial_selection_manifest"]).resolve()
    delta_npz_path = Path(paths_cfg["delta_dataset_npz"]).resolve()
    delta_metadata_path = Path(paths_cfg["delta_dataset_metadata"]).resolve()
    train_main_status_path = models_dir / "train_main_status.json"
    train_aux_status_path = models_dir / "train_aux_status.json"
    training_diagnostics_path = Path(paths_cfg.get("training_diagnostics_file", models_dir / "training_diagnostics.json")).resolve()
    uncertainty_status_path = results_dir / "uncertainty_status.json"
    uncertainty_latest_path = Path(results_dir / "uncertainty_latest.json").resolve()
    round_selection_summary_path = results_dir / "round_001_selection_summary.json"
    round_selected_manifest_path = results_dir / "round_001_selected_manifest.json"
    check_environment_report_path = Path(paths_cfg.get("check_environment_report", results_dir / "check_environment_latest.json")).resolve()
    pipeline_run_summary_path = Path(paths_cfg.get("pipeline_run_summary", results_dir / "pipeline_run_summary.json")).resolve()
    smoke_manifest_path = results_dir / "smoke_test_manifest.json"

    stage_names = base_stage_names.copy()
    if args.with_smoke_tests:
        stage_names.insert(stage_names.index("run_xtb_labels"), "smoke_test_labels")

    if args.from_stage and args.from_stage not in stage_names:
        raise ValueError(f"当前阶段列表中不存在 from-stage={args.from_stage}")
    if args.to_stage and args.to_stage not in stage_names:
        raise ValueError(f"当前阶段列表中不存在 to-stage={args.to_stage}")

    start_index = 0 if args.from_stage is None else stage_names.index(args.from_stage)
    end_index = len(stage_names) - 1 if args.to_stage is None else stage_names.index(args.to_stage)
    if start_index > end_index:
        raise ValueError("from-stage 不能排在 to-stage 后面。")
    selected_stages = stage_names[start_index : end_index + 1]

    pipeline_summary: dict[str, Any] = {
        "generated_at": timestamp_string(),
        "config_file": str(config_path),
        "selected_stages": selected_stages,
        "resume": args.resume,
        "force": args.force,
        "submit_mode_labels": args.submit_mode_labels,
        "submit_mode_train": args.submit_mode_train,
        "submit_mode_uq": args.submit_mode_uq,
        "with_smoke_tests": args.with_smoke_tests,
        "stages": [],
        "success": False,
    }

    def persist_summary() -> None:
        write_json(pipeline_run_summary_path, pipeline_summary)

    def build_smoke_manifest() -> dict[str, Any]:
        initial_entries = load_manifest(initial_manifest_path)
        smoke_entries = initial_entries[: min(3, len(initial_entries))]
        write_manifest(smoke_entries, smoke_manifest_path)
        return {
            "smoke_manifest": str(smoke_manifest_path),
            "num_samples": len(smoke_entries),
            "sample_ids": [entry["sample_id"] for entry in smoke_entries],
        }

    def check_environment_complete() -> bool:
        return bool(safe_read_json(check_environment_report_path).get("checks"))

    def sample_geometries_complete() -> bool:
        return bool(manifest_sample_ids(geometry_manifest_path))

    def initial_selection_complete() -> bool:
        return bool(manifest_sample_ids(initial_manifest_path))

    def smoke_test_complete() -> bool:
        sample_ids = manifest_sample_ids(smoke_manifest_path)
        if not sample_ids:
            return False
        xtb_root = Path(paths_cfg["xtb_labels_dir"]).resolve()
        gaussian_root = Path(paths_cfg["gaussian_labels_dir"]).resolve()
        return count_successful_labels(xtb_root, sample_ids) == len(sample_ids) and count_successful_labels(gaussian_root, sample_ids) == len(sample_ids)

    def xtb_labels_complete() -> bool:
        sample_ids = manifest_sample_ids(initial_manifest_path)
        return bool(sample_ids) and count_successful_labels(Path(paths_cfg["xtb_labels_dir"]).resolve(), sample_ids) == len(sample_ids)

    def target_labels_complete() -> bool:
        sample_ids = manifest_sample_ids(initial_manifest_path)
        return bool(sample_ids) and count_successful_labels(Path(paths_cfg["gaussian_labels_dir"]).resolve(), sample_ids) == len(sample_ids)

    def delta_dataset_complete() -> bool:
        metadata = safe_read_json(delta_metadata_path)
        return delta_npz_path.exists() and metadata.get("num_samples", 0) > 0

    def train_main_complete() -> bool:
        return bool(safe_read_json(train_main_status_path).get("success", False))

    def train_aux_complete() -> bool:
        return bool(safe_read_json(train_aux_status_path).get("success", False))

    def diagnostics_complete() -> bool:
        diagnostics = safe_read_json(training_diagnostics_path)
        return bool(diagnostics.get("artifacts"))

    def uncertainty_complete() -> bool:
        return bool(safe_read_json(uncertainty_status_path).get("success", False)) and uncertainty_latest_path.exists()

    def selection_complete() -> bool:
        return round_selection_summary_path.exists() and round_selected_manifest_path.exists()

    stages: dict[str, dict[str, Any]] = {
        "check_environment": {
            "is_complete": check_environment_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "check_environment.py").resolve()),
                        "--config",
                        str(config_path),
                        "--json-output",
                        str(check_environment_report_path),
                        "--strict",
                    ],
                    cwd=project_root,
                ),
                {"report_file": str(check_environment_report_path)},
            )[1],
        },
        "sample_initial_geometries": {
            "is_complete": sample_geometries_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "sample_initial_geometries.py").resolve()),
                        "--config",
                        str(config_path),
                    ],
                    cwd=project_root,
                ),
                {"geometry_pool_manifest": str(geometry_manifest_path)},
            )[1],
        },
        "initial_selection": {
            "is_complete": initial_selection_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "active_learning_loop.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(geometry_manifest_path),
                        "--mode",
                        "initial-selection",
                        "--round-index",
                        "0",
                    ],
                    cwd=project_root,
                ),
                {"initial_selection_manifest": str(initial_manifest_path)},
            )[1],
        },
        "smoke_test_labels": {
            "is_complete": smoke_test_complete,
            "run": lambda: (
                build_smoke_manifest(),
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "run_xtb_labels.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(smoke_manifest_path),
                        "--submit-mode",
                        args.submit_mode_labels,
                        *([] if not args.force else ["--force"]),
                    ],
                    cwd=project_root,
                ),
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "run_target_labels.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(smoke_manifest_path),
                        "--submit-mode",
                        args.submit_mode_labels,
                        *([] if not args.force else ["--force"]),
                    ],
                    cwd=project_root,
                ),
                {"smoke_manifest": str(smoke_manifest_path)},
            )[-1],
        },
        "run_xtb_labels": {
            "is_complete": xtb_labels_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "run_xtb_labels.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(initial_manifest_path),
                        "--submit-mode",
                        args.submit_mode_labels,
                        *([] if not args.force else ["--force"]),
                    ],
                    cwd=project_root,
                ),
                {"labels_root": str(Path(paths_cfg["xtb_labels_dir"]).resolve())},
            )[1],
        },
        "run_target_labels": {
            "is_complete": target_labels_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "run_target_labels.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(initial_manifest_path),
                        "--submit-mode",
                        args.submit_mode_labels,
                        *([] if not args.force else ["--force"]),
                    ],
                    cwd=project_root,
                ),
                {"labels_root": str(Path(paths_cfg["gaussian_labels_dir"]).resolve())},
            )[1],
        },
        "build_delta_dataset": {
            "is_complete": delta_dataset_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "build_delta_dataset.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(initial_manifest_path),
                    ],
                    cwd=project_root,
                ),
                {
                    "delta_dataset_npz": str(delta_npz_path),
                    "delta_dataset_metadata": str(delta_metadata_path),
                },
            )[1],
        },
        "train_main_model": {
            "is_complete": train_main_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "train_main_model.py").resolve()),
                        "--config",
                        str(config_path),
                        "--submit-mode",
                        args.submit_mode_train,
                    ],
                    cwd=project_root,
                ),
                {"status_file": str(train_main_status_path)},
            )[1],
        },
        "train_aux_model": {
            "is_complete": train_aux_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "train_aux_model.py").resolve()),
                        "--config",
                        str(config_path),
                        "--submit-mode",
                        args.submit_mode_train,
                    ],
                    cwd=project_root,
                ),
                {"status_file": str(train_aux_status_path)},
            )[1],
        },
        "export_training_diagnostics": {
            "is_complete": diagnostics_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "export_training_diagnostics.py").resolve()),
                        "--config",
                        str(config_path),
                    ],
                    cwd=project_root,
                ),
                {"training_diagnostics_file": str(training_diagnostics_path)},
            )[1],
        },
        "evaluate_uncertainty": {
            "is_complete": uncertainty_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "evaluate_uncertainty.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(geometry_manifest_path),
                        "--submit-mode",
                        args.submit_mode_uq,
                    ],
                    cwd=project_root,
                ),
                {"uncertainty_file": str(uncertainty_latest_path)},
            )[1],
        },
        "select_round_001": {
            "is_complete": selection_complete,
            "run": lambda: (
                run_python_script(
                    [
                        sys.executable,
                        str((project_root / "scripts" / "active_learning_loop.py").resolve()),
                        "--config",
                        str(config_path),
                        "--manifest",
                        str(geometry_manifest_path),
                        "--mode",
                        "next-round",
                        "--uncertainty",
                        str(uncertainty_latest_path),
                        "--round-index",
                        "1",
                    ],
                    cwd=project_root,
                ),
                {
                    "selection_summary_file": str(round_selection_summary_path),
                    "selection_manifest_file": str(round_selected_manifest_path),
                },
            )[1],
        },
    }

    persist_summary()

    must_rerun_remaining = False
    for stage_name in selected_stages:
        stage_def = stages[stage_name]
        stage_record: dict[str, Any] = {
            "stage": stage_name,
            "started_at": timestamp_string(),
        }
        try:
            if args.resume and not args.force and not must_rerun_remaining and stage_def["is_complete"]():
                stage_record["status"] = "skipped"
                stage_record["reason"] = "检测到标准产物已存在，且当前启用了 resume。"
            else:
                outputs = stage_def["run"]()
                stage_record["status"] = "completed"
                stage_record["outputs"] = outputs
                must_rerun_remaining = True
            stage_record["finished_at"] = timestamp_string()
            pipeline_summary["stages"].append(stage_record)
            persist_summary()
        except Exception as exc:  # noqa: BLE001
            stage_record["status"] = "failed"
            stage_record["finished_at"] = timestamp_string()
            stage_record["error_type"] = type(exc).__name__
            stage_record["error_message"] = str(exc)
            stage_record["traceback"] = traceback.format_exc()
            pipeline_summary["stages"].append(stage_record)
            pipeline_summary["success"] = False
            persist_summary()
            raise

    pipeline_summary["success"] = True
    pipeline_summary["finished_at"] = timestamp_string()
    persist_summary()
    print(f"第一轮主线流程完成：{pipeline_run_summary_path}")


if __name__ == "__main__":
    main()
