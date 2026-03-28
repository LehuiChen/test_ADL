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
from minimal_adl.io_utils import read_json, write_json
from minimal_adl.uncertainty import select_next_round_samples


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

    selected_entries = [manifest_by_id[sample_id] for sample_id in selection["selected_sample_ids"] if sample_id in manifest_by_id]
    selection_manifest_path = results_dir / f"round_{args.round_index:03d}_selected_manifest.json"
    write_manifest(selected_entries, selection_manifest_path)
    write_json(results_dir / f"round_{args.round_index:03d}_selection_summary.json", selection)

    print(f"本轮新增样本数：{len(selected_entries)}")
    print(f"高不确定性比例：{selection['uncertain_ratio']:.4f}")
    print(f"是否收敛：{selection['converged']}")


if __name__ == "__main__":
    main()
