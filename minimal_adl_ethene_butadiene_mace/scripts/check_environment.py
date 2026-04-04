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


def check_any_python_module(candidates: list[str], *, check_name: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "check": check_name,
        "candidates": candidates,
        "ok": False,
        "resolved_module": None,
        "details": {},
    }
    for module_name in candidates:
        result = check_python_module(module_name)
        payload["details"][module_name] = result
        if result.get("ok", False):
            payload["ok"] = True
            payload["resolved_module"] = module_name
            break
    if not payload["ok"]:
        payload["error_message"] = " / ".join(candidates) + " 均不可导入。"
    return payload


def check_command(command_name: str, version_args: list[str] | None = None) -> dict[str, Any]:
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


def check_torch_status(expect_gpu: bool, *, model_type: str) -> dict[str, Any]:
    payload = check_python_module("torch")
    if not payload.get("ok"):
        return payload

    try:
        import torch

        payload["torch_version"] = torch.__version__
        payload["cuda_version"] = torch.version.cuda
        payload["cuda_available"] = bool(torch.cuda.is_available())
        payload["expected_gpu"] = expect_gpu
        payload["model_type"] = model_type

        model_type_lower = model_type.casefold()
        if model_type_lower == "ani":
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
    payload: dict[str, Any] = {"test": "mlatom_xtb_single_point", "ok": False}
    try:
        config = load_config(config_path)
        import mlatom as ml

        geometry_path = Path(config["paths"]["ts_seed_xyz"]).resolve()
        if not geometry_path.exists():
            raise FileNotFoundError(
                f"TS seed XYZ is missing: {geometry_path}. Run scripts/prepare_ts_seed.py first."
            )
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


def detect_model_type(config: dict[str, Any]) -> str:
    return str(config.get("training", {}).get("ml_model_type", "ANI")).strip() or "ANI"


def model_dependency_requirements(model_type: str) -> tuple[str, list[str], str]:
    model_type_lower = model_type.casefold()
    if model_type_lower == "ani":
        return "torchani", ["torchani"], "ANI"
    if model_type_lower == "mace":
        return "mace_backend", ["mace", "mace_torch"], "MACE"
    if model_type_lower == "nequip":
        return "nequip", ["nequip"], "NequIP"
    return "model_backend_unknown", [], model_type


def main() -> None:
    parser = argparse.ArgumentParser(description="检查 ADL 环境是否满足当前模型后端的运行要求。")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "base.yaml"), help="配置文件路径。")
    parser.add_argument("--expect-gpu", action="store_true", help="如果你当前在 GPU 节点上，可以打开这个选项检查 CUDA。")
    parser.add_argument("--test-mlatom-xtb", action="store_true", help="额外执行一次最小 mlatom + xtb 单点测试。")
    parser.add_argument("--json-output", default=None, help="将检查结果写入 JSON 文件。")
    parser.add_argument("--strict", action="store_true", help="若关键依赖缺失，则以非零状态码退出。")
    args = parser.parse_args()

    config = load_config(args.config)
    model_type = detect_model_type(config)
    model_check_key, model_candidates, model_display_name = model_dependency_requirements(model_type)
    target_uses_gaussian = str(config.get("methods", {}).get("target", {}).get("program", "")).lower() == "gaussian"

    checks: dict[str, Any] = {
        "yaml": check_python_module("yaml"),
        "pandas": check_python_module("pandas"),
        "matplotlib": check_python_module("matplotlib"),
        "seaborn": check_python_module("seaborn"),
        "mlatom": check_python_module("mlatom"),
        "pyh5md": check_python_module("pyh5md"),
        "joblib": check_python_module("joblib"),
        "sklearn": check_python_module("sklearn"),
        "torch": check_torch_status(expect_gpu=args.expect_gpu, model_type=model_display_name),
        "xtb": check_command("xtb", ["--version"]),
        "g16": check_command("g16", None),
        "Gau_Mlatom.py": check_command("Gau_Mlatom.py", None),
    }

    if model_candidates:
        if len(model_candidates) == 1:
            checks[model_check_key] = check_python_module(model_candidates[0])
        else:
            checks[model_check_key] = check_any_python_module(model_candidates, check_name=model_check_key)
    else:
        checks[model_check_key] = {
            "ok": False,
            "error_message": f"未知 ml_model_type: {model_type}，当前仅支持 ANI/MACE/NequIP。",
        }

    report: dict[str, Any] = {
        "config_file": str(Path(config["config_path"]).resolve()),
        "ml_model_type": model_type,
        "checks": checks,
    }

    if args.test_mlatom_xtb:
        report["checks"]["mlatom_xtb_single_point"] = run_optional_mlatom_xtb_test(config["config_path"])

    if args.json_output:
        write_json(args.json_output, report)

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.strict:
        required_keys = ["yaml", "mlatom", "pyh5md", "joblib", "sklearn", "torch", "xtb", model_check_key]
        if target_uses_gaussian:
            required_keys.append("g16")

        failed_checks = [
            key
            for key in required_keys
            if not report["checks"].get(key, {}).get("ok", False)
        ]
        if args.test_mlatom_xtb and not report["checks"].get("mlatom_xtb_single_point", {}).get("ok", False):
            failed_checks.append("mlatom_xtb_single_point")

        if failed_checks:
            raise SystemExit("关键环境检查未通过：" + ", ".join(failed_checks))


if __name__ == "__main__":
    main()

