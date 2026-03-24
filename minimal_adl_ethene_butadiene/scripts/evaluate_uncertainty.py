from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.uncertainty import evaluate_uncertainty_for_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="对几何池计算不确定性。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    parser.add_argument("--manifest", required=True, help="几何池 manifest 路径。")
    parser.add_argument(
        "--output",
        default=None,
        help="不确定性输出 JSON 路径，默认写入 results/uncertainty_latest.json。",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    output_path = args.output or str((Path(config["paths"]["results_dir"]) / "uncertainty_latest.json").resolve())
    payload = evaluate_uncertainty_for_manifest(config=config, manifest_path=args.manifest, output_path=output_path)
    print(f"不确定性评估完成，共处理 {payload['num_samples']} 个样本。")


if __name__ == "__main__":
    main()

