from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.md_sampling import select_md_frames


def main() -> None:
    parser = argparse.ArgumentParser(description="Select returned uncertain MD points for the next labeling round.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    parser.add_argument("--round-index", type=int, required=True, help="Round index to select from.")
    parser.add_argument("--frame-manifest", default=None, help="Override the MD frame manifest path.")
    parser.add_argument("--max-new-points", type=int, default=None, help="Override the max number of new points.")
    parser.add_argument(
        "--dedup-rmsd-threshold",
        type=float,
        default=None,
        help="Override the RMSD threshold used for deduplication.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    summary = select_md_frames(
        config=config,
        round_index=args.round_index,
        frame_manifest_path=args.frame_manifest,
        max_new_points=args.max_new_points,
        dedup_rmsd_threshold=args.dedup_rmsd_threshold,
    )
    print(
        "Selected returned MD uncertain points for round "
        f"{args.round_index}: {summary['selected_count']} kept, converged = {summary['converged']}"
    )


if __name__ == "__main__":
    main()
