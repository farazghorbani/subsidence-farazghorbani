#!/usr/bin/env bash
set -euo pipefail

echo "=== Reproducible ISCE2 + MintPy pipeline ==="

usage() {
cat <<EOF
Usage:
bash run_all.sh <WORKDIR> <PROJECT_NAME> [CFG_PATH] [--skip-isce] [--reset-mintpy]

Arguments:
WORKDIR Base working directory on your machine (e.g. /mnt/data2/insar_chain)
PROJECT_NAME Project name (e.g. tehran_s1_test)
CFG_PATH Optional. Path to MintPy smallbaselineApp cfg (default: <repo>/configs/smallbaselineApp.cfg)

Options:
--skip-isce Skip topsApp.py (ISCE processing) and run MintPy only (recommended if you already have an ISCE project)
--reset-mintpy Remove <ISCE_DIR>/inputs to force MintPy re-load (fixes missing ifgramStack.h5 issues)

Example:
bash run_all.sh /mnt/data2/insar_chain tehran_s1_test configs/smallbaselineApp.cfg --skip-isce --reset-mintpy
EOF
}

# ---------- parse args ----------
if [[ $# -lt 2 ]]; then
usage
exit 1
fi

WORKDIR="$(realpath "$1")"
PROJECT_NAME="$2"
shift 2

# repo dir = location of this script
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CFG="${1:-$REPO_DIR/configs/smallbaselineApp.cfg}"
if [[ $# -ge 1 ]]; then shift 1; fi

SKIP_ISCE="no"
RESET_MINTPY="no"
for arg in "$@"; do
case "$arg" in
--skip-isce) SKIP_ISCE="yes" ;;
--reset-mintpy) RESET_MINTPY="yes" ;;
-h|--help) usage; exit 0 ;;
*) echo "[ERROR] Unknown option: $arg"; usage; exit 1 ;;
esac
done

# ---------- derived paths ----------
ISCE_DIR="${WORKDIR}/work/${PROJECT_NAME}/ISCE"
OUT_DIR="${WORKDIR}/outputs"

echo "[INFO] REPO_DIR : ${REPO_DIR}"
echo "[INFO] WORKDIR : ${WORKDIR}"
echo "[INFO] PROJECT : ${PROJECT_NAME}"
echo "[INFO] ISCE_DIR : ${ISCE_DIR}"
echo "[INFO] MintPy CFG : ${CFG}"
echo "[INFO] SKIP_ISCE : ${SKIP_ISCE}"
echo "[INFO] RESET_MINTPY: ${RESET_MINTPY}"

mkdir -p "${OUT_DIR}/paper_figs" "${OUT_DIR}/paper_tables"
mkdir -p "$(dirname "${ISCE_DIR}")"

# ---------- tool checks ----------
if ! command -v python >/dev/null 2>&1; then
echo "[ERROR] python not found"
exit 1
fi
if ! command -v smallbaselineApp.py >/dev/null 2>&1; then
echo "[ERROR] smallbaselineApp.py not found in PATH. Activate conda env first."
exit 1
fi

# ISCE tool (topsApp.py) is optional if --skip-isce
if [[ "${SKIP_ISCE}" == "no" ]]; then
if ! command -v topsApp.py >/dev/null 2>&1; then
echo "[ERROR] topsApp.py not found in PATH."
echo " If you already have an ISCE project, run with --skip-isce."
exit 1
fi
fi

# ---------- ensure ISCE project exists ----------
if [[ ! -d "${ISCE_DIR}" ]]; then
cat <<EOF
[ERROR] ISCE_DIR not found: ${ISCE_DIR}

Put/Link your processed ISCE project here:
${WORKDIR}/work/${PROJECT_NAME}/ISCE

Tip (symlink example):
ln -s /path/to/your_existing_ISCE_project ${WORKDIR}/work/${PROJECT_NAME}/ISCE
EOF
exit 1
fi

# CFG exists?
if [[ ! -f "${CFG}" ]]; then
echo "[ERROR] MintPy config not found: ${CFG}"
exit 1
fi

# ---------- optional: reset mintpy ----------
if [[ "${RESET_MINTPY}" == "yes" ]]; then
echo "[WARN] Resetting MintPy by removing: ${ISCE_DIR}/inputs"
rm -rf "${ISCE_DIR}/inputs"
fi

# ---------- run pipeline ----------
cd "${ISCE_DIR}"

if [[ "${SKIP_ISCE}" == "no" ]]; then
echo "=== STEP 1: ISCE2 (topsApp) ==="
# If you use topsStack / topsApp XML, ensure it is present in ISCE_DIR.
# Typical usage:
# topsApp.py topsApp.xml --steps
#
# If your workflow uses a prepared XML, keep it in ISCE_DIR as topsApp.xml.
if [[ -f "topsApp.xml" ]]; then
topsApp.py topsApp.xml --steps
else
echo "[ERROR] topsApp.xml not found in ${ISCE_DIR}."
echo " Either add it, or run with --skip-isce (if ISCE already processed)."
exit 1
fi
else
echo "=== STEP 1: ISCE2 skipped ==="
fi

echo "=== STEP 2: MintPy (smallbaselineApp) ==="
# IMPORTANT: run MintPy INSIDE ISCE_DIR so relative paths in cfg resolve correctly.
smallbaselineApp.py "${CFG}" --dostep load_data
smallbaselineApp.py "${CFG}" --dostep modify_network
smallbaselineApp.py "${CFG}" --dostep reference_point
smallbaselineApp.py "${CFG}" --dostep invert_network
smallbaselineApp.py "${CFG}" --dostep correct_topography
smallbaselineApp.py "${CFG}" --dostep residual_RMS
smallbaselineApp.py "${CFG}" --dostep velocity

echo "=== STEP 3: Custom post-processing (optional) ==="
cd "${WORKDIR}"

if [[ -d "${REPO_DIR}/scripts/py" ]]; then
# Run only if scripts exist; do not fail if missing
for s in los_to_vertical.py visualize_vertical_map.py analyze_vertical_roi.py; do
if [[ -f "${REPO_DIR}/scripts/py/${s}" ]]; then
python "${REPO_DIR}/scripts/py/${s}" || echo "[WARN] Script failed: ${s}"
fi
done
fi

echo "[DONE] ISCE project: ${ISCE_DIR}"
echo "[DONE] MintPy outputs typically in: ${ISCE_DIR}/inputs and ${ISCE_DIR}/pic"
echo "[DONE] Paper outputs folder: ${OUT_DIR}"

