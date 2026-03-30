from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.geometry import load_manifest, write_manifest
from minimal_adl.io_utils import read_json, timestamp_string, write_json
from minimal_adl.uncertainty import select_next_round_samples


def normalize_selected_ids(payload: dict) -> list[str]:
    selected_ids = payload.get("selected_sample_ids")
    if isinstance(selected_ids, list) and selected_ids:
        return [str(item) for item in selected_ids]

    selected_samples = payload.get("selected_samples", [])
    if isinstance(selected_samples, list):
        if selected_samples and isinstance(selected_samples[0], dict):
            return [str(item.get("sample_id")) for item in selected_samples if item.get("sample_id") is not None]
        return [str(item) for item in selected_samples]
    return []


def rebuild_round_history(results_dir: Path) -> dict:
    round_rows = []
    for summary_path in sorted(results_dir.glob("round_*_selection_summary.json")):
        payload = read_json(summary_path)
        round_index = int(payload.get("round_index", 0))
        selected_sample_ids = normalize_selected_ids(payload)
        selected_count = int(payload.get("selected_count") or payload.get("num_selected") or len(selected_sample_ids))
        manifest_path = results_dir / f"round_{round_index:03d}_selected_manifest.json"
        manifest_selected_count = None
        if manifest_path.exists():
            try:
                manifest_selected_count = len(load_manifest(manifest_path))
            except Exception:  # noqa: BLE001
                manifest_selected_count = None

        round_rows.append(
            {
                "round_index": round_index,
                "selected_count": selected_count,
                "selected_sample_ids": selected_sample_ids,
                "num_pool_samples": payload.get("num_pool_samples"),
                "num_uncertain_samples": payload.get("num_uncertain_samples"),
                "uncertain_ratio": payload.get("uncertain_ratio"),
                "converged": payload.get("converged"),
                "selection_summary_file": str(summary_path.resolve()),
                "selection_manifest_file": str(manifest_path.resolve()),
                "selected_manifest_exists": manifest_path.exists(),
                "manifest_selected_count": manifest_selected_count,
                "updated_at": payload.get("updated_at") or timestamp_string(),
            }
        )

    latest_round_index = max((row["round_index"] for row in round_rows), default=None)
    return {
        "total_rounds": len(round_rows),
        "latest_round_index": latest_round_index,
        "rounds": round_rows,
        "updated_at": timestamp_string(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="运行最小版主动学习样本选择逻辑。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    parser.add_argument("--manifest", required=True, help="完整几何池 manifest。")
    parser.add_argument(
        "--mode",
        choices=["auto", "initial-selection", "next-round"],
        default="auto",
        help="显式指定当前阶段：初始选点、下一轮选点，或按旧逻辑自动判断。",
    )
    parser.add_argument(
        "--uncertainty",
        default=None,
        help="不确定性结果 JSON。若数据集尚不存在，则忽略该参数并做初始 250 点选择。",
    )
    parser.add_argument("--round-index", type=int, default=0, help="当前轮次编号。")
    args = parser.parse_args()

    config = load_config(args.config)
    al_cfg = config["active_learning"]
    results_dir = Path(config["paths"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries = load_manifest(args.manifest)
    manifest_by_id = {entry["sample_id"]: entry for entry in manifest_entries}
    dataset_metadata_path = Path(config["paths"]["delta_dataset_metadata"])

    if args.mode == "next-round" and not dataset_metadata_path.exists():
        raise FileNotFoundError(
            f"你显式要求运行下一轮选点，但还没有找到 delta 数据集 metadata：{dataset_metadata_path}"
        )

    run_initial_selection = args.mode == "initial-selection" or (
        args.mode == "auto" and not dataset_metadata_path.exists()
    )

    if run_initial_selection:
        rng = random.Random(int(al_cfg.get("random_seed", 20260324)))
        initial_points = min(int(al_cfg.get("initial_points", 250)), len(manifest_entries))
        selected_entries = manifest_entries[:]
        rng.shuffle(selected_entries)
        selected_entries = selected_entries[:initial_points]

        write_manifest(selected_entries, config["paths"]["initial_selection_manifest"])
        write_json(
            results_dir / f"round_{args.round_index:03d}_initial_selection.json",
            {
                "round_index": args.round_index,
                "mode": "initial_selection",
                "num_selected": len(selected_entries),
                "selected_sample_ids": [entry["sample_id"] for entry in selected_entries],
                "notes": "论文一致：初始样本数默认 250；工程简化：当前按随机打乱后的几何池选取。",
            },
        )
        print(f"已写出初始选择 manifest：{config['paths']['initial_selection_manifest']}")
        return

    uncertainty_path = Path(
        args.uncertainty or str((results_dir / "uncertainty_latest.json").resolve())
    )
    uncertainty_payload = read_json(uncertainty_path)
    dataset_metadata = read_json(dataset_metadata_path)
    labeled_ids = {item["sample_id"] for item in dataset_metadata.get("samples", [])}
    filtered_payload = {
        **uncertainty_payload,
        "samples": [item for item in uncertainty_payload.get("samples", []) if item["sample_id"] not in labeled_ids],
    }

    selection = select_next_round_samples(
        uncertainty_payload=filtered_payload,
        max_new_points=int(al_cfg.get("max_new_points_per_round", 100)),
        convergence_ratio=float(al_cfg.get("convergence_ratio", 0.05)),
    )
    selection["round_index"] = args.round_index
    selection["selected_count"] = len(selection["selected_sample_ids"])
    selection["updated_at"] = timestamp_string()

    selected_entries = [manifest_by_id[sample_id] for sample_id in selection["selected_sample_ids"] if sample_id in manifest_by_id]
    selection_manifest_path = results_dir / f"round_{args.round_index:03d}_selected_manifest.json"
    write_manifest(selected_entries, selection_manifest_path)
    selection_summary_path = results_dir / f"round_{args.round_index:03d}_selection_summary.json"
    write_json(selection_summary_path, selection)
    write_json(results_dir / "active_learning_round_history.json", rebuild_round_history(results_dir))

    print(f"本轮新增样本数：{len(selected_entries)}")
    print(f"高不确定性比例：{selection['uncertain_ratio']:.4f}")
    print(f"是否收敛：{selection['converged']}")


if __name__ == "__main__":
    main()
