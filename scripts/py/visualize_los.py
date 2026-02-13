#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
نمایش نقشه جابجایی LOS (میلی‌متر) تولید شده از ISCE:

- خواندن GeoTIFF (مثلاً merged/los_displacement_mm.tif)
- محاسبه درصدی (percentile) برای تعیین محدوده رنگ
- نمایش نقشه با matplotlib
- امکان نمایش یک ROI مشخص (اختیاری)
- امکان ذخیره شکل به صورت PNG
"""

import os
import argparse
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt


def read_gdal_array(path):
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Cannot open {path}")
    arr = ds.ReadAsArray()
    # اگر چندباندی بود، باند اول
    if arr.ndim == 3:
        arr = arr[0]
    return arr


def parse_roi(roi_str):
    if roi_str is None:
        return None
    parts = [int(p) for p in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError("فرمت ROI باید x1,x2,y1,y2 باشد.")
    return tuple(parts)


def parse_args():
    parser = argparse.ArgumentParser(
        description="نمایش نقشه LOS displacement (mm) از GeoTIFF."
    )
    parser.add_argument(
        "--isce-dir",
        default=os.path.expanduser("~/insar_chain/projects/tehran_s1_test/ISCE"),
        help="مسیر فولدر ISCE (جایی که merged داخل آن است).",
    )
    parser.add_argument(
        "--los-path",
        default=None,
        help="مسیر فایل LOS (mm). اگر ندهید، پیش‌فرض merged/los_displacement_mm.tif است.",
    )
    parser.add_argument(
        "--roi",
        default=None,
        help="ROI پیکسلی برای زوم: x1,x2,y1,y2 (اختیاری).",
    )
    parser.add_argument(
        "--savefig",
        default=None,
        help="نام فایل خروجی برای ذخیره شکل (مثلاً results/los_map.png). اگر خالی باشد، فقط نمایش روی صفحه.",
    )
    parser.add_argument(
        "--percentiles",
        default="5,95",
        help="درصدهای پایین/بالا برای تعیین محدوده رنگ، پیش‌فرض 5,95.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    merged_dir = os.path.join(isce_dir, "merged")

    los_path = (
        args.los_path
        if args.los_path is not None
        else os.path.join(merged_dir, "los_displacement_mm.tif")
    )

    roi = parse_roi(args.roi) if args.roi is not None else None
    p_lo, p_hi = [float(p) for p in args.percentiles.split(",")]

    print("ISCE DIR:", isce_dir)
    print("LOS file:", los_path)

    # خواندن داده
    los = read_gdal_array(los_path).astype("float32")
    print("اندازه تصویر:", los.shape)

    # اعمال ROI اگر داده شده
    if roi is not None:
        x1, x2, y1, y2 = roi
        los_plot = los[y1:y2, x1:x2]
        print("ROI:", roi, " -> شکل زیرمجموعه:", los_plot.shape)
    else:
        los_plot = los

    # نادیده گرفتن NaNها
    finite = np.isfinite(los_plot)
    if not finite.any():
        raise RuntimeError("هیچ مقدار معتبری (غیر NaN) در داده وجود ندارد.")

    # محاسبه محدوده رنگ بر اساس percentiles
    vmin = float(np.nanpercentile(los_plot[finite], p_lo))
    vmax = float(np.nanpercentile(los_plot[finite], p_hi))
    print(f"Color scale vmin/vmax based on P{p_lo}/P{p_hi}:", vmin, vmax)

    # رسم
    plt.figure(figsize=(8, 6))
    im = plt.imshow(los_plot, cmap="jet", vmin=vmin, vmax=vmax)
    plt.colorbar(im, label="LOS displacement (mm)")
    plt.title("LOS displacement (mm)")
    plt.xlabel("Pixel (range)")
    plt.ylabel("Pixel (azimuth)")

    plt.tight_layout()

    # ذخیره یا نمایش
    if args.savefig is not None:
        out_fig = args.savefig
        if not os.path.isabs(out_fig):
            # اگر نسبی باشد، در خود ISCE ذخیره می‌کنیم
            out_fig = os.path.join(isce_dir, out_fig)
        os.makedirs(os.path.dirname(out_fig), exist_ok=True)
        plt.savefig(out_fig, dpi=300)
        print("شکل ذخیره شد در:", out_fig)

    plt.show()


if __name__ == "__main__":
    main()
