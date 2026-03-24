from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from minimal_adl.config import load_config
from minimal_adl.training import train_delta_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="训练主模型：学习 delta_E + delta_F。")
    parser.add_argument("--config", required=True, help="YAML 配置文件路径。")
    args = parser.parse_args()

    config = load_config(args.config)
    state = train_delta_bundle(config=config, train_main=True, train_aux=False)
    print(f"主模型训练完成，输出文件：{state.get('main_model_file')}")


if __name__ == "__main__":
    main()

