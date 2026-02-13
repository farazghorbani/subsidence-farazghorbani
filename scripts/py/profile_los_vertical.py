#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal


def read_gdal_array(path):
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Cannot open file: {path}")
    arr = ds.ReadAsArray()
    ds = None
    return arr


def parse_args():
    p = argparse.ArgumentParser(
        description="Default horizontal profile for LOS and vertical displacement"
    )
    p.add_argument("--isce-dir", default=".")
    p.add_argument("--los-path", required=True,
                   help="LOS displacement GeoTIFF (mm)")
    p.add_argument("--vert-path", required=True,
                   help="Vertical displacement GeoTIFF (mm)")
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)

    los_path = args.los_path
    if not os.path.isabs(los_path):
        los_path = os.path.join(isce_dir, los_path)

    vert_path = args.vert_path
    if not os.path.isabs(vert_path):
        vert_path = os.path.join(isce_dir, vert_path)

    los = read_gdal_array(los_path)
    if los.ndim == 3:
        los = los[0]

    vert = read_gdal_array(vert_path)
    if vert.ndim == 3:
        vert = vert[0]

    if los.shape != vert.shape:
        raise RuntimeError(f"Shape mismatch: LOS {los.shape} vs vertical {vert.shape}")

    ny, nx = los.shape
    print("Image size (ny, nx):", ny, nx)

    # Use mid-row of valid pixels
    finite = np.isfinite(vert)
    ys, xs = np.where(finite)
    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()
    y_mid = (y_min + y_max) // 2

    print(f"Using horizontal profile at row y={y_mid}")
    print(f"x-range from {x_min} to {x_max}")

    los_prof = los[y_mid, x_min:x_max+1]
    vert_prof = vert[y_mid, x_min:x_max+1]
    x_idx = np.arange(x_min, x_max+1)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x_idx, los_prof, label="LOS displacement (mm)", alpha=0.7)
    ax.plot(x_idx, vert_prof, label="Vertical displacement (mm)", alpha=0.7)
    ax.set_xlabel("Pixel index (range)")
    ax.set_ylabel("Displacement (mm)")
    ax.set_title(f"LOS and vertical displacement profile (row y={y_mid})")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
