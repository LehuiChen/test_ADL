from __future__ import annotations

from pathlib import Path
from typing import Any


def _import_yaml():
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyYAML is required to load this project config. Install PyYAML in your KREG environment first."
        ) from exc
    return yaml


def _resolve_path_values(node: Any, project_root: Path) -> Any:
    if isinstance(node, dict):
        resolved: dict[str, Any] = {}
        for key, value in node.items():
            if isinstance(value, str) and (
                "/" in value or "\\" in value or value.endswith((".json", ".npz", ".xyz", ".yaml", ".txt", ".log"))
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
    methods = config.get("methods", {})
    if method_key not in methods:
        raise KeyError(f"Method '{method_key}' is missing from the config file.")
    return methods[method_key]