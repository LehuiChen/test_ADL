from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from .config import get_method_config
from .geometry import load_manifest
from .io_utils import ensure_dir, read_json, write_json
from .pbs import build_pbs_script, submit_job, wait_for_status_files, write_pbs_script


def launch_label_jobs(
    *,
    config: dict,
    manifest_path: str | Path,
    method_key: str,
    submit_mode: str,
    wait: bool,
    force: bool,
) -> list[dict]:
    """按 manifest 批量提交 baseline 或 target 标注任务。"""

    method_config = get_method_config(config, method_key)
    cluster_config = config["cluster"]
    project_root = Path(config["project_root"]).resolve()
    manifest_entries = load_manifest(manifest_path)
    labels_root = Path(config["paths"]["xtb_labels_dir"] if method_key == "baseline" else config["paths"]["gaussian_labels_dir"])
    labels_root.mkdir(parents=True, exist_ok=True)

    script_path = (project_root / "scripts" / "execute_label_job.py").resolve()
    config_path = Path(config["config_path"]).resolve()
    python_command = cluster_config.get("python_command", "python")

    submitted_jobs: list[dict] = []
    status_files: list[Path] = []

    for entry in manifest_entries:
        sample_id = entry["sample_id"]
        geometry_file = Path(entry["geometry_file"])
        if not geometry_file.is_absolute():
            geometry_file = project_root / geometry_file

        job_dir = labels_root / sample_id
        ensure_dir(job_dir)
        label_file = job_dir / "label.json"
        status_file = job_dir / "status.json"
        status_files.append(status_file)

        if not force and label_file.exists():
            try:
                payload = read_json(label_file)
                if payload.get("success", False):
                    submitted_jobs.append(
                        {
                            "sample_id": sample_id,
                            "method_key": method_key,
                            "status": "skipped_existing_success",
                            "job_dir": str(job_dir.resolve()),
                        }
                    )
                    continue
            except Exception:  # noqa: BLE001
                pass

        write_json(job_dir / "job_meta.json", {"sample_id": sample_id, "geometry_file": str(geometry_file.resolve())})

        local_cmd = [
            python_command,
            str(script_path),
            "--config",
            str(config_path),
            "--geometry",
            str(geometry_file.resolve()),
            "--method-key",
            method_key,
            "--output-dir",
            str(job_dir.resolve()),
        ]

        if submit_mode == "local":
            subprocess.run(local_cmd, check=True, cwd=project_root)
            submitted_jobs.append(
                {
                    "sample_id": sample_id,
                    "method_key": method_key,
                    "status": "ran_locally",
                    "job_dir": str(job_dir.resolve()),
                }
            )
            continue

        if submit_mode != "pbs":
            raise ValueError("submit_mode 只能是 `local` 或 `pbs`。")

        quoted_command = " ".join(shlex.quote(part) for part in local_cmd)
        pbs_text = build_pbs_script(
            job_name=f"{method_key[:3]}_{sample_id[-8:]}",
            workdir=project_root,
            command=quoted_command,
            stdout_path=job_dir / "stdout.log",
            stderr_path=job_dir / "stderr.log",
            cluster_config=cluster_config,
            method_key=method_key,
        )
        script_file = write_pbs_script(job_dir / "job.pbs", pbs_text)
        job_id = submit_job(script_file, submit_command=cluster_config.get("submit_command", "qsub"))
        submitted_jobs.append(
            {
                "sample_id": sample_id,
                "method_key": method_key,
                "status": "submitted",
                "job_id": job_id,
                "job_dir": str(job_dir.resolve()),
            }
        )

    if wait and submit_mode == "pbs":
        wait_for_status_files(
            status_files,
            timeout_seconds=int(cluster_config.get("poll_timeout_seconds", 86400)),
            poll_interval_seconds=int(cluster_config.get("poll_interval_seconds", 30)),
        )

    return submitted_jobs

