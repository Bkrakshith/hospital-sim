#!/usr/bin/env python3
"""Render the saved SLAM map (maps/hospital_full.yaml) as a clean PNG for posting, optionally with the walked trail.

    python3 media/linkedin/render_map.py ros2_ws/src/hospital-sim-ros2/g1_navigation/maps/hospital_full.yaml out.png \
        [--trail datasets/slam_survey/<run>/trail_map.csv] [--title ...]
Colours: free = light, occupied = dark ink, unknown = background. Nothing is drawn into the map itself.
"""
import argparse
import os

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/ubuntu/Ubuntu-{}.ttf"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map_yaml")
    ap.add_argument("out")
    ap.add_argument("--trail", default="")
    ap.add_argument("--scale", type=int, default=2, help="output pixels per map cell")
    ap.add_argument("--title", default="Hospital ground floor + surgical wing: lidar SLAM map built by a simulated "
                                       "Unitree G1")
    ap.add_argument("--sub", default="NVIDIA Isaac Sim · Livox MID-360 2-D slice · slam_toolbox · 5 cm cells")
    a = ap.parse_args()
    y = yaml.safe_load(open(a.map_yaml))
    img = np.array(Image.open(os.path.join(os.path.dirname(a.map_yaml), y["image"])))
    res = float(y["resolution"])
    ox, oy = y["origin"][:2]
    h, w = img.shape
    # crop to the known area + margin
    known = img != 205
    rows, cols = np.nonzero(known)
    m = 30
    r0, r1 = max(0, rows.min() - m), min(h, rows.max() + m)
    c0, c1 = max(0, cols.min() - m), min(w, cols.max() + m)
    img = img[r0:r1, c0:c1]
    bg = np.array([16, 20, 28], np.uint8)
    rgb = np.empty(img.shape + (3,), np.uint8)
    rgb[:] = bg
    rgb[img > 250] = (232, 236, 242)
    rgb[img < 100] = (30, 120, 220)
    out = Image.fromarray(rgb).resize(((c1 - c0) * a.scale, (r1 - r0) * a.scale), Image.NEAREST)
    d = ImageDraw.Draw(out, "RGBA")
    if a.trail and os.path.exists(a.trail):
        pts = np.loadtxt(a.trail, delimiter=",", ndmin=2)[:, 1:3]
        # world -> image pixels (row 0 = top = max y)
        px = ((pts[:, 0] - ox) / res - c0) * a.scale
        py = ((h - 1 - (pts[:, 1] - oy) / res) - r0) * a.scale
        seg = [0] + [k for k in range(1, len(pts)) if np.hypot(*(pts[k] - pts[k - 1])) > 1.5] + [len(pts)]
        for s0, s1 in zip(seg[:-1], seg[1:]):  # no line across gaps in the trail log (runner restarts)
            if s1 - s0 > 1:
                d.line(list(zip(px[s0:s1], py[s0:s1])), fill=(255, 150, 30, 200), width=max(2, a.scale + 1))
        d.ellipse((px[0] - 9, py[0] - 9, px[0] + 9, py[0] + 9), fill=(60, 220, 100, 255))
    pad_top = 130
    canvas = Image.new("RGB", (out.width + 80, out.height + pad_top + 60), tuple(bg))
    canvas.paste(out, (40, pad_top))
    dc = ImageDraw.Draw(canvas)
    dc.text((40, 28), a.title, font=ImageFont.truetype(FONT.format("B"), 40), fill=(255, 255, 255))
    dc.text((40, 80), "SIMULATION  ·  " + a.sub, font=ImageFont.truetype(FONT.format("L"), 28), fill=(255, 207, 64))
    # scale bar 10 m
    sb = 10.0 / res * a.scale
    x0, y0 = 40, canvas.height - 35
    dc.line((x0, y0, x0 + sb, y0), fill=(220, 225, 232), width=4)
    dc.text((x0 + sb + 12, y0 - 16), "10 m", font=ImageFont.truetype(FONT.format("R"), 24), fill=(220, 225, 232))
    leg = "blue = walls / obstacles seen by the lidar   ·   light = free floor   ·   orange = path the robot walked"
    f = ImageFont.truetype(FONT.format("R"), 22)
    dc.text((canvas.width - 40 - dc.textlength(leg, font=f), y0 - 14), leg, font=f, fill=(170, 180, 195))
    canvas.save(a.out, optimize=True)
    print(a.out, canvas.size)


if __name__ == "__main__":
    main()
