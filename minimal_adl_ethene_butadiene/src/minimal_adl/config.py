from __future__ import annotations

from pathlib import Path
from typing import Any


def _import_yaml():
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "当前环境缺少 PyYAML。请先在 aiqm 环境中安装 `PyYAML`，再运行本项目脚本。"
        ) from exc
    return yaml


def _resolve_path_values(node: Any, project_root: Path) -> Any:
    """把配置中的相对路径统一解析为绝对路径。"""

    if isinstance(node, dict):
        resolved = {}
        for key, value in node.items():
            if isinstance(value, str) and (
                "/" in value or "\\" in value or value.endswith((".json", ".npz", ".xyz", ".yaml", ".txt"))
            ):
                candidate = Path(value)
                resolved[key] = str(candidate if candidate.is_absolute() else (project_root / candidate).resolve())
            else:
                resolved[key] = _resolve_path_values(value, project_root)
        return resolved
    if isinstance(node, list):
        return [_resolve_path_values(item, project_root) for item in node]
    return node


def load_config(config_path: str | Path) -> dict[str, Any]:
    """读取 YAML 配置文件并返回字典。"""

    yaml = _import_yaml()
    config_path = Path(config_path).resolve()
    project_root = config_path.parent.parent.resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    config["config_path"] = str(config_path)
    config["project_root"] = str(project_root)
    config["paths"] = _resolve_path_values(config.get("paths", {}), project_root)
    return config


def get_method_config(config: dict[str, Any], method_key: str) -> dict[str, Any]:
    """读取 baseline 或 target 的方法配置。"""

    methods = config.get("methods", {})
    if method_key not in methods:
        raise KeyError(f"配置文件中找不到方法 `{method_key}`。")
    return methods[method_key]

