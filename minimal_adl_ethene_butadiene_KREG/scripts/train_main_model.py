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
from minimal_adl.gpu_monitor import GPUMonitor, is_kreg_cuda_mode
from minimal_adl.io_utils import write_json
from minimal_adl.pbs import launch_python_job
from minimal_adl.training import train_delta_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="训练主模型：学习 delta_E + delta_F。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    parser.add_argument("--submit-mode", choices=["local", "pbs"], default="local", help="运行方式。")
    parser.add_argument("--wait", dest="wait", action="store_true", help="PBS 提交后等待完成。")
    parser.add_argument("--no-wait", dest="wait", action="store_false", help="PBS 提交后直接返回。")
    parser.add_argument("--device", default=None, help="覆盖配置文件中的训练设备，例如 cuda 或 cpu。")
    parser.add_argument("--status-file", default=None, help="训练状态 JSON 路径。")
    parser.set_defaults(wait=True)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.device:
        config["training"]["device"] = args.device

    status_path = Path(args.status_file) if args.status_file else Path(config["paths"]["models_dir"]) / "train_main_status.json"
    status_path = status_path.resolve()

    if args.submit_mode == "pbs":
        job_info = launch_python_job(
            config=config,
            job_key="training",
            submit_mode="pbs",
            wait=args.wait,
            script_path=Path(__file__),
            script_args=[
                "--config",
                str(Path(config["config_path"]).resolve()),
                "--submit-mode",
                "local",
                "--status-file",
                str(status_path),
                *([] if args.device is None else ["--device", args.device]),
            ],
            output_dir=Path(config["paths"]["models_dir"]) / "jobs" / "train_main",
            status_file=status_path,
            job_name="adl_train_main",
        )
        print(f"主模型训练任务已提交：{job_info}")
        return

    kreg_cuda_mode = is_kreg_cuda_mode(config)
    monitor = GPUMonitor(
        enabled=kreg_cuda_mode,
        poll_interval_seconds=float(config.get("training", {}).get("gpu_monitor_poll_interval_seconds", 2.0)),
    )

    try:
        monitor.start()
        state = train_delta_bundle(config=config, train_main=True, train_aux=False)
        gpu_payload = monitor.stop()
        if kreg_cuda_mode and not bool(gpu_payload.get("gpu_observed", False)):
            raise RuntimeError(
                "KREG is configured with training.device=cuda, but no GPU usage was observed during training."
            )
        summary_path = Path(config["paths"]["models_dir"]) / config["training"].get("summary_filename", "training_summary.json")
        state_path = Path(config["paths"]["models_dir"]) / config["training"].get("state_filename", "training_state.json")
        write_json(
            status_path,
            {
                "success": True,
                "stage": "train_main",
                "device": config["training"]["device"],
                "kreg_cuda_mode": kreg_cuda_mode,
                "main_model_file": state.get("main_model_file"),
                "aux_model_file": state.get("aux_model_file"),
                "training_summary_file": str(summary_path.resolve()),
                "training_state_file": str(state_path.resolve()),
                "training_split_file": state.get("training_split_file"),
                "train_main_predictions_file": state.get("train_main_predictions_file"),
                "train_aux_predictions_file": state.get("train_aux_predictions_file"),
                "train_main_history_file": state.get("train_main_history_file"),
                "train_aux_history_file": state.get("train_aux_history_file"),
                **gpu_payload,
            },
        )
        print(f"主模型训练完成，输出文件：{state.get('main_model_file')}")
    except Exception as exc:  # noqa: BLE001
        gpu_payload = monitor.stop()
        write_json(
            status_path,
            {
                "success": False,
                "stage": "train_main",
                "device": config["training"]["device"],
                "kreg_cuda_mode": kreg_cuda_mode,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "traceback": traceback.format_exc(),
                **gpu_payload,
            },
        )
        raise


if __name__ == "__main__":
    main()
