#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
visualize_los.py

نمایش نقشه جابجایی از GeoTIFF (LOS یا vertical)
و تنظیم خودکار عنوان و برچسب colorbar بر اساس نام فایل:

اگر نام فایل شامل "vertical" باشد → Vertical displacement (mm)
در غیر این صورت → LOS displacement (mm)
"""

import os
import argparse
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt


def read_gdal_array(path):
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Cannot open {path}")
    arr = ds.ReadAsArray()
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    ds = None
    return arr, gt, proj


def parse_args():
    p = argparse.ArgumentParser(
        description="نمایش نقشه جابجایی (LOS یا vertical) از GeoTIFF"
    )
    p.add_argument(
        "--isce-dir",
        default=".",
        help="مسیر فولدر ISCE (فولدری که merged داخل آن است).",
    )
    p.add_argument(
        "--los-path",
        required=True,
        help="مسیر فایل GeoTIFF جابجایی (mm)؛ مثلاً merged/los_displacement_clean.tif "
             "یا merged/vertical_displacement_mm.tif",
    )
    p.add_argument(
        "--percentiles",
        default="5,95",
        help="پرسنتایل برای تعیین min/max رنگ، مثلاً 5,95",
    )
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    los_path = args.los_path
    if not os.path.isabs(los_path):
        los_path = os.path.join(isce_dir, los_path)

    print("ISCE DIR:", isce_dir)
    print("LOS file:", los_path)

    data, gt, proj = read_gdal_array(los_path)
    if data.ndim == 3:
        data = data[0]

    ny, nx = data.shape
    print("اندازه تصویر:", (ny, nx))

    # تعیین نوع داده از روی نام فایل
    fname = os.path.basename(los_path).lower()
    if "vertical" in fname:
        title = "Vertical displacement (mm)"
        cbar_label = "Vertical displacement (mm)"
    else:
        title = "LOS displacement (mm)"
        cbar_label = "LOS displacement (mm)"

    # تعیین بازه رنگ بر اساس percentiles
    p_lo, p_hi = [float(p) for p in args.percentiles.split(",")]
    finite = np.isfinite(data)
    if not finite.any():
        raise RuntimeError("هیچ مقدار معتبری (غیر NaN) در داده وجود ندارد.")

    vmin = np.percentile(data[finite], p_lo)
    vmax = np.percentile(data[finite], p_hi)
    print(f"Color scale vmin/vmax based on P{p_lo}/P{p_hi}: {vmin} {vmax}")

    plt.figure(figsize=(6, 6))
    im = plt.imshow(data, cmap="jet", vmin=vmin, vmax=vmax)
    plt.colorbar(im, label=cbar_label)
    plt.title(title)
    plt.xlabel("Pixel (range)")
    plt.ylabel("Pixel (azimuth)")
    plt.gca().invert_yaxis()  # برای اینکه مثل تصویر راداری نمایش داده شود
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
