from __future__ import annotations

import argparse
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.geometry import load_manifest
from minimal_adl.io_utils import read_json, timestamp_string, write_json


def run_python_script(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = read_json(path)
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def latest_selection_summary(results_dir: Path) -> tuple[int | None, dict[str, Any]]:
    latest_round_index: int | None = None
    latest_payload: dict[str, Any] = {}
    for summary_path in sorted(results_dir.glob("round_*_selection_summary.json")):
        payload = safe_read_json(summary_path)
        round_index = payload.get("round_index")
        if round_index is None:
            continue
        round_index = int(round_index)
        if latest_round_index is None or round_index > latest_round_index:
            latest_round_index = round_index
            latest_payload = payload
    return latest_round_index, latest_payload


def manifest_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(load_manifest(path))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full TS-seeded active-learning experiment across multiple rounds."
    )
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    parser.add_argument("--resume", dest="resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--force", action="store_true", help="Force reruns even if outputs already exist.")
    parser.add_argument("--max-rounds", type=int, default=None, help="Override the maximum number of active-learning rounds.")
    parser.add_argument("--submit-mode-labels", choices=["local", "pbs"], default="pbs")
    parser.add_argument("--submit-mode-train", choices=["local", "pbs"], default="pbs")
    parser.add_argument("--submit-mode-md", choices=["local", "pbs"], default="pbs")
    parser.add_argument("--md-num-initial-conditions", type=int, default=None)
    parser.add_argument("--md-maximum-propagation-time", type=float, default=None)
    parser.add_argument("--md-time-step", type=float, default=None)
    parser.add_argument("--md-save-interval-steps", type=int, default=None)
    parser.add_argument(
        "--max-new-points",
        type=int,
        default=None,
        help="Optional explicit cap for new points per round. Omit to keep all uncertain points.",
    )
    parser.add_argument("--device", default=None, help="Optional training / MD device override, such as cpu or cuda.")
    args = parser.parse_args()

    config = load_config(args.config)
    project_root = Path(config["project_root"]).resolve()
    config_path = Path(config["config_path"]).resolve()
    results_dir = Path(config["paths"]["results_dir"]).resolve()
    experiment_summary_path = results_dir / "active_learning_experiment_summary.json"
    max_rounds = int(args.max_rounds or config.get("active_learning", {}).get("max_rounds", 10))

    summary: dict[str, Any] = {
        "generated_at": timestamp_string(),
        "config_file": str(config_path),
        "max_rounds": max_rounds,
        "resume": args.resume,
        "force": args.force,
        "submit_mode_labels": args.submit_mode_labels,
        "submit_mode_train": args.submit_mode_train,
        "submit_mode_md": args.submit_mode_md,
        "device_override": args.device,
        "selection_cap_override": args.max_new_points,
        "rounds": [],
        "success": False,
    }

    def persist_summary() -> None:
        write_json(experiment_summary_path, summary)

    persist_summary()

    try:
        run_python_script(
            [
                sys.executable,
                str((project_root / "scripts" / "run_first_round_pipeline.py").resolve()),
                "--config",
                str(config_path),
                "--submit-mode-labels",
                args.submit_mode_labels,
                "--submit-mode-train",
                args.submit_mode_train,
                "--submit-mode-md",
                args.submit_mode_md,
                "--resume" if args.resume else "--no-resume",
                *([] if not args.force else ["--force"]),
                *([] if args.md_num_initial_conditions is None else ["--md-num-initial-conditions", str(args.md_num_initial_conditions)]),
                *([] if args.md_maximum_propagation_time is None else ["--md-maximum-propagation-time", str(args.md_maximum_propagation_time)]),
                *([] if args.md_time_step is None else ["--md-time-step", str(args.md_time_step)]),
                *([] if args.md_save_interval_steps is None else ["--md-save-interval-steps", str(args.md_save_interval_steps)]),
                *([] if args.device is None else ["--device", args.device]),
            ],
            cwd=project_root,
        )

        while True:
            latest_round_index, latest_payload = latest_selection_summary(results_dir)
            if latest_round_index is None:
                raise RuntimeError("No round selection summary was found after running the first-round pipeline.")

            round_record: dict[str, Any] = {
                "round_index": latest_round_index,
                "selection_summary_file": str((results_dir / f"round_{latest_round_index:03d}_selection_summary.json").resolve()),
                "selected_manifest_file": str((results_dir / f"round_{latest_round_index:03d}_selected_manifest.json").resolve()),
                "selected_count": latest_payload.get("selected_count"),
                "converged": latest_payload.get("converged"),
                "started_at": timestamp_string(),
            }

            if bool(latest_payload.get("converged", False)):
                round_record["status"] = "stopped"
                round_record["reason"] = "converged"
                round_record["finished_at"] = timestamp_string()
                summary["rounds"].append(round_record)
                break

            if latest_round_index >= max_rounds:
                round_record["status"] = "stopped"
                round_record["reason"] = "max_rounds_reached"
                round_record["finished_at"] = timestamp_string()
                summary["rounds"].append(round_record)
                break

            selected_manifest_path = results_dir / f"round_{latest_round_index:03d}_selected_manifest.json"
            selected_count = manifest_count(selected_manifest_path)
            round_record["selected_manifest_count"] = selected_count
            if selected_count == 0:
                round_record["status"] = "stopped"
                round_record["reason"] = "no_selected_points"
                round_record["finished_at"] = timestamp_string()
                summary["rounds"].append(round_record)
                break

            next_round_index = latest_round_index + 1

            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "run_xtb_labels.py").resolve()),
                    "--config",
                    str(config_path),
                    "--manifest",
                    str(selected_manifest_path.resolve()),
                    "--submit-mode",
                    args.submit_mode_labels,
                    *([] if not args.force else ["--force"]),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "run_target_labels.py").resolve()),
                    "--config",
                    str(config_path),
                    "--manifest",
                    str(selected_manifest_path.resolve()),
                    "--submit-mode",
                    args.submit_mode_labels,
                    *([] if not args.force else ["--force"]),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "update_cumulative_manifest.py").resolve()),
                    "--config",
                    str(config_path),
                    "--manifest",
                    str(selected_manifest_path.resolve()),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "build_delta_dataset.py").resolve()),
                    "--config",
                    str(config_path),
                    "--manifest",
                    str(Path(config["paths"]["cumulative_labeled_manifest"]).resolve()),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "train_main_model.py").resolve()),
                    "--config",
                    str(config_path),
                    "--submit-mode",
                    args.submit_mode_train,
                    *([] if args.device is None else ["--device", args.device]),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "train_aux_model.py").resolve()),
                    "--config",
                    str(config_path),
                    "--submit-mode",
                    args.submit_mode_train,
                    *([] if args.device is None else ["--device", args.device]),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "export_training_diagnostics.py").resolve()),
                    "--config",
                    str(config_path),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "run_md_sampling.py").resolve()),
                    "--config",
                    str(config_path),
                    "--round-index",
                    str(next_round_index),
                    "--submit-mode",
                    args.submit_mode_md,
                    *([] if args.md_num_initial_conditions is None else ["--num-initial-conditions", str(args.md_num_initial_conditions)]),
                    *([] if args.md_maximum_propagation_time is None else ["--maximum-propagation-time", str(args.md_maximum_propagation_time)]),
                    *([] if args.md_time_step is None else ["--time-step", str(args.md_time_step)]),
                    *([] if args.md_save_interval_steps is None else ["--save-interval-steps", str(args.md_save_interval_steps)]),
                    *([] if args.device is None else ["--device", args.device]),
                ],
                cwd=project_root,
            )
            run_python_script(
                [
                    sys.executable,
                    str((project_root / "scripts" / "select_md_frames.py").resolve()),
                    "--config",
                    str(config_path),
                    "--round-index",
                    str(next_round_index),
                    *([] if args.max_new_points is None else ["--max-new-points", str(args.max_new_points)]),
                ],
                cwd=project_root,
            )

            next_summary_path = results_dir / f"round_{next_round_index:03d}_selection_summary.json"
            next_summary = safe_read_json(next_summary_path)
            round_record["status"] = "completed"
            round_record["next_round_index"] = next_round_index
            round_record["next_round_selection_summary_file"] = str(next_summary_path.resolve())
            round_record["next_round_selected_count"] = next_summary.get("selected_count")
            round_record["next_round_converged"] = next_summary.get("converged")
            round_record["finished_at"] = timestamp_string()
            summary["rounds"].append(round_record)
            persist_summary()

        summary["success"] = True
        summary["finished_at"] = timestamp_string()
        persist_summary()
        print(f"Active-learning experiment completed: {experiment_summary_path}")
    except Exception as exc:  # noqa: BLE001
        summary["success"] = False
        summary["finished_at"] = timestamp_string()
        summary["error_type"] = type(exc).__name__
        summary["error_message"] = str(exc)
        summary["traceback"] = traceback.format_exc()
        persist_summary()
        raise


if __name__ == "__main__":
    main()
