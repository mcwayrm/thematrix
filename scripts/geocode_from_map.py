#!/usr/bin/env python3
"""
Script 1: Geocode factory markers from Bloomberg ESG Nature map PNGs.

Usage:
    python3 geocode_from_map.py <image.png> [--output output.csv] [--calibrate]

Detects blue factory markers in Bloomberg ESG Nature / Heatmap Explorer
screenshots, converts pixel positions to estimated lat/lon coordinates,
and outputs a geocoded CSV.

Calibration:
    The default projection parameters are fitted for standard Bloomberg ESG
    Nature full-world map screenshots. If your map is zoomed or cropped
    differently, use --calibrate to interactively set reference points,
    or edit MAP_CALIBRATION below.
"""

import argparse
import csv
import sys
import numpy as np
from PIL import Image
from scipy.ndimage import label

# ---------------------------------------------------------------------------
# MAP CALIBRATION (equirectangular fit for standard Bloomberg ESG world map)
#   pixel_x = LON_SCALE * longitude + LON_OFFSET
#   pixel_y = LAT_SCALE * latitude  + LAT_OFFSET
#
# Derived from known Ford factory locations on a 1072x884 Bloomberg screenshot.
# Adjust these if your map has different zoom/crop.
# ---------------------------------------------------------------------------
LON_SCALE  =  2.9791
LON_OFFSET =  533.75
LAT_SCALE  = -1.9213
LAT_OFFSET =  494.79

# Marker detection parameters
BLUE_MIN = (0, 0, 180)       # Min (R, G, B) for marker color
BLUE_MAX = (100, 100, 255)   # Max (R, G, B) for marker color
MIN_MARKER_PX = 5            # Minimum pixels to count as a marker
HEADER_PX = 50               # Rows to skip at top (Bloomberg UI header)
FOOTER_PX = 80               # Rows to skip at bottom


def detect_markers(image_path):
    """Detect blue markers in a Bloomberg ESG map PNG."""
    img = Image.open(image_path)
    px = np.array(img)

    h, w = px.shape[:2]
    r, g, b = px[:, :, 0], px[:, :, 1], px[:, :, 2]

    # Color threshold for blue markers
    mask = (
        (r >= BLUE_MIN[0]) & (r <= BLUE_MAX[0]) &
        (g >= BLUE_MIN[1]) & (g <= BLUE_MAX[1]) &
        (b >= BLUE_MIN[2]) & (b <= BLUE_MAX[2])
    )

    # Exclude header/footer UI regions
    mask[:HEADER_PX, :] = False
    mask[h - FOOTER_PX:, :] = False

    # Find connected components
    labeled_array, n_features = label(mask)

    markers = []
    for i in range(1, n_features + 1):
        ys, xs = np.where(labeled_array == i)
        if len(ys) >= MIN_MARKER_PX:
            markers.append({
                "pixel_x": float(np.mean(xs)),
                "pixel_y": float(np.mean(ys)),
                "pixel_size": len(ys),
            })

    markers.sort(key=lambda m: (m["pixel_y"], m["pixel_x"]))
    return markers, (w, h)


def pixel_to_latlon(px_x, px_y):
    """Convert pixel coordinates to lat/lon using calibration parameters."""
    lon = (px_x - LON_OFFSET) / LON_SCALE
    lat = (px_y - LAT_OFFSET) / LAT_SCALE
    return round(lat, 4), round(lon, 4)


def run_calibration(image_path):
    """Interactive calibration: user provides known reference points."""
    markers, (w, h) = detect_markers(image_path)
    print(f"Detected {len(markers)} markers in {image_path}")
    print(f"Image size: {w} x {h}\n")

    print("Enter 3+ reference points (known locations visible on the map).")
    print("For each, provide: pixel_x, pixel_y, latitude, longitude")
    print("(Enter blank line when done)\n")

    refs = []
    while True:
        line = input("  px_x, px_y, lat, lon: ").strip()
        if not line:
            break
        parts = [float(x.strip()) for x in line.split(",")]
        if len(parts) == 4:
            refs.append(parts)
        else:
            print("  Need 4 values: px_x, px_y, lat, lon")

    if len(refs) < 2:
        print("Need at least 2 reference points.")
        return

    pxs = np.array([r[0] for r in refs])
    pys = np.array([r[1] for r in refs])
    lons = np.array([r[3] for r in refs])
    lats = np.array([r[2] for r in refs])

    # Least-squares fit
    A_x = np.column_stack([lons, np.ones_like(lons)])
    (a_lon, b_lon), *_ = np.linalg.lstsq(A_x, pxs, rcond=None)
    A_y = np.column_stack([lats, np.ones_like(lats)])
    (a_lat, b_lat), *_ = np.linalg.lstsq(A_y, pys, rcond=None)

    print(f"\n# Updated calibration (paste into script):")
    print(f"LON_SCALE  = {a_lon:.4f}")
    print(f"LON_OFFSET = {b_lon:.2f}")
    print(f"LAT_SCALE  = {a_lat:.4f}")
    print(f"LAT_OFFSET = {b_lat:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Geocode factory markers from Bloomberg ESG Nature map PNGs"
    )
    parser.add_argument("image", help="Path to Bloomberg ESG Nature map PNG")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output CSV path (default: <image>_geocoded.csv)"
    )
    parser.add_argument(
        "--calibrate", action="store_true",
        help="Run interactive calibration mode"
    )
    args = parser.parse_args()

    if args.calibrate:
        run_calibration(args.image)
        return

    # Detect and geocode
    markers, (w, h) = detect_markers(args.image)
    print(f"Detected {len(markers)} markers in {args.image} ({w}x{h})")

    for m in markers:
        lat, lon = pixel_to_latlon(m["pixel_x"], m["pixel_y"])
        m["est_latitude"] = lat
        m["est_longitude"] = lon

    # Output
    out_path = args.output or args.image.replace(".png", "_geocoded.csv").replace(".PNG", "_geocoded.csv")
    fields = ["marker_id", "pixel_x", "pixel_y", "pixel_size",
              "est_latitude", "est_longitude"]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, m in enumerate(markers, 1):
            writer.writerow({
                "marker_id": i,
                "pixel_x": round(m["pixel_x"], 1),
                "pixel_y": round(m["pixel_y"], 1),
                "pixel_size": m["pixel_size"],
                "est_latitude": m["est_latitude"],
                "est_longitude": m["est_longitude"],
            })

    print(f"Saved {len(markers)} markers to {out_path}")

    # Print summary
    print(f"\n{'#':>3} {'px_x':>7} {'px_y':>7} {'lat':>8} {'lon':>9} {'size':>5}")
    print("-" * 42)
    for i, m in enumerate(markers, 1):
        print(f"{i:3d} {m['pixel_x']:7.1f} {m['pixel_y']:7.1f} "
              f"{m['est_latitude']:8.1f} {m['est_longitude']:9.1f} "
              f"{m['pixel_size']:5d}")


if __name__ == "__main__":
    main()
