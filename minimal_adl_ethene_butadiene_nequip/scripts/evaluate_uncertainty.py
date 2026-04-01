from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.io_utils import write_json
from minimal_adl.pbs import launch_python_job
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
    parser.add_argument("--submit-mode", choices=["local", "pbs"], default="local", help="运行方式。")
    parser.add_argument("--wait", dest="wait", action="store_true", help="PBS 提交后等待完成。")
    parser.add_argument("--no-wait", dest="wait", action="store_false", help="PBS 提交后直接返回。")
    parser.add_argument("--device", default=None, help="覆盖配置文件中的预测设备，例如 cuda 或 cpu。")
    parser.add_argument("--status-file", default=None, help="状态 JSON 路径。")
    parser.set_defaults(wait=True)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.device:
        config["training"]["device"] = args.device

    output_path = Path(args.output) if args.output else Path(config["paths"]["results_dir"]) / "uncertainty_latest.json"
    output_path = output_path.resolve()
    status_path = Path(args.status_file) if args.status_file else Path(config["paths"]["results_dir"]) / "uncertainty_status.json"
    status_path = status_path.resolve()

    if args.submit_mode == "pbs":
        job_info = launch_python_job(
            config=config,
            job_key="uncertainty",
            submit_mode="pbs",
            wait=args.wait,
            script_path=Path(__file__),
            script_args=[
                "--config",
                str(Path(config["config_path"]).resolve()),
                "--manifest",
                str(Path(args.manifest).resolve()),
                "--output",
                str(output_path),
                "--submit-mode",
                "local",
                "--status-file",
                str(status_path),
                *([] if args.device is None else ["--device", args.device]),
            ],
            output_dir=Path(config["paths"]["results_dir"]) / "jobs" / "uncertainty",
            status_file=status_path,
            job_name="adl_uncertainty",
        )
        print(f"不确定性评估任务已提交：{job_info}")
        return

    try:
        payload = evaluate_uncertainty_for_manifest(
            config=config,
            manifest_path=args.manifest,
            output_path=output_path,
        )
        write_json(
            status_path,
            {
                "success": True,
                "stage": "uncertainty",
                "device": config["training"]["device"],
                "output_file": str(output_path),
                "num_samples": payload["num_samples"],
            },
        )
        print(f"不确定性评估完成，共处理 {payload['num_samples']} 个样本。")
    except Exception as exc:  # noqa: BLE001
        write_json(
            status_path,
            {
                "success": False,
                "stage": "uncertainty",
                "device": config["training"]["device"],
                "output_file": str(output_path),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        raise


if __name__ == "__main__":
    main()
