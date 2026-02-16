Reproducible Sentinel-1 InSAR Processing Pipeline
ISCE2 (TOPS) + MintPy (SBAS Time-Series)










📌 Overview

This repository provides a fully reproducible, end-to-end InSAR processing pipeline for Sentinel-1 data using:

ISCE2 (TOPS mode) → Interferometric processing

MintPy (SBAS) → Time-series deformation analysis

The workflow is designed for:

🎓 Academic research

📈 Ground deformation / subsidence studies

🔁 Reproducible thesis results

🧠 Processing Workflow
Sentinel-1 SAFE / SLC
        │
        ▼
ISCE2 (TOPSApp)
  - Coregistration
  - Interferogram formation
  - Filtering
  - Unwrapping
        │
        ▼
MintPy (SmallBaselineApp)
  - Stack loading
  - Network inversion
  - Time-series estimation
  - Velocity estimation
        │
        ▼
Final deformation maps & time-series

🗂 Repository Structure
subsidence-farazghorbani_repo/
│
├── configs/
│   ├── topsApp.xml
│   └── smallbaselineApp.cfg
│
├── run_all.sh
├── environment.yml
└── README.md

📁 Expected Working Directory Structure

The pipeline expects this structure outside the repo:

<WORKDIR>/
│
├── data/
│   ├── SAFE/        (Sentinel-1 SAFE or .zip)
│   ├── SLC/         (Optional: prepared SLC stack)
│   ├── ORBIT/       (Precise orbit files)
│   └── DEM/         (DEM files)
│
├── work/
│   └── <PROJECT>/
│
└── outputs/


Example:

/mnt/data2/insar_chain

⚙️ Installation
1️⃣ Create Conda Environment
conda env create -f environment.yml
conda activate insar-full

2️⃣ Verify Installation
which topsApp.py
which smallbaselineApp.py


Both must return valid paths.

🛰 Supported Input Modes

The pipeline supports two modes:

Mode	Description	Recommended
SAFE	Raw Sentinel-1 SAFE / zip files	✅ Yes
SLC	Pre-processed SLC stack	Optional
▶️ Running the Pipeline

Go to repository root:

cd subsidence-farazghorbani_repo
conda activate insar-full

✅ SAFE Mode (Full Automatic Processing)
./run_all.sh \
  /mnt/data2/insar_chain \
  tehran_s1_test \
  configs/smallbaselineApp.cfg \
  --mode safe

✅ SLC Mode
./run_all.sh \
  /mnt/data2/insar_chain \
  tehran_s1_test \
  configs/smallbaselineApp.cfg \
  --mode slc

🧾 Command Arguments
Argument	Description
WORKDIR	Root working directory
PROJECT	Project name
CFG	MintPy configuration file
--mode	safe or slc
--skip-isce	Skip ISCE step
--reset-mintpy	Remove MintPy results before rerun
📤 Outputs

After successful execution:

ISCE results:
<WORKDIR>/work/<PROJECT>/ISCE

MintPy results:
<WORKDIR>/work/<PROJECT>/mintpy

Final figures:
<WORKDIR>/outputs

🔬 Reproducibility Statement

This pipeline guarantees reproducibility through:

Fixed configuration files

Controlled Conda environment

Deterministic processing order

Explicit directory structure

Tested with:

ISCE2 v2.6.x

MintPy (stable release)

Python 3.9

Sentinel-1 IW TOPS mode

Results are reproducible given identical input datasets.

🛠 Troubleshooting
❌ SAFE_DIR not found

Ensure:

<WORKDIR>/data/SAFE


contains Sentinel-1 SAFE or zip files.

❌ smallbaselineApp.cfg not found

Pass config relative to repo root:

configs/smallbaselineApp.cfg

❌ ISCE preprocess NoneType error

Usually caused by:

Empty SAFE directory

Missing orbit files

Missing DEM

Verify:

ls <WORKDIR>/data/SAFE
ls <WORKDIR>/data/ORBIT
ls <WORKDIR>/data/DEM
