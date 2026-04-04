from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.geometry import load_manifest, write_manifest
from minimal_adl.io_utils import read_json, timestamp_string, write_json


def _label_success(label_file: Path) -> bool:
    if not label_file.exists():
        return False
    try:
        payload = read_json(label_file)
    except Exception:  # noqa: BLE001
        return False
    return bool(payload.get("success", False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Append a fully labeled manifest into the cumulative labeled manifest.")
    parser.add_argument("--config", required=True, help="Path to the YAML config file.")
    parser.add_argument("--manifest", required=True, help="Manifest to append after labels are complete.")
    parser.add_argument("--output", default=None, help="Override the cumulative manifest output path.")
    args = parser.parse_args()

    config = load_config(args.config)
    manifest_path = Path(args.manifest).resolve()
    cumulative_manifest_path = Path(args.output or config["paths"]["cumulative_labeled_manifest"]).resolve()

    incoming_entries = load_manifest(manifest_path)
    if not incoming_entries:
        raise ValueError(f"No manifest entries found in {manifest_path}")

    xtb_root = Path(config["paths"]["xtb_labels_dir"]).resolve()
    gaussian_root = Path(config["paths"]["gaussian_labels_dir"]).resolve()
    for entry in incoming_entries:
        sample_id = str(entry["sample_id"])
        if not _label_success(xtb_root / sample_id / "label.json"):
            raise RuntimeError(f"Baseline label is missing or failed for {sample_id}")
        if not _label_success(gaussian_root / sample_id / "label.json"):
            raise RuntimeError(f"Target label is missing or failed for {sample_id}")

    existing_entries = load_manifest(cumulative_manifest_path) if cumulative_manifest_path.exists() else []
    existing_ids = {str(entry["sample_id"]) for entry in existing_entries}
    appended_entries = [entry for entry in incoming_entries if str(entry["sample_id"]) not in existing_ids]
    updated_entries = existing_entries + appended_entries
    write_manifest(updated_entries, cumulative_manifest_path)

    summary_path = Path(config["paths"]["results_dir"]).resolve() / "cumulative_manifest_summary.json"
    summary = {
        "manifest_file": str(cumulative_manifest_path.resolve()),
        "added_count": len(appended_entries),
        "total_count": len(updated_entries),
        "added_sample_ids": [str(entry["sample_id"]) for entry in appended_entries],
        "updated_at": timestamp_string(),
    }
    write_json(summary_path, summary)
    print(
        "Updated cumulative manifest: "
        f"{summary['added_count']} added, {summary['total_count']} total -> {summary['manifest_file']}"
    )


if __name__ == "__main__":
    main()
