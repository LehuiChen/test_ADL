from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.gaussian_ts_seed import parse_gaussian_ts_log, write_ts_seed_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a Gaussian TS log into standardized TS seed artifacts.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    parser.add_argument("--log", default=None, help="Override the Gaussian TS log path.")
    args = parser.parse_args()

    config = load_config(args.config)
    log_path = Path(args.log or config["paths"]["ts_frequency_source"]).resolve()
    ts_data = parse_gaussian_ts_log(log_path)
    summary = write_ts_seed_outputs(
        ts_data=ts_data,
        json_output_path=config["paths"]["ts_seed_json"],
        xyz_output_path=config["paths"]["ts_seed_xyz"],
        summary_output_path=config["paths"]["ts_seed_summary_file"],
    )
    print(
        "Prepared TS seed from Gaussian log: "
        f"{summary['ts_seed_json']} (first imaginary frequency = {summary['first_imaginary_frequency']})"
    )


if __name__ == "__main__":
    main()
