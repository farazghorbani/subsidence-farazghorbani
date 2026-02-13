#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.pyplot as plt
import contextily as cx


def parse_args():
    p = argparse.ArgumentParser(
        description="Overlay vertical displacement (mm) on web basemap"
    )
    p.add_argument(
        "--isce-dir",
        default=".",
        help="Path to ISCE project directory.",
    )
    p.add_argument(
        "--vert-path",
        required=True,
        help="Vertical displacement GeoTIFF (mm, geocoded)",
    )
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    vert_path = args.vert_path
    if not os.path.isabs(vert_path):
        vert_path = os.path.join(isce_dir, vert_path)

    print("Vertical file:", vert_path)

    # --- read vertical displacement ---
    with rasterio.open(vert_path) as src:
        data = src.read(1)
        src_crs = src.crs
        src_transform = src.transform
        src_bounds = src.bounds
        src_width = src.width
        src_height = src.height

    if src_crs is None:
        raise RuntimeError("Input raster has no CRS. Cannot overlay on basemap.")

    # --- reproject to Web Mercator (EPSG:3857) ---
    dst_crs = "EPSG:3857"
    transform, width, height = calculate_default_transform(
        src_crs, dst_crs, src_width, src_height, *src_bounds
    )

    dst_data = np.empty((height, width), dtype=np.float32)
    reproject(
        source=data,
        destination=dst_data,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear,
    )

    # --- محاسبه vmin/vmax فقط روی پیکسل‌های معتبر ---
    valid = np.isfinite(dst_data)
    if not valid.any():
        raise RuntimeError("No valid values after reprojection.")

    vals = dst_data[valid]
    vmin = np.percentile(vals, 5)
    vmax = np.percentile(vals, 95)

    # حالا برای plot یک MaskedArray درست می‌کنیم
    mask = ~valid
    dst_masked = np.ma.array(dst_data, mask=mask)

    # --- plot روی basemap ---
    fig, ax = plt.subplots(figsize=(8, 8))

    extent = rasterio.transform.array_bounds(height, width, transform)

    img = ax.imshow(
        dst_masked,
        extent=extent,
        cmap="jet",
        vmin=vmin,
        vmax=vmax,
        alpha=0.7,
        origin="upper",
    )

    cx.add_basemap(ax, crs=dst_crs, source=cx.providers.Stamen.TonerLite)

    ax.set_title("Vertical displacement (mm) over basemap")
    fig.colorbar(img, ax=ax, label="Vertical displacement (mm)")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
