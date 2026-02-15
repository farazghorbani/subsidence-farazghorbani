Subsidence Monitoring using ISCE2 + MintPy

Reproducible InSAR processing pipeline for land subsidence monitoring using Sentinel-1 data, ISCE2, and MintPy.
This repository contains code-only workflow (no raw SAR data).

1. Requirements

Linux (Ubuntu recommended)

Conda / Miniconda

ISCE2 installed and configured

SNAP is NOT used in this workflow

2. Clone Repository
git clone https://github.com/farazghorbani/subsidence-farazghorbani.git
cd subsidence-farazghorbani

3. Create Conda Environment
conda env create -f environment.yml
conda activate insar-env

4. Project Structure

Place your ISCE2 processed project in:

work/PROJECT_NAME/ISCE/


Example:

work/tehran_s1_test/ISCE/


The ISCE directory must contain interferograms and geometry files required by MintPy.

5. Run Full Processing
chmod +x run_all.sh
./run_all.sh


This script will execute:

MintPy smallbaselineApp workflow

Network inversion

Topographic correction

Velocity estimation

Vertical displacement conversion

Figure/table generation

6. Outputs

Main outputs are generated inside:

work/PROJECT_NAME/ISCE/


Including:

velocity.h5

velocity_vertical.h5

temporalCoherence.h5

timeseries.h5

Generated figures and tables:

outputs/paper_figs/
outputs/paper_tables/

7. Notes

SNAP is not used in this workflow.

Raw Sentinel-1 SLC files are NOT included in this repository.

User must prepare ISCE2 project before running MintPy
