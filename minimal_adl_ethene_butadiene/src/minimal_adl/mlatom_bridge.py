from __future__ import annotations

import importlib
import inspect
import traceback
from pathlib import Path
from typing import Any

import numpy as np

from .geometry import load_manifest
from .io_utils import read_json, write_json


def import_mlatom():
    """延迟导入 MLatom，避免在当前桌面环境中直接报错。"""

    try:
        import mlatom as ml
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "当前环境无法导入 `mlatom`。请先激活 `ADL_env`，并使用 `import mlatom as ml` 方式检查安装。"
        ) from exc
    return ml


def detect_geometry_format(geometry_path: str | Path) -> str:
    """根据文件后缀判断 MLatom 读取格式。"""

    suffix = Path(geometry_path).suffix.lower()
    if suffix == ".xyz":
        return "xyz"
    if suffix == ".json":
        return "json"
    raise ValueError(f"无法识别的几何文件格式：{geometry_path}")


def create_mlatom_method(method_config: dict[str, Any]):
    """根据配置创建一个 MLatom 方法对象。"""
    return _create_mlatom_method(method_config)


def _create_mlatom_method(
    method_config: dict[str, Any],
    *,
    working_directory: str | Path | None = None,
):
    """根据配置创建一个 MLatom 方法对象。"""

    ml = import_mlatom()
    method_name = str(method_config["method"]).strip()
    program_name = method_config.get("program")
    kwargs = {
        "method": method_name,
        "nthreads": int(method_config.get("nthreads", 1)),
        "save_files_in_current_directory": bool(method_config.get("save_files_in_current_directory", False)),
    }
    if program_name:
        kwargs["program"] = program_name

    # MLatom 3.22 在通用 ml.models.methods(...) 路径下可能提前触发 PySCF 接口导入。
    # 对于纯 xTB baseline，优先走 xTB 专用接口，避免把不需要的 PySCF 变成硬依赖。
    if method_name.lower() in {"gfn2-xtb", "gfn1-xtb", "ipea1-xtb"} and not method_config.get("program"):
        try:
            xtb_module = importlib.import_module("mlatom.interfaces.xtb_interface")
            xtb_methods = getattr(xtb_module, "xtb_methods")
            xtb_kwargs = {
                "method": method_name,
                "nthreads": int(method_config.get("nthreads", 1)),
            }
            if "save_files_in_current_directory" in inspect.signature(xtb_methods).parameters:
                xtb_kwargs["save_files_in_current_directory"] = bool(
                    method_config.get("save_files_in_current_directory", False)
                )
            return xtb_methods(**xtb_kwargs)
        except Exception:  # noqa: BLE001
            # 如果专用接口不可用，再回退到通用入口，保留原始行为。
            pass

    # 对 Gaussian target，优先走专用接口，并把工作目录固定到样本作业目录，便于保留 .com/.log 做排错。
    if str(program_name).lower() == "gaussian":
        try:
            gaussian_module = importlib.import_module("mlatom.interfaces.gaussian_interface")
            gaussian_methods = getattr(gaussian_module, "gaussian_methods")
            gaussian_kwargs = {
                "method": method_name,
                "nthreads": int(method_config.get("nthreads", 1)),
                "save_files_in_current_directory": bool(method_config.get("save_files_in_current_directory", False)),
            }
            if working_directory is not None and "working_directory" in inspect.signature(gaussian_methods).parameters:
                gaussian_kwargs["working_directory"] = str(Path(working_directory).resolve())
            return gaussian_methods(**gaussian_kwargs)
        except Exception:  # noqa: BLE001
            pass

    return ml.models.methods(**kwargs)


def _read_text_tail(path: Path, max_lines: int = 40) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:  # noqa: BLE001
        return f"<无法读取 {path.name}: {type(exc).__name__}: {exc}>"
    return "\n".join(lines[-max_lines:])


def _extract_energy_and_gradients(
    molecule: Any,
    *,
    method_config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> tuple[float, np.ndarray]:
    energy_value = None
    for attr_name in ("energy", "scf_energy"):
        if hasattr(molecule, attr_name):
            try:
                energy_value = float(getattr(molecule, attr_name))
                break
            except Exception:  # noqa: BLE001
                pass

    gradients = None
    if hasattr(molecule, "get_energy_gradients"):
        try:
            gradients = np.asarray(molecule.get_energy_gradients(), dtype=float)
        except Exception:  # noqa: BLE001
            gradients = None
    if gradients is None and hasattr(molecule, "energy_gradients"):
        try:
            gradients = np.asarray(getattr(molecule, "energy_gradients"), dtype=float)
        except Exception:  # noqa: BLE001
            gradients = None
    if gradients is None and hasattr(molecule, "get_xyz_vectorial_properties"):
        try:
            gradients = np.asarray(molecule.get_xyz_vectorial_properties("energy_gradients"), dtype=float)
        except Exception:  # noqa: BLE001
            gradients = None

    if energy_value is not None and gradients is not None:
        return energy_value, gradients

    debug_lines = [
        "MLatom 预测完成后未能从 molecule 对象中提取完整的 energy/energy_gradients。",
        f"method = {method_config.get('method')}",
        f"program = {method_config.get('program')}",
        f"molecule_attrs = {sorted(molecule.__dict__.keys())}",
    ]
    if hasattr(molecule, "error_message"):
        debug_lines.append(f"molecule.error_message = {getattr(molecule, 'error_message')}")

    if output_dir is not None:
        output_path = Path(output_dir)
        for suffix in ("*.log", "*.out", "*.com"):
            for file_path in sorted(output_path.glob(suffix)):
                debug_lines.append(f"===== {file_path.name} =====")
                debug_lines.append(_read_text_tail(file_path))

    raise RuntimeError("\n".join(debug_lines))


def label_geometry_with_mlatom(
    *,
    geometry_path: str | Path,
    method_config: dict[str, Any],
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """调用 MLatom 对一个几何做单点能和梯度计算。"""

    ml = import_mlatom()
    molecule = ml.data.molecule()
    molecule.load(str(geometry_path), format=detect_geometry_format(geometry_path))

    method = _create_mlatom_method(method_config, working_directory=output_dir)
    method.predict(
        molecule=molecule,
        calculate_energy=True,
        calculate_energy_gradients=True,
        calculate_hessian=False,
    )

    energy, gradients = _extract_energy_and_gradients(
        molecule,
        method_config=method_config,
        output_dir=output_dir,
    )
    forces = -gradients

    return {
        "success": True,
        "method": method_config["method"],
        "program": method_config.get("program"),
        "geometry_file": str(Path(geometry_path).resolve()),
        "energy": energy,
        "energy_gradients": gradients.tolist(),
        "forces": forces.tolist(),
    }


def run_and_save_label_job(
    *,
    geometry_path: str | Path,
    method_config: dict[str, Any],
    output_dir: str | Path,
    method_key: str,
) -> dict[str, Any]:
    """执行一个标注任务，并把成功或失败状态写入指定目录。"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    status_path = output_dir / "status.json"
    label_path = output_dir / "label.json"

    try:
        payload = label_geometry_with_mlatom(
            geometry_path=geometry_path,
            method_config=method_config,
            output_dir=output_dir,
        )
        payload["method_key"] = method_key
        write_json(label_path, payload)
        write_json(
            status_path,
            {
                "success": True,
                "method_key": method_key,
                "geometry_file": str(Path(geometry_path).resolve()),
                "label_file": str(label_path.resolve()),
            },
        )
        return payload
    except Exception as exc:  # noqa: BLE001
        error_payload = {
            "success": False,
            "method_key": method_key,
            "geometry_file": str(Path(geometry_path).resolve()),
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }
        write_json(status_path, error_payload)
        write_json(label_path, error_payload)
        raise


def build_molecular_database_from_dataset(
    *,
    npz_path: str | Path,
    metadata_path: str | Path,
):
    """把统一数据集转换成 MLatom 可训练的 molecular_database。"""

    ml = import_mlatom()
    dataset = np.load(npz_path, allow_pickle=True)
    metadata = read_json(metadata_path)["samples"]

    molecular_database = ml.data.molecular_database()
    geometry_files = [entry["geometry_file"] for entry in metadata]

    for index, geometry_file in enumerate(geometry_files):
        molecule = ml.data.molecule()
        molecule.load(str(geometry_file), format=detect_geometry_format(geometry_file))

        sample_id = str(dataset["sample_ids"][index])
        molecule.id = sample_id
        molecule.reference_energy = float(dataset["E_target"][index])
        molecule.baseline_energy = float(dataset["E_baseline"][index])
        molecule.delta_energy = float(dataset["delta_E"][index])
        molecule.energy = float(dataset["E_target"][index])

        reference_force = np.asarray(dataset["F_target"][index], dtype=float)
        baseline_force = np.asarray(dataset["F_baseline"][index], dtype=float)
        delta_force = np.asarray(dataset["delta_F"][index], dtype=float)

        molecule.add_xyz_vectorial_property(-reference_force, "reference_energy_gradients")
        molecule.add_xyz_vectorial_property(-baseline_force, "baseline_energy_gradients")
        molecule.add_xyz_vectorial_property(-delta_force, "delta_energy_gradients")
        molecular_database += molecule

    return molecular_database


def build_molecular_database_from_geometry_manifest(manifest_path: str | Path):
    """把未标注的几何池转成 MLatom 的 molecular_database。"""

    ml = import_mlatom()
    entries = load_manifest(manifest_path)
    molecular_database = ml.data.molecular_database()
    manifest_root = Path(manifest_path).resolve().parent.parent.parent

    for entry in entries:
        geometry_file = Path(entry["geometry_file"])
        if not geometry_file.is_absolute():
            geometry_file = manifest_root / geometry_file
        molecule = ml.data.molecule()
        molecule.load(str(geometry_file), format=detect_geometry_format(geometry_file))
        molecule.id = entry["sample_id"]
        molecular_database += molecule

    return molecular_database
