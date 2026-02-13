#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analyze_vertical_roi.py

Compute basic statistics of vertical displacement (mm)
for the whole image and for a user-defined ROI.

ROI format: x1,x2,y1,y2  (pixel indices; x=range, y=azimuth)
"""

import os
import argparse
import numpy as np
from osgeo import gdal


def read_gdal_array(path):
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Cannot open file: {path}")
    arr = ds.ReadAsArray()
    ds = None
    return arr


def stats(arr, name=""):
    finite = np.isfinite(arr)
    if not finite.any():
        print(f"{name}: all values are NaN.")
        return
    vals = arr[finite]
    print(f"{name} min / mean / max : {vals.min():.3f}  {vals.mean():.3f}  {vals.max():.3f}")
    p5, p50, p95 = np.percentile(vals, [5, 50, 95])
    print(f"{name} P5 / P50 / P95     : {p5:.3f}  {p50:.3f}  {p95:.3f}")
    print(f"{name} valid pixels       : {vals.size}")


def parse_roi(roi_str):
    parts = [int(p) for p in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError("ROI must be x1,x2,y1,y2")
    x1, x2, y1, y2 = parts
    return x1, x2, y1, y2


def parse_args():
    p = argparse.ArgumentParser(
        description="Analyze vertical displacement (mm) over a ROI."
    )
    p.add_argument("--isce-dir", default=".", help="Path to ISCE project directory.")
    p.add_argument("--vert-path", required=True,
                   help="Path to vertical displacement GeoTIFF (mm).")
    p.add_argument("--roi", required=True,
                   help="ROI in pixel coordinates: x1,x2,y1,y2")
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    vert_path = args.vert_path
    if not os.path.isabs(vert_path):
        vert_path = os.path.join(isce_dir, vert_path)

    print("ISCE DIR:", isce_dir)
    print("Vertical displacement file:", vert_path)

    data = read_gdal_array(vert_path)
    if data.ndim == 3:
        data = data[0]

    ny, nx = data.shape
    print("Image size (ny, nx):", ny, nx)

    print("\n== Global vertical displacement stats (mm) ==")
    stats(data, "Global")

    x1, x2, y1, y2 = parse_roi(args.roi)
    print(f"\nROI (x1,x2,y1,y2) = ({x1},{x2},{y1},{y2})")

    # sanity clamp
    x1 = max(0, min(nx, x1))
    x2 = max(0, min(nx, x2))
    y1 = max(0, min(ny, y1))
    y2 = max(0, min(ny, y2))

    roi = data[y1:y2, x1:x2]
    print("ROI shape (ny, nx):", roi.shape)

    print("\n== ROI vertical displacement stats (mm) ==")
    stats(roi, "ROI")


if __name__ == "__main__":
    main()
