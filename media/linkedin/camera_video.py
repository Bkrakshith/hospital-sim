#!/usr/bin/env python3
"""Clean head-camera video of the survey walk: the frames rendered afterwards in Isaac Sim from the recorded walk
(g1-isaac-sim/tools/replay_camera.py, 0.5 Hz sim), one frame each, at 30 fps -> 60x faster than simulated time.

    python3 media/linkedin/camera_video.py <run_dir/edit_input> <camera_replay_dir> out.mp4 [--speed 60]
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import AREA_CAPTIONS, Data  # noqa: E402
from make_videos import Encoder, font, hms, rounded  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("run_dir")
ap.add_argument("cam")
ap.add_argument("out")
ap.add_argument("--edit", required=True)
ap.add_argument("--route", default="ros2_ws/src/hospital-sim-ros2/g1_navigation/config/survey_route.yaml")
ap.add_argument("--speed", type=float, default=60.0)
a = ap.parse_args()
D = Data(a.run_dir, a.edit, a.cam, a.route)
enc = Encoder(a.out, 1920, 1080, crf=21, preset="medium")
n = int((D.s1 - D.s0) / a.speed * 30)
for i in range(n):
    t = D.s0 + i * a.speed / 30.0
    img = Image.open(D.cam(t)).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    d = ImageDraw.Draw(img, "RGBA")
    rounded(d, (18, 16, 200, 56), 8, (200, 30, 40, 225))
    d.text((32, 22), "SIMULATION", font=font(22, bold=True), fill=(255, 255, 255))
    st, cur = D.wp_states(t)
    area = AREA_CAPTIONS.get(D.wps[cur]["area"], D.wps[cur]["area"]) if cur is not None else ""
    txt = (f"Unitree G1 head camera (forward view), rendered in Isaac Sim afterwards from the recorded walk  ·  "
           f"{a.speed:.0f}× faster than simulated time  ·  sim time {hms(t - D.s0)}  ·  {area}")
    f = font(22)
    tw = d.textlength(txt, font=f)
    rounded(d, (18, 1080 - 56, 18 + tw + 28, 1080 - 16), 8, (8, 10, 15, 200))
    d.text((32, 1080 - 50), txt, font=f, fill=(232, 236, 242))
    enc.put(img)
enc.close()
print(f"{enc.n} frames, {enc.n / 30:.1f} s -> {a.out}")
