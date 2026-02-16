#!/usr/bin/env bash
set -euo pipefail

echo "=== FULL Reproducible ISCE2 + MintPy + Paper Outputs ==="

if [[ $# -lt 2 ]]; then
echo "Usage:"
echo " bash run_all.sh <WORKDIR> <PROJECT_NAME> [CFG]"
exit 1
fi

WORKDIR="$(realpath "$1")"
PROJECT="$2"
CFG_INPUT="${3:-configs/smallbaselineApp.cfg}"

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "${CFG_INPUT}" ]]; then
CFG="$(realpath "${CFG_INPUT}")"
else
CFG="$(realpath "${REPO_DIR}/${CFG_INPUT}")"
fi

ISCE_DIR="${WORKDIR}/work/${PROJECT}/ISCE"
TOPS_XML="${REPO_DIR}/configs/topsApp.xml"
SLC_DIR="${REPO_DIR}/data/SLC"

OUT_FIGS="${WORKDIR}/outputs/paper_figs"
OUT_TABLES="${WORKDIR}/outputs/paper_tables"

mkdir -p "${OUT_FIGS}" "${OUT_TABLES}"

echo "[INFO] WORKDIR : ${WORKDIR}"
echo "[INFO] PROJECT : ${PROJECT}"
echo "[INFO] ISCE_DIR : ${ISCE_DIR}"
echo "[INFO] CFG : ${CFG}"

# --------------------------------------------------
# Environment check
# --------------------------------------------------
if ! command -v smallbaselineApp.py >/dev/null 2>&1; then
echo "[ERROR] MintPy not found. Activate environment."
exit 1
fi

if ! command -v topsApp.py >/dev/null 2>&1; then
echo "[ERROR] ISCE topsApp.py not found."
exit 1
fi

# --------------------------------------------------
# STEP 1: ISCE (if needed)
# --------------------------------------------------
if [[ ! -d "${ISCE_DIR}" ]]; then
echo "=== Running ISCE ==="
mkdir -p "${ISCE_DIR}"
cp "${TOPS_XML}" "${ISCE_DIR}/topsApp.xml"
cd "${ISCE_DIR}"
topsApp.py --steps
else
echo "[INFO] ISCE already exists → skipping"
fi

# Validate structure
if [[ ! -d "${ISCE_DIR}/mintpy_inputs" ]]; then
echo "[ERROR] mintpy_inputs missing → ISCE failed"
exit 1
fi

# --------------------------------------------------
# STEP 2: MintPy
# --------------------------------------------------
echo "=== Running MintPy ==="
cd "${ISCE_DIR}"

smallbaselineApp.py "${CFG}" --dostep load_data
smallbaselineApp.py "${CFG}" --dostep modify_network
smallbaselineApp.py "${CFG}" --dostep reference_point
smallbaselineApp.py "${CFG}" --dostep invert_network
smallbaselineApp.py "${CFG}" --dostep correct_topography
smallbaselineApp.py "${CFG}" --dostep residual_RMS
smallbaselineApp.py "${CFG}" --dostep velocity

# --------------------------------------------------
# STEP 3: Paper Figures & Tables
# --------------------------------------------------
echo "=== Generating Paper Outputs ==="

cd "${REPO_DIR}"

if [[ -f scripts/py/los_to_vertical.py ]]; then
python scripts/py/los_to_vertical.py
fi

if [[ -f scripts/py/visualize_vertical_map.py ]]; then
python scripts/py/visualize_vertical_map.py
fi

if [[ -f scripts/py/analyze_vertical_roi.py ]]; then
python scripts/py/analyze_vertical_roi.py
fi

echo ""
echo "=========================================="
echo " FULL PIPELINE COMPLETED SUCCESSFULLY"
echo "=========================================="
echo "ISCE/MintPy results: ${ISCE_DIR}"
echo "Figures folder : ${OUT_FIGS}"
echo "Tables folder : ${OUT_TABLES}"
