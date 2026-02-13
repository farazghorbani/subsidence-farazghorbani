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
    p = argparse.ArgumentParser(description="Histogram of vertical displacement (mm)")
    p.add_argument("--isce-dir", default=".", help="Path to ISCE project directory.")
    p.add_argument(
        "--vert-path",
        required=True,
        help="Path to vertical displacement GeoTIFF (mm).",
    )
    p.add_argument(
        "--bins",
        type=int,
        default=50,
        help="Number of histogram bins (default: 50).",
    )
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    vert_path = args.vert_path
    if not os.path.isabs(vert_path):
        vert_path = os.path.join(isce_dir, vert_path)

    print("Vertical displacement file:", vert_path)

    data = read_gdal_array(vert_path)
    if data.ndim == 3:
        data = data[0]

    finite = np.isfinite(data)
    if not finite.any():
        raise RuntimeError("No valid (non-NaN) values in dataset.")

    vals = data[finite]

    print("Number of valid pixels:", vals.size)
    print("Min / Mean / Max (mm):", vals.min(), vals.mean(), vals.max())

    plt.figure(figsize=(6, 4))
    plt.hist(vals, bins=args.bins)
    plt.xlabel("Vertical displacement (mm)")
    plt.ylabel("Pixel count")
    plt.title("Histogram of vertical displacement (mm)")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
