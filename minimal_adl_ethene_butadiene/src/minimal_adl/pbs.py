from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .io_utils import ensure_dir


def build_pbs_script(
    *,
    job_name: str,
    workdir: str | Path,
    command: str,
    stdout_path: str | Path,
    stderr_path: str | Path,
    cluster_config: dict,
    method_key: str,
) -> str:
    """根据配置生成 PBS 作业脚本。"""

    workdir = Path(workdir).resolve()
    stdout_path = Path(stdout_path).resolve()
    stderr_path = Path(stderr_path).resolve()

    resources = cluster_config.get("resources_by_method", {}).get(method_key, {})
    queue = cluster_config.get("queue", "default")
    nodes = int(resources.get("nodes", cluster_config.get("nodes", 1)))
    ppn = int(resources.get("ppn", cluster_config.get("ppn", 1)))
    walltime = resources.get("walltime", cluster_config.get("walltime", "01:00:00"))
    conda_init = cluster_config.get("conda_init", "source ~/.bashrc")
    conda_env = cluster_config.get("conda_env", "aiqm")

    lines = [
        "#!/bin/bash",
        f"#PBS -N {job_name}",
        f"#PBS -q {queue}",
        f"#PBS -l nodes={nodes}:ppn={ppn}",
        f"#PBS -l walltime={walltime}",
        f"#PBS -o {stdout_path}",
        f"#PBS -e {stderr_path}",
        "",
        "set -euo pipefail",
        f"cd {workdir}",
        conda_init,
        f"conda activate {conda_env}",
        command,
        "",
    ]
    return "\n".join(lines)


def submit_job(script_path: str | Path, submit_command: str = "qsub") -> str:
    """提交 PBS 作业，返回作业号。"""

    script_path = Path(script_path).resolve()
    result = subprocess.run(
        [submit_command, str(script_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def wait_for_status_files(
    status_files: list[Path],
    *,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> None:
    """轮询等待一批 status.json 出现。"""

    start_time = time.time()
    pending = set(Path(item).resolve() for item in status_files)

    while pending:
        finished = {item for item in pending if item.exists()}
        pending -= finished
        if not pending:
            return
        if time.time() - start_time > timeout_seconds:
            pending_text = "\n".join(str(item) for item in sorted(pending))
            raise TimeoutError(f"等待作业结果超时，以下文件仍未出现：\n{pending_text}")
        time.sleep(poll_interval_seconds)


def write_pbs_script(script_path: str | Path, content: str) -> Path:
    """保存 PBS 脚本。"""

    script_path = Path(script_path)
    ensure_dir(script_path.parent)
    script_path.write_text(content, encoding="utf-8")
    return script_path

