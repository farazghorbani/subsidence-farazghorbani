Reproducible Multi-Temporal InSAR Workflow for Land Subsidence Monitoring


ISCE2 + MintPy Processing Chain

1. Scientific Purpose of This Repository


This repository provides a fully reproducible, research-grade InSAR processing framework for land subsidence monitoring using Sentinel-1 SLC data.


The objective of this workflow is to establish a transparent and academically rigorous processing chain that enables:

    Interferometric processing from raw Sentinel-1 SAFE files

    Multi-temporal InSAR time-series inversion (SBAS method)

    Estimation of Line-of-Sight (LOS) deformation velocity

    Conversion to vertical subsidence

    Quantification of uncertainty


This repository is designed to support reproducible scientific research in geodetic deformation monitoring and urban subsidence studies.


No SNAP-based processing is used in this project.

All interferometric steps are performed using ISCE2 and MintPy.

2. Methodological Framework


The workflow follows the standard scientific structure of multi-temporal InSAR processing:

    Sentinel-1 SLC coregistration (TOPS mode)

    Interferogram generation

    Topographic phase removal

    Phase unwrapping

    Network construction using Small Baseline Subset (SBAS)

    Weighted least squares inversion

    DEM error correction

    Velocity estimation

    Uncertainty assessment


The processing philosophy emphasizes:

    Physical consistency

    Mathematical transparency

    Computational reproducibility

    Open-source implementation

3. Software Architecture


The processing chain integrates:


ISCE2

Used for interferometric SAR processing, including:

    SLC preparation

    Coregistration

    Interferogram generation

    Geometry computation


MintPy

Used for:

    Time-series inversion (SBAS)

    Temporal coherence estimation

    DEM error correction

    Velocity estimation

    Residual analysis


All post-processing scripts are written in Python.

4. Input Data Requirements


Required input data:

    Sentinel-1 IW SLC SAFE files

    Same relative orbit

    Same track (Ascending or Descending)

    Same subswath configuration


Data structure expected:


work/PROJECT_NAME/SLC/


Only SLC SAFE format is supported in this simplified academic workflow.

5. Computational Requirements


Recommended minimum:

    Linux operating system

    16–32 GB RAM

    Multi-core CPU

    Conda environment management


Large stacks may require increased memory resources.

6. Environment Installation


ISCE2 Environment


conda create -n isce2-env python=3.9

conda activate isce2-env

conda install -c conda-forge isce2


Verify:


python -c “import isce”

MintPy Environment


conda create -n mintpy-env python=3.9

conda activate mintpy-env

conda install -c conda-forge mintpy


Verify:


smallbaselineApp.py -h

7. Execution Procedure


Run from repository root:


bash run_all.sh /path/to/work PROJECT_NAME


Example:


bash run_all.sh /mnt/data/insar_chain tehran_project

8. Processing Stages Performed Automatically


The script executes:


ISCE2 Stage:

    TOPS coregistration

    Interferogram formation

    Geometry preparation


MintPy Stage:

    load_data

    modify_network

    reference_point

    invert_network

    correct_topography

    residual_RMS

    velocity

9. Outputs


Primary scientific outputs:


timeseries.h5

velocity.h5

velocityStd.h5

temporalCoherence.h5


Derived products:

    Vertical deformation map

    Velocity uncertainty map

    ROI deformation statistics

    Publication-ready figures


All outputs are reproducible.

10. Scientific Assumptions

    Dominant vertical deformation assumption for LOS-to-vertical conversion

    Single track geometry

    SBAS network configuration

    Temporal coherence thresholding


These assumptions are explicitly stated to ensure methodological clarity.

11. Reproducibility Statement


This repository is structured to allow:

    Independent execution

    Transparent parameter control

    Replication of scientific results

    Academic auditing of processing steps


All configuration parameters are explicitly defined in:


configs/smallbaselineApp.cfg
