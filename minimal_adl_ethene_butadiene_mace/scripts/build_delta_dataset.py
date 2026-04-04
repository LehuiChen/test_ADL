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
    parser = argparse.ArgumentParser(description="Assemble the labeled samples into a unified delta-learning dataset.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    parser.add_argument("--manifest", default=None, help="Override the source manifest path.")
    args = parser.parse_args()

    config = load_config(args.config)
    manifest_path = args.manifest or config["paths"]["cumulative_labeled_manifest"]

    metadata = build_delta_dataset(
        manifest_path=manifest_path,
        xtb_labels_dir=config["paths"]["xtb_labels_dir"],
        gaussian_labels_dir=config["paths"]["gaussian_labels_dir"],
        npz_output_path=config["paths"]["delta_dataset_npz"],
        metadata_output_path=config["paths"]["delta_dataset_metadata"],
        project_root=config["project_root"],
    )
    print(f"Built delta dataset with {metadata['num_samples']} labeled samples -> {config['paths']['delta_dataset_npz']}")


if __name__ == "__main__":
    main()
