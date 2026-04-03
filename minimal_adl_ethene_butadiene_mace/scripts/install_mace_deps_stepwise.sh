#!/usr/bin/env bash
set -euo pipefail

# Stepwise installer for ADL_MACE dependencies.
# Usage:
#   conda activate ADL_MACE
#   bash scripts/install_mace_deps_stepwise.sh
#
# Optional env vars:
#   PIP_INDEX_URL (default: Tsinghua mirror)
#   TORCH_INSTALL_CMD (required for torch step if not already installed)

PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
PIP_FLAGS=( -i "$PIP_INDEX_URL" --retries 2 --timeout 20 )

log() { echo "[mace-step] $*"; }

check_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[mace-step][ERROR] Missing command: $cmd" >&2
    exit 1
  fi
}

check_cmd conda
check_cmd python

log "Python executable: $(command -v python)"
python -V

log "Step 0: mirror reachability test"
python -m pip install "${PIP_FLAGS[@]}" packaging==24.2
python - <<'PY'
import packaging
print('packaging ok:', packaging.__version__)
PY

log "Step 1: conda基础工具"
conda install -y pip setuptools wheel
python -V
which python

log "Step 2: conda科学栈"
conda install -y numpy=1.26 scipy pandas pyyaml matplotlib seaborn joblib scikit-learn h5py statsmodels tqdm
python - <<'PY'
import yaml, joblib, sklearn, pandas, numpy
print('base ok')
print('numpy version =', numpy.__version__)
PY

log "Step 3: pip安装 pyh5md"
python -m pip install "${PIP_FLAGS[@]}" pyh5md
python - <<'PY'
import pyh5md
print('pyh5md ok')
PY

log "Step 4: pip安装 mlatom（固定为 --no-deps）"
python -m pip install "${PIP_FLAGS[@]}" mlatom --no-deps
python -m pip install "${PIP_FLAGS[@]}" requests==2.32.3 urllib3==2.2.3 idna==3.10 charset-normalizer==3.4.0
python - <<'PY'
import mlatom
print('mlatom ok')
PY

log "Step 5: torch安装与校验（当前仓库默认按 CPU 训练）"
if python - <<'PY'
import importlib
raise SystemExit(0 if importlib.util.find_spec('torch') else 1)
PY
then
  log "Detected existing torch; skip install."
else
  if [[ -z "${TORCH_INSTALL_CMD:-}" ]]; then
    cat >&2 <<'MSG'
[mace-step][ERROR] torch not found and TORCH_INSTALL_CMD is empty.
Please set TORCH_INSTALL_CMD first, for example:
  export TORCH_INSTALL_CMD="python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --retries 2 --timeout 20 torch==2.6.0"
Then re-run this script.
MSG
    exit 1
  fi
  log "Run TORCH_INSTALL_CMD"
  eval "$TORCH_INSTALL_CMD"
fi
python - <<'PY'
import torch
print('torch version =', torch.__version__)
print('torch cuda =', torch.version.cuda)
print('torch cuda available =', torch.cuda.is_available())
PY

log "Step 6: 安装 MACE 后端与配套依赖"
conda install -y -c conda-forge ase matscipy
python -m pip uninstall -y mace-torch mace e3nn || true
python -m pip install "${PIP_FLAGS[@]}" mace-torch==0.3.11 --no-deps
python -m pip install "${PIP_FLAGS[@]}" e3nn==0.4.4 opt_einsum prettytable torch-ema configargparse GitPython lmdb orjson python-hostlist torchmetrics opt_einsum_fx lightning-utilities --no-deps
python - <<'PY'
import os
os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
import torch
import e3nn
import mace
import ase
import matscipy
print('torch version =', torch.__version__)
print('e3nn version =', e3nn.__version__)
print('mace backend ok =', True)
PY

log "Step 7: training gate checks"
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb

cat <<'DONE'
[mace-step] Done.
This repository now defaults to CPU training for MACE on the current cluster.
Recommended next step:
  python scripts/train_main_model.py --config configs/base.yaml --submit-mode pbs
DONE
