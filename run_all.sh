#!/usr/bin/env bash
set -euo pipefail

WORKDIR="$(pwd)"

# این مسیر را استاد/کاربر باید تنظیم کند:
# مسیر پروژه ISCE که داخلش smallbaselineApp.cfg اجرا می‌شود
ISCE_DIR="${WORKDIR}/work/PROJECT_NAME/ISCE"

CFG="${WORKDIR}/configs/smallbaselineApp.cfg"

echo "[INFO] WORKDIR: ${WORKDIR}"
echo "[INFO] ISCE_DIR: ${ISCE_DIR}"
echo "[INFO] CFG: ${CFG}"

mkdir -p "${WORKDIR}/outputs/paper_figs" "${WORKDIR}/outputs/paper_tables"

if [ ! -d "${ISCE_DIR}" ]; then
  echo "[ERROR] ISCE_DIR not found: ${ISCE_DIR}"
  echo "        Put your ISCE project here (work/PROJECT_NAME/ISCE) or edit ISCE_DIR in run_all.sh"
  exit 1
fi

cd "${ISCE_DIR}"

echo "[STEP] MintPy processing ..."
smallbaselineApp.py "${CFG}" --dostep load_data
smallbaselineApp.py "${CFG}" --dostep modify_network
smallbaselineApp.py "${CFG}" --dostep reference_point
smallbaselineApp.py "${CFG}" --dostep invert_network
smallbaselineApp.py "${CFG}" --dostep correct_topography
smallbaselineApp.py "${CFG}" --dostep residual_RMS
smallbaselineApp.py "${CFG}" --dostep velocity

echo "[DONE] MintPy outputs should be in: ${ISCE_DIR}"
echo "       Figures/tables scripts are in: ${WORKDIR}/scripts/py"
