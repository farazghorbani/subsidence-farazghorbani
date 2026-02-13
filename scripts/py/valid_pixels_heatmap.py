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
        description="Heatmap of valid pixels (non-NaN) from vertical displacement"
    )
    p.add_argument("--isce-dir", default=".")
    p.add_argument("--vert-path", required=True,
                   help="Vertical displacement GeoTIFF (mm)")
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

    valid = np.isfinite(data).astype(float)  # 1 for valid, 0 for invalid

    plt.figure(figsize=(6, 6))
    im = plt.imshow(valid, cmap="Greys")
    plt.colorbar(im, label="Valid mask (1=valid, 0=invalid)")
    plt.title("Valid pixels mask (vertical displacement)")
    plt.xlabel("Pixel index (range)")
    plt.ylabel("Pixel index (azimuth)")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
