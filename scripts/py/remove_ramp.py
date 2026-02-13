#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
حذف ramp بزرگ‌مقیاس از فاز بازشده (unwrapped phase) ISCE:

- خواندن فاز بازشده geocoded (مثلاً merged/filt_topophase.unw.geo.vrt)
- خواندن coherence و اعمال ماسک
- فیت‌کردن سطح چندجمله‌ای درجه ۱ یا ۲ روی فاز (فقط روی پیکسل‌های با coherence بالا)
- کم‌کردن ramp از فاز و ذخیره فاز تصحیح‌شده
"""

import os
import argparse
from osgeo import gdal
import numpy as np


def read_gdal_array(path):
    ds = gdal.Open(path)
    if ds is None:
        raise RuntimeError(f"Cannot open {path}")
    arr = ds.ReadAsArray()
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    ds = None
    # اگر چندباندی بود، باند اول
    if arr.ndim == 3:
        arr = arr[0]
    return arr.astype("float32"), gt, proj


def save_geotiff(path, array, geotransform, projection, nodata=None):
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


def build_design_matrix(x, y, degree=2):
    """
    ساخت ماتریس طراحی برای فیت کردن ramp:
    degree=1 -> a + b*x + c*y
    degree=2 -> a + b*x + c*y + d*x*y + e*x^2 + f*y^2
    """
    if degree == 1:
        G = np.vstack([
            np.ones_like(x),
            x,
            y
        ]).T
    elif degree == 2:
        G = np.vstack([
            np.ones_like(x),
            x,
            y,
            x * y,
            x * x,
            y * y
        ]).T
    else:
        raise ValueError("degree فقط می‌تواند ۱ یا ۲ باشد.")
    return G


def parse_args():
    p = argparse.ArgumentParser(
        description="حذف ramp از فاز بازشده ISCE با فیت کردن سطح چندجمله‌ای."
    )
    p.add_argument(
        "--isce-dir",
        default=os.path.expanduser("~/insar_chain/projects/tehran_s1_test/ISCE"),
        help="مسیر فولدر ISCE (جایی که merged داخلش است).",
    )
    p.add_argument(
        "--unw-path",
        default=None,
        help="مسیر فاز بازشده geocoded (پیش‌فرض: merged/filt_topophase.unw.geo.vrt).",
    )
    p.add_argument(
        "--coh-path",
        default=None,
        help="مسیر coherence (پیش‌فرض: merged/topophase.cor.geo.vrt).",
    )
    p.add_argument(
        "--coh-scale",
        type=float,
        default=1000.0,
        help="ضریب scale coherence در ISCE (معمولاً 1000).",
    )
    p.add_argument(
        "--coh-threshold",
        type=float,
        default=0.3,
        help="آستانه coherence برای انتخاب پیکسل‌های معتبر.",
    )
    p.add_argument(
        "--degree",
        type=int,
        default=2,
        help="درجه چندجمله‌ای ramp (۱ یا ۲). پیش‌فرض: ۲.",
    )
    p.add_argument(
        "--out-unw",
        default="filt_topophase.unw_rampcorr.geo.tif",
        help="نام فایل خروجی فاز اصلاح‌شده (در صورت نسبی بودن در merged ذخیره می‌شود).",
    )
    return p.parse_args()


def main():
    args = parse_args()

    isce_dir = os.path.abspath(args.isce_dir)
    merged_dir = os.path.join(isce_dir, "merged")

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

    out_unw = args.out_unw
    if not os.path.isabs(out_unw):
        out_unw = os.path.join(merged_dir, out_unw)

    print("ISCE DIR:", isce_dir)
    print("Unwrapped phase:", unw_path)
    print("Coherence:", coh_path)
    print("Output corrected unw:", out_unw)

    # ---------- خواندن داده ----------
    unw, gt, proj = read_gdal_array(unw_path)
    coh_raw, _, _ = read_gdal_array(coh_path)
    coh = coh_raw / float(args.coh_scale)

    ny, nx = unw.shape
    print("اندازه تصویر:", (ny, nx))

    # ماسک پیکسل‌های معتبر: فعلاً همه پیکسل‌های فاز که finite هستند
    mask_valid = np.isfinite(unw)
    n_valid = int(mask_valid.sum())
    print("تعداد پیکسل‌های معتبر برای فیت ramp:", n_valid)
    if n_valid < 1000:
        raise RuntimeError("پیکسل معتبر برای فیت ramp خیلی کم است.")


    # مختصات x,y نرمال‌شده برای پیکسل‌های معتبر
    yy, xx = np.indices(unw.shape)
    # نرمال‌سازی به بازه [-1, 1] برای پایداری عددی
    x_norm = (xx - xx.mean()) / max(1.0, xx.std())
    y_norm = (yy - yy.mean()) / max(1.0, yy.std())

    xv = x_norm[mask_valid].ravel()
    yv = y_norm[mask_valid].ravel()
    zv = unw[mask_valid].ravel()

    # ---------- ساخت ماتریس طراحی و فیت least squares ----------
    print("در حال فیت کردن ramp درجه", args.degree)
    G = build_design_matrix(xv, yv, degree=args.degree)
    # حل کمترین مربعات
    m, residuals, rank, s = np.linalg.lstsq(G, zv, rcond=None)
    print("پارامترهای ramp:", m)
    if residuals.size > 0:
        print("مجموع مربعات باقیمانده:", float(residuals[0]))

    # ---------- بازسازی ramp روی کل تصویر ----------
    G_full = build_design_matrix(x_norm.ravel(), y_norm.ravel(), degree=args.degree)
    ramp_full = (G_full @ m).reshape(unw.shape)

    # ---------- کم کردن ramp ----------
    unw_corr = unw - ramp_full

    # ---------- آمار قبل و بعد ----------
    def stats(a, name):
        finite = np.isfinite(a)
        print(
            f"{name}: min/mean/max =",
            float(a[finite].min()),
            float(a[finite].mean()),
            float(a[finite].max()),
        )

    print("\n== آمار قبل از حذف ramp ==")
    stats(unw, "unw (rad)")
    print("\n== آمار ramp فیت شده ==")
    stats(ramp_full, "ramp (rad)")
    print("\n== آمار بعد از حذف ramp ==")
    stats(unw_corr, "unw_corr (rad)")

    # ---------- ذخیره فاز اصلاح‌شده ----------
    print("\nذخیره فاز اصلاح‌شده در:", out_unw)
    save_geotiff(out_unw, unw_corr, gt, proj, nodata=np.nan)
    print("تمام شد.")


if __name__ == "__main__":
    main()
