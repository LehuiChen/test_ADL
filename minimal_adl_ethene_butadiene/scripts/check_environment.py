from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.io_utils import write_json
from minimal_adl.mlatom_bridge import create_mlatom_method


def check_python_module(module_name: str) -> dict[str, Any]:
    """检查一个 Python 模块是否可以导入，并尽量返回版本信息。"""

    payload: dict[str, Any] = {"module": module_name, "ok": False}
    try:
        module = importlib.import_module(module_name)
        payload["ok"] = True
        payload["file"] = getattr(module, "__file__", None)
        payload["version"] = getattr(module, "__version__", None)
    except Exception as exc:  # noqa: BLE001
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    return payload


def check_command(command_name: str, version_args: list[str] | None = None) -> dict[str, Any]:
    """检查一个外部命令是否存在，并尝试读取版本输出。"""

    payload: dict[str, Any] = {"command": command_name, "ok": False}
    command_path = shutil.which(command_name)
    payload["path"] = command_path
    if command_path is None:
        payload["error_message"] = f"在当前 PATH 中找不到命令 `{command_name}`。"
        return payload

    payload["ok"] = True
    if version_args:
        try:
            result = subprocess.run(
                [command_name, *version_args],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            payload["returncode"] = result.returncode
            payload["stdout"] = result.stdout.strip()
            payload["stderr"] = result.stderr.strip()
        except Exception as exc:  # noqa: BLE001
            payload["version_error"] = f"{type(exc).__name__}: {exc}"
    return payload


def check_torch_status(expect_gpu: bool) -> dict[str, Any]:
    """单独检查 torch 的 CUDA 状态。"""

    payload = check_python_module("torch")
    if not payload.get("ok"):
        return payload

    try:
        import torch

        payload["torch_version"] = torch.__version__
        payload["cuda_version"] = torch.version.cuda
        payload["cuda_available"] = bool(torch.cuda.is_available())
        payload["expected_gpu"] = expect_gpu
        if not str(torch.__version__).startswith("1.12"):
            payload["version_warning"] = "当前 torch 版本不是推荐的 1.12.x，ANI 老驱动兼容方案可能失效。"
        if torch.version.cuda not in (None, "11.3"):
            payload["cuda_warning"] = "当前 torch 绑定的 CUDA 版本不是推荐的 11.3。"
        if payload["cuda_available"]:
            payload["device_name"] = torch.cuda.get_device_name(0)
        elif expect_gpu:
            payload["warning"] = "当前要求检查 GPU，但 torch.cuda.is_available() 为 False。请确认现在位于 GPU 节点。"
    except Exception as exc:  # noqa: BLE001
        payload["ok"] = False
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    return payload


def run_optional_mlatom_xtb_test(config_path: str | Path) -> dict[str, Any]:
    """可选：直接做一次最小的 mlatom + xtb 单点测试。"""

    payload: dict[str, Any] = {"test": "mlatom_xtb_single_point", "ok": False}
    try:
        config = load_config(config_path)
        import mlatom as ml

        geometry_path = Path(config["paths"]["seed_geometry"]).resolve()
        molecule = ml.data.molecule()
        molecule.load(str(geometry_path), format="xyz")
        method = create_mlatom_method(
            {
                "method": "GFN2-xTB",
                "nthreads": 4,
                "save_files_in_current_directory": False,
            }
        )
        method.predict(
            molecule=molecule,
            calculate_energy=True,
            calculate_energy_gradients=True,
            calculate_hessian=False,
        )
        payload["ok"] = True
        payload["geometry_file"] = str(geometry_path)
        payload["energy"] = float(molecule.energy)
    except Exception as exc:  # noqa: BLE001
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 ADL_env 环境是否满足最小 ADL 项目的运行要求。")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "base.yaml"), help="配置文件路径。")
    parser.add_argument("--expect-gpu", action="store_true", help="如果你当前在 GPU 节点上，可以打开这个选项检查 CUDA。")
    parser.add_argument("--test-mlatom-xtb", action="store_true", help="额外执行一次最小的 mlatom + xtb 单点测试。")
    parser.add_argument("--json-output", default=None, help="把检查结果写入 JSON 文件。")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "config_file": str(Path(args.config).resolve()),
        "python": sys.executable,
        "checks": {
            "yaml": check_python_module("yaml"),
            "mlatom": check_python_module("mlatom"),
            "pyh5md": check_python_module("pyh5md"),
            "joblib": check_python_module("joblib"),
            "sklearn": check_python_module("sklearn"),
            "torch": check_torch_status(expect_gpu=args.expect_gpu),
            "torchani": check_python_module("torchani"),
            "xtb": check_command("xtb", ["--version"]),
            "g16": check_command("g16", None),
            "Gau_Mlatom.py": check_command("Gau_Mlatom.py", None),
        },
    }

    if args.test_mlatom_xtb:
        report["checks"]["mlatom_xtb_single_point"] = run_optional_mlatom_xtb_test(args.config)

    if args.json_output:
        write_json(args.json_output, report)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
