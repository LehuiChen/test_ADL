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
from minimal_adl.gaussian_ts_seed import parse_gaussian_ts_log
from minimal_adl.geometry import save_xyz
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
        payload["error_message"] = "Could not import any of: " + ", ".join(candidates)
    return payload


def check_command(command_name: str, version_args: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"command": command_name, "ok": False}
    command_path = shutil.which(command_name)
    payload["path"] = command_path
    if command_path is None:
        payload["error_message"] = f"Command `{command_name}` was not found in PATH."
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

        if model_type.casefold() == "ani":
            if not str(torch.__version__).startswith("1.12"):
                payload["version_warning"] = "ANI is usually validated with torch 1.12.x."
            if torch.version.cuda not in (None, "11.3"):
                payload["cuda_warning"] = "ANI is usually validated with CUDA 11.3 builds."

        if payload["cuda_available"]:
            payload["device_name"] = torch.cuda.get_device_name(0)
        elif expect_gpu:
            payload["warning"] = "GPU was requested for checking, but torch.cuda.is_available() is False."
    except Exception as exc:  # noqa: BLE001
        payload["ok"] = False
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    return payload


def detect_model_type(config: dict[str, Any]) -> str:
    return str(config.get("training", {}).get("ml_model_type", "ANI")).strip() or "ANI"


def model_dependency_requirements(model_type: str) -> tuple[str, list[str], bool]:
    model_type_lower = model_type.casefold()
    if model_type_lower == "ani":
        return "torchani", ["torchani"], True
    if model_type_lower == "mace":
        return "mace_backend", ["mace", "mace_torch"], True
    if model_type_lower == "kreg":
        return "kreg_backend", [], False
    return "model_backend_unknown", [], False


def resolve_ts_seed_xyz(config: dict[str, Any]) -> tuple[Path, str]:
    seed_xyz_path = Path(config["paths"]["ts_seed_xyz"]).resolve()
    if seed_xyz_path.exists():
        return seed_xyz_path, "prepared_ts_seed_xyz"

    ts_data = parse_gaussian_ts_log(config["paths"]["ts_frequency_source"])
    geometry_path = Path(config["paths"]["results_dir"]).resolve() / "check_environment_ts_seed.xyz"
    geometry_path.parent.mkdir(parents=True, exist_ok=True)
    save_xyz(ts_data.geometry_record, geometry_path, comment="temporary ts seed for environment check")
    return geometry_path, "temporary_xyz_from_ts_log"


def run_optional_mlatom_xtb_test(config_path: str | Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"test": "mlatom_xtb_single_point", "ok": False}
    try:
        config = load_config(config_path)
        import mlatom as ml

        geometry_path, geometry_source = resolve_ts_seed_xyz(config)
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
        payload["geometry_source"] = geometry_source
        payload["energy"] = float(molecule.energy)
    except Exception as exc:  # noqa: BLE001
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)
        payload["traceback"] = traceback.format_exc()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether the current environment matches the active ADL backend.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "base.yaml"), help="Path to the YAML config file.")
    parser.add_argument("--expect-gpu", action="store_true", help="Also verify that CUDA is available in the current session.")
    parser.add_argument("--test-mlatom-xtb", action="store_true", help="Run a minimal mlatom + xTB single-point test.")
    parser.add_argument("--json-output", default=None, help="Optional JSON file to save the report.")
    parser.add_argument("--strict", action="store_true", help="Exit with a non-zero code when required checks fail.")
    args = parser.parse_args()

    config = load_config(args.config)
    model_type = detect_model_type(config)
    model_check_key, model_candidates, require_torch = model_dependency_requirements(model_type)
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
        "torch": check_torch_status(expect_gpu=args.expect_gpu, model_type=model_type),
        "xtb": check_command("xtb", ["--version"]),
        "g16": check_command("g16", None),
        "Gau_Mlatom.py": check_command("Gau_Mlatom.py", None),
    }

    if model_candidates:
        if len(model_candidates) == 1:
            checks[model_check_key] = check_python_module(model_candidates[0])
        else:
            checks[model_check_key] = check_any_python_module(model_candidates, check_name=model_check_key)
    elif model_type.casefold() == "kreg":
        checks[model_check_key] = {
            "ok": True,
            "note": "KREG backend support is provided by MLatom itself and does not require an extra Python package.",
        }
    else:
        checks[model_check_key] = {
            "ok": False,
            "error_message": f"Unsupported ml_model_type: {model_type}. Expected ANI, MACE, or KREG.",
        }

    report: dict[str, Any] = {
        "config_file": str(Path(config["config_path"]).resolve()),
        "python": sys.executable,
        "ml_model_type": model_type,
        "checks": checks,
    }

    if args.test_mlatom_xtb:
        report["checks"]["mlatom_xtb_single_point"] = run_optional_mlatom_xtb_test(config["config_path"])

    if args.json_output:
        write_json(args.json_output, report)

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.strict:
        required_keys = ["yaml", "mlatom", "pyh5md", "joblib", "sklearn", "xtb", model_check_key]
        if require_torch:
            required_keys.append("torch")
        if target_uses_gaussian:
            required_keys.append("g16")

        failed_checks = [key for key in required_keys if not report["checks"].get(key, {}).get("ok", False)]
        if args.test_mlatom_xtb and not report["checks"].get("mlatom_xtb_single_point", {}).get("ok", False):
            failed_checks.append("mlatom_xtb_single_point")

        if failed_checks:
            raise SystemExit("Required environment checks failed: " + ", ".join(failed_checks))


if __name__ == "__main__":
    main()
