from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.dataset import build_delta_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="把 baseline/target 标注结果组装成统一 delta 数据集。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    parser.add_argument("--manifest", default=None, help="几何池 manifest 路径，默认读取配置文件。")
    args = parser.parse_args()

    config = load_config(args.config)
    manifest_path = args.manifest or config["paths"]["geometry_pool_manifest"]

    metadata = build_delta_dataset(
        manifest_path=manifest_path,
        xtb_labels_dir=config["paths"]["xtb_labels_dir"],
        gaussian_labels_dir=config["paths"]["gaussian_labels_dir"],
        npz_output_path=config["paths"]["delta_dataset_npz"],
        metadata_output_path=config["paths"]["delta_dataset_metadata"],
    )
    print(f"delta 数据集构建完成，共 {metadata['num_samples']} 个样本。")


if __name__ == "__main__":
    main()

