#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
postprocess_ifg.py

تحلیل یک اینترفروگرام ISCE:

- خواندن coherence و فاز بازشده (unwrapped phase)
- حذف فازهای غیرواقعی با برش (phase clipping)
- محاسبه جابجایی LOS بر حسب میلی‌متر
- حذف نواحی خارج از swath بر اساس coherence=0
- محاسبه آمار کلی و آمار ROI (اگر داده شود)
- ذخیره GeoTIFF جابجایی LOS (mm)

مثال اجرا:

python scripts/postprocess_ifg.py \
    --isce-dir . \
    --unw-path merged/filt_topophase.unw_rampcorr.geo.tif \
    --coh-threshold 0.0 \
    --phase-clip 50 \
    --out los_displacement_clean.tif
"""

import os
import argparse
import numpy as np
from osgeo import gdal


# --------------------- توابع کمکی ------------------------

def read_gdal_array(path):
    """خواندن یک raster با GDAL و برگرداندن (آرایه، GeoTransform، Projection)."""
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Cannot open {path}")
    arr = ds.ReadAsArray()
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    ds = None
    return arr, gt, proj


def save_geotiff(path, array, geotransform, projection, nodata=None):
    """ذخیره یک آرایه ۲بعدی به صورت GeoTIFF float32."""
    driver = gdal.GetDriverByName("GTiff")
    ny, nx = array.shape
    ds = driver.Create(path, nx, ny, 1, gdal.GDT_Float32)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projection)
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.WriteArray(array.astype("float32"))
    band.FlushCache()
    ds = None


def stats_from_array(arr, name=""):
    finite = np.isfinite(arr)
    if not finite.any():
        print(f"{name} : همه مقادیر NaN هستند!")
        return
    print(f"{name} min / mean / max :",
          float(arr[finite].min()),
          float(arr[finite].mean()),
          float(arr[finite].max()))


def parse_roi(roi_str):
    if roi_str is None:
        return None
    parts = [int(p) for p in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError("فرمت ROI باید x1,x2,y1,y2 باشد")
    return tuple(parts)


# --------------------- پارس آرگومان‌ها ---------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="محاسبه جابجایی LOS از خروجی ISCE (unw + coherence)"
    )
    p.add_argument(
        "--isce-dir",
        default=".",
        help="مسیر فولدر ISCE (فولدری که merged داخل آن است).",
    )
    p.add_argument(
        "--unw-path",
        default=None,
        help="مسیر فاز بازشده (geocoded). پیش‌فرض: merged/filt_topophase.unw.geo.vrt",
    )
    p.add_argument(
        "--coh-path",
        default=None,
        help="مسیر coherence. پیش‌فرض: merged/topophase.cor.geo.vrt",
    )
    p.add_argument(
        "--coh-scale",
        type=float,
        default=1000.0,
        help="ضریب scale در فایل coherence (معمولاً 1000).",
    )
    p.add_argument(
        "--coh-threshold",
        type=float,
        default=0.0,
        help="آستانه coherence برای ماسک کردن (بعد از حذف swath). "
             "اگر 0.0 باشد فقط swath mask اعمال می‌شود.",
    )
    p.add_argument(
        "--phase-clip",
        type=float,
        default=50.0,
        help="حداکثر قدرمطلق فاز (رادیان) برای محاسبه LOS؛ بزرگ‌ترها NaN می‌شوند.",
    )
    p.add_argument(
        "--roi",
        default=None,
        help="ROI به صورت x1,x2,y1,y2 در مختصات پیکسلی (اختیاری).",
    )
    p.add_argument(
        "--out",
        default="los_displacement_mm.tif",
        help="نام فایل خروجی LOS (mm) داخل فولدر merged.",
    )
    return p.parse_args()


# --------------------- بدنه اصلی ---------------------------

def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    merged_dir = os.path.join(isce_dir, "merged")

    # مسیرها
    unw_path = (
        args.unw_path
        if args.unw_path is not None
        else os.path.join(merged_dir, "filt_topophase.unw.geo.vrt")
    )
    coh_path = (
        args.coh_path
        if args.coh_path is not None
        else os.path.join(merged_dir, "topophase.cor.geo.vrt")
    )

    out_path = (
        os.path.join(merged_dir, args.out)
        if not os.path.isabs(args.out)
        else args.out
    )

    roi = parse_roi(args.roi) if args.roi is not None else None

    print("ISCE DIR :", isce_dir)
    print("Coherence:", coh_path)
    print("Unwrapped phase:", unw_path)
    print("Output LOS (mm):", out_path)
    if roi is not None:
        print("ROI (x1,x2,y1,y2):", roi)

    # طول موج Sentinel-1
    S1_WAVELENGTH = 0.055465  # متر

    # ---------- خواندن coherence ----------
    print("\n== خواندن coherence ==")
    coh_raw, gt_coh, proj_coh = read_gdal_array(coh_path)

    # اگر چندباندی بود -> باند اول
    if coh_raw.ndim == 3:
        coh_raw = coh_raw[0]

    coh = coh_raw.astype("float32") / float(args.coh_scale)
    print("اندازه تصویر coherence:", coh.shape)

    print("\n== آمار global coherence ==")
    stats_from_array(coh, "Global coherence")

    if roi is not None:
        x1, x2, y1, y2 = roi
        roi_coh = coh[y1:y2, x1:x2]
        print("\nROI shape:", roi_coh.shape)
        stats_from_array(roi_coh, "ROI coherence")

    # ---------- خواندن فاز ----------
    print("\n== خواندن فاز ==")
    unw_raw, gt_unw, proj_unw = read_gdal_array(unw_path)

    # اگر چندباندی بود → باند اول
    if unw_raw.ndim == 3:
        unw_raw = unw_raw[0]

    unw = unw_raw.astype("float32")
    ny, nx = unw.shape
    print("اندازه تصویر فاز:", (ny, nx))

    # ---------- برش فازهای غیرواقعی ----------
    phase_clip = float(args.phase_clip)
    print(f"\nبرش فاز با |phi| <= {phase_clip} rad")

    mask_good_phase = np.isfinite(unw) & (np.abs(unw) <= phase_clip)
    n_good_phase = int(mask_good_phase.sum())
    print("تعداد پیکسل با فاز معقول برای LOS:", n_good_phase)

    unw_clipped = np.where(mask_good_phase, unw, np.nan)

    print("\n== آمار فاز قبل از کلیپ ==")
    stats_from_array(unw, "UNW (rad)")
    print("\n== آمار فاز بعد از کلیپ ==")
    stats_from_array(unw_clipped, f"UNW clipped |phi|<={phase_clip}rad")

    # ---------- محاسبه LOS ----------
    print("\n== محاسبه LOS displacement (mm) از فاز کلیپ شده ==")
    los_m = unw_clipped * (S1_WAVELENGTH / (4.0 * np.pi))
    los_mm = los_m * 1000.0

    print("\n== آمار global LOS displacement (mm) (قبل از ماسک) ==")
    stats_from_array(los_mm, "Global LOS mm")

    # ---------- ماسک swath: حذف نواحی بیرون از پوشش ----------
    mask_swath = np.isfinite(coh) & (coh > 0.0)
    n_swath = int(mask_swath.sum())
    print("تعداد پیکسل داخل swath (coh>0):", n_swath)

    los_swath = np.where(mask_swath, los_mm, np.nan)

    # ---------- ماسک coherence (اختیاری) ----------
    coh_thr = float(args.coh_threshold)
    if coh_thr > 0.0:
        mask_coh = mask_swath & (coh >= coh_thr)
        n_mask = int(mask_coh.sum())
        print("تعداد پیکسل عبورکرده از آستانه coherence:", n_mask)

        if n_mask == 0:
            print("هشدار: هیچ پیکسل عبور از آستانه coherence پیدا نشد؛ "
                  "فقط ماسک swath اعمال می‌شود.")
            los_final = los_swath
        else:
            los_final = np.where(mask_coh, los_mm, np.nan)
    else:
        print("coh-threshold = 0.0 → فقط swath mask اعمال می‌شود.")
        los_final = los_swath

    print("\n== آمار LOS پس از ماسک‌های نهایی ==")
    stats_from_array(los_final, "LOS final mm")

    if roi is not None:
        x1, x2, y1, y2 = roi
        roi_los = los_final[y1:y2, x1:x2]
        print("\n== آمار ROI LOS (mm) ==")
        stats_from_array(roi_los, "ROI LOS mm")

    # ---------- ذخیره GeoTIFF ----------
    print("\n== ذخیره GeoTIFF جابجایی LOS (mm) در:")
    print(out_path)
    save_geotiff(out_path, los_final, gt_unw, proj_unw, nodata=np.nan)
    print("تمام شد.")


if __name__ == "__main__":
    main()
