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
conda install -y numpy pyyaml matplotlib seaborn joblib scikit-learn
python - <<'PY'
import yaml, joblib, sklearn
print('base ok')
PY

log "Step 3: pip安装 pyh5md"
python -m pip install "${PIP_FLAGS[@]}" pyh5md
python - <<'PY'
import pyh5md
print('pyh5md ok')
PY

log "Step 4: pip安装 mlatom"
python -m pip install "${PIP_FLAGS[@]}" mlatom
python - <<'PY'
import mlatom
print('mlatom ok')
PY

log "Step 5: torch安装与校验"
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
  export TORCH_INSTALL_CMD="python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --retries 2 --timeout 20 torch==1.12.0"
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

log "Step 6: pip安装 mace-torch（或 mace）"
if python -m pip install "${PIP_FLAGS[@]}" mace-torch; then
  python - <<'PY'
import importlib
ok = importlib.util.find_spec('mace_torch') is not None or importlib.util.find_spec('mace') is not None
print('mace backend ok =', ok)
if not ok:
    raise SystemExit(1)
PY
else
  log "mace-torch install failed, fallback to mace"
  python -m pip install "${PIP_FLAGS[@]}" mace
  python - <<'PY'
import importlib
ok = importlib.util.find_spec('mace_torch') is not None or importlib.util.find_spec('mace') is not None
print('mace backend ok =', ok)
if not ok:
    raise SystemExit(1)
PY
fi

log "Step 7: training gate checks"
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb

cat <<'DONE'
[mace-step] Done.
If you are on GPU node, run:
  python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
DONE
