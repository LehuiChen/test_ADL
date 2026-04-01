from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import get_method_config, load_config
from minimal_adl.mlatom_bridge import create_mlatom_method, import_mlatom


def main() -> None:
    parser = argparse.ArgumentParser(description="可选工具：用 MLatom + Gaussian/xTB 做一个 TS 几何优化。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    parser.add_argument("--geometry", required=True, help="输入几何文件。")
    parser.add_argument("--method-key", choices=["baseline", "target"], default="target", help="使用哪种方法优化。")
    parser.add_argument("--output", required=True, help="优化后 xyz 输出路径。")
    args = parser.parse_args()

    ml = import_mlatom()
    config = load_config(args.config)
    method = create_mlatom_method(get_method_config(config, args.method_key))

    molecule = ml.data.molecule()
    molecule.load(args.geometry, format=Path(args.geometry).suffix.lstrip(".").lower())
    geomopt = ml.optimize_geometry(
        ts=True,
        model=method,
        initial_molecule=molecule,
        program="gaussian" if args.method_key == "target" else None,
    )
    optimized = geomopt.optimized_molecule
    optimized.write_file_with_xyz_coordinates(filename=args.output)
    print(f"优化完成，结果已写入 {args.output}")


if __name__ == "__main__":
    main()
