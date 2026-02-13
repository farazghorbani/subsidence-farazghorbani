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
        description="Scatter plot: coherence vs vertical displacement (mm)"
    )
    p.add_argument("--isce-dir", default=".")
    p.add_argument("--vert-path", required=True,
                   help="Vertical displacement GeoTIFF (mm)")
    p.add_argument("--coh-path", required=True,
                   help="Geocoded coherence VRT (e.g. topophase.cor.geo.vrt)")
    p.add_argument("--sample", type=int, default=5000,
                   help="Max number of random samples to plot")
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)

    vert_path = args.vert_path
    if not os.path.isabs(vert_path):
        vert_path = os.path.join(isce_dir, vert_path)

    coh_path = args.coh_path
    if not os.path.isabs(coh_path):
        coh_path = os.path.join(isce_dir, coh_path)

    vert = read_gdal_array(vert_path)
    if vert.ndim == 3:
        vert = vert[0]

    coh_raw = read_gdal_array(coh_path)
    # ISCE coherence is often stored with scale *1000
    if coh_raw.ndim == 3:
        coh_raw = coh_raw[0]
    coh = coh_raw.astype("float32")
    if coh.max() > 2.0:
        coh /= 1000.0

    if vert.shape != coh.shape:
        raise RuntimeError(f"Shape mismatch: vert {vert.shape} vs coh {coh.shape}")

    finite = np.isfinite(vert) & np.isfinite(coh)
    v = vert[finite].ravel()
    c = coh[finite].ravel()

    n = v.size
    print("Total valid samples:", n)

    if n == 0:
        raise RuntimeError("No valid overlapping pixels.")

    # random subsample for plotting
    if n > args.sample:
        idx = np.random.choice(n, size=args.sample, replace=False)
        v = v[idx]
        c = c[idx]

    plt.figure(figsize=(6, 5))
    plt.scatter(c, v, s=5, alpha=0.4)
    plt.xlabel("Coherence")
    plt.ylabel("Vertical displacement (mm)")
    plt.title("Coherence vs. vertical displacement")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
