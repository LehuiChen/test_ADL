from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.io_utils import write_json
from minimal_adl.md_sampling import generate_ts_initial_conditions


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample round-0 TS initial conditions from the prepared TS seed.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    parser.add_argument("--round-index", type=int, default=0, help="Round index to stamp into the manifest.")
    parser.add_argument(
        "--num-initial-conditions",
        type=int,
        default=None,
        help="Override the number of initial conditions to sample.",
    )
    parser.add_argument("--output-dir", default=None, help="Override the output directory for sampled geometries.")
    parser.add_argument("--manifest", default=None, help="Override the manifest output path.")
    parser.add_argument("--summary-output", default=None, help="Optional JSON summary output path.")
    args = parser.parse_args()

    config = load_config(args.config)
    sampling_cfg = config.get("sampling", {})
    default_count = (
        sampling_cfg.get("initial_conditions_initial", 200)
        if args.round_index == 0
        else sampling_cfg.get("initial_conditions_per_round", 100)
    )
    number_of_initial_conditions = int(args.num_initial_conditions or default_count)
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "raw" / f"round_{args.round_index:03d}_initial_conditions"
    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else Path(config["paths"]["results_dir"]) / f"round_{args.round_index:03d}_initial_conditions_manifest.json"
    )
    payload = generate_ts_initial_conditions(
        config=config,
        round_index=args.round_index,
        number_of_initial_conditions=number_of_initial_conditions,
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    if args.summary_output:
        write_json(args.summary_output, payload)
    print(
        "Sampled TS initial conditions: "
        f"{payload['num_initial_conditions']} -> {payload['manifest_file']}"
    )


if __name__ == "__main__":
    main()
