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
    p = argparse.ArgumentParser(description="Visualize LOS displacement map (mm)")
    p.add_argument("--isce-dir", default=".", help="Path to ISCE project directory.")
    p.add_argument("--los-path", required=True, help="Path to LOS displacement GeoTIFF.")
    p.add_argument(
        "--percentiles",
        default="5,95",
        help="Percentiles for color scale, e.g., 5,95",
    )
    return p.parse_args()


def main():
    args = parse_args()

    # FIXED: use args.isce_dir (underscore), not args.isce-dir
    isce_dir = os.path.abspath(args.isce_dir)
    los_path = args.los_path
    if not os.path.isabs(los_path):
        los_path = os.path.join(isce_dir, los_path)

    print("LOS displacement file:", los_path)

    data = read_gdal_array(los_path)
    if data.ndim == 3:
        data = data[0]

    finite = np.isfinite(data)
    if not finite.any():
        raise RuntimeError("No valid (non-NaN) values in dataset.")

    p_lo, p_hi = [float(p) for p in args.percentiles.split(",")]
    vmin = np.percentile(data[finite], p_lo)
    vmax = np.percentile(data[finite], p_hi)
    print(f"Color scale vmin/vmax (P{p_lo}/P{p_hi}): {vmin} {vmax}")

    plt.figure(figsize=(6, 6))
    im = plt.imshow(data, cmap="jet", vmin=vmin, vmax=vmax)
    plt.colorbar(im, label="LOS displacement (mm)")
    plt.title("LOS displacement (mm)")
    plt.xlabel("Pixel index (range direction)")
    plt.ylabel("Pixel index (azimuth direction)")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
