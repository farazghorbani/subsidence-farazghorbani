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


def parse_roi(roi_str):
    parts = [int(p) for p in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError("ROI must be x1,x2,y1,y2")
    return parts  # x1,x2,y1,y2


def parse_args():
    p = argparse.ArgumentParser(
        description="Histogram + boxplot of vertical displacement in ROI"
    )
    p.add_argument("--isce-dir", default=".")
    p.add_argument("--vert-path", required=True,
                   help="Vertical displacement GeoTIFF (mm)")
    p.add_argument("--roi", required=True,
                   help="ROI as x1,x2,y1,y2 in pixel coordinates")
    p.add_argument("--bins", type=int, default=40)
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    vert_path = args.vert_path
    if not os.path.isabs(vert_path):
        vert_path = os.path.join(isce_dir, vert_path)

    print("Vertical file:", vert_path)
    data = read_gdal_array(vert_path)
    if data.ndim == 3:
        data = data[0]

    ny, nx = data.shape
    print("Image size (ny, nx):", ny, nx)

    x1, x2, y1, y2 = parse_roi(args.roi)
    x1, x2 = max(0, x1), min(nx, x2)
    y1, y2 = max(0, y1), min(ny, y2)
    roi = data[y1:y2, x1:x2]

    finite = np.isfinite(roi)
    vals = roi[finite]
    if vals.size == 0:
        raise RuntimeError("No valid values in ROI.")

    print("ROI valid pixels:", vals.size)
    print("ROI min / mean / max (mm):", vals.min(), vals.mean(), vals.max())

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].hist(vals, bins=args.bins)
    axes[0].set_xlabel("Vertical displacement (mm)")
    axes[0].set_ylabel("Pixel count")
    axes[0].set_title("ROI histogram")

    axes[1].boxplot(vals, vert=True, showfliers=True)
    axes[1].set_ylabel("Vertical displacement (mm)")
    axes[1].set_title("ROI boxplot")

    fig.suptitle(f"Vertical displacement in ROI x[{x1},{x2}), y[{y1},{y2})")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
