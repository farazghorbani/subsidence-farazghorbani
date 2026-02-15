#!/usr/bin/env bash
set -euo pipefail

echo "=== Reproducible ISCE2 + MintPy pipeline ==="

# -------------------------
# Usage
# -------------------------
if [[ $# -lt 2 ]]; then
  echo "Usage:"
  echo "  bash run_all.sh <WORKDIR> <PROJECT_NAME> [CFG_PATH]"
  echo ""
  echo "Example:"
  echo "  bash run_all.sh /mnt/data2/insar_chain tehran_s1_test configs/smallbaselineApp.cfg"
  exit 1
fi

WORKDIR="$(realpath "$1")"
PROJECT_NAME="$2"
CFG="${3:-$WORKDIR/configs/smallbaselineApp.cfg}"

ISCE_DIR="${WORKDIR}/work/${PROJECT_NAME}/ISCE"

echo "[INFO] WORKDIR    : ${WORKDIR}"
echo "[INFO] PROJECT    : ${PROJECT_NAME}"
echo "[INFO] ISCE_DIR   : ${ISCE_DIR}"
echo "[INFO] MintPy CFG : ${CFG}"

# outputs
mkdir -p "${WORKDIR}/outputs/paper_figs" "${WORKDIR}/outputs/paper_tables"

# sanity checks
command -v topsApp.py >/dev/null 2>&1 || { echo "[ERROR] topsApp.py not found in PATH"; exit 1; }
command -v smallbaselineApp.py >/dev/null 2>&1 || { echo "[ERROR] smallbaselineApp.py not found in PATH"; exit 1; }

if [[ ! -d "${ISCE_DIR}" ]]; then
  echo "[ERROR] ISCE_DIR not found: ${ISCE_DIR}"
  echo "Put your ISCE project here:"
  echo "  ${WORKDIR}/work/${PROJECT_NAME}/ISCE"
  exit 1
fi

if [[ ! -f "${CFG}" ]]; then
  echo "[ERROR] MintPy config not found: ${CFG}"
  exit 1
fi

# -------------------------
# Step 1: ISCE (optional)
# -------------------------
# If you want to run ISCE, uncomment the next lines.
# echo "[STEP] Running ISCE topsApp..."
# cd "${ISCE_DIR}"
# topsApp.py --steps

# -------------------------
# Step 2: MintPy
# -------------------------
echo "[STEP] Running MintPy processing..."
cd "${ISCE_DIR}"

smallbaselineApp.py "${CFG}" --dostep load_data
smallbaselineApp.py "${CFG}" --dostep modify_network
smallbaselineApp.py "${CFG}" --dostep reference_point
smallbaselineApp.py "${CFG}" --dostep invert_network
smallbaselineApp.py "${CFG}" --dostep correct_topography
smallbaselineApp.py "${CFG}" --dostep residual_RMS
smallbaselineApp.py "${CFG}" --dostep velocity

# -------------------------
# Step 3: Post-processing scripts
# -------------------------
echo "[STEP] Running custom post-processing scripts..."
cd "${WORKDIR}"

python scripts/py/los_to_vertical.py
python scripts/py/visualize_vertical_map.py
python scripts/py/analyze_vertical_roi.py

echo "=== DONE ==="
echo "[DONE] MintPy outputs are in: ${ISCE_DIR}"
echo "[DONE] Figures/tables output folder: ${WORKDIR}/outputs"
