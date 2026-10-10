#!/usr/bin/env python3
"""LinkedIn edit of the G1 hospital SLAM survey, drawn from the run's recorded data (no re-simulation):

  left  : the SLAM map as it grows (the /map messages slam_toolbox published during the walk, from the rosbag),
          view follows the robot and widens as the map grows; robot trail, route waypoints, Nav2 plan and the live
          2-D lidar scan on top (all from the same rosbag / survey log)
  right : the head-camera view, rendered in Isaac Sim afterwards from the recorded pose + joint trajectory
          (g1-isaac-sim/tools/replay_camera.py), same sim timestamps; route progress and legend
Every sped-up section states its speed factor relative to simulated time.

    python3 media/linkedin/compose.py <run_dir> --edit <run_dir>/edit --cam <frames_dir> --out x.mp4
        [--speed 70] [--portrait] [--nav-run <nav_check_dir> --nav-edit ... --nav-cam ...] [--map-png ...]
"""
import argparse
import bisect
import json
import math
import os
import sys

import numpy as np
import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_videos import Encoder, card, fade, font, hms, rounded  # noqa: E402

BG = (16, 20, 28)
UNKNOWN = (24, 29, 40)
FREE = (226, 231, 238)
OCC = (32, 120, 225)
TRAIL = (0, 190, 255)
PLAN = (60, 230, 100)
SCAN = (255, 40, 200)
ROBOT = (255, 210, 40)
WP = {"pending": (150, 150, 155), "current": (255, 217, 26), "reached": (51, 217, 77), "skipped": (242, 64, 51)}

AREA_CAPTIONS = {
    "Main lobby": "Main lobby", "Central hall": "Main hospital: central hall", "West hall": "Main hospital: west hall",
    "North-west ward": "North-west ward", "West corridor": "West wing corridor", "West wing room": "West wing rooms",
    "South-west hall": "West wing", "Stair hall (kept 1.5 m from the stairs)": "Stair hall (stairs avoided)",
    "East wing": "East wing", "East wing corridor": "East wing corridor", "East wing room": "East wing rooms",
    "East wing north": "East wing", "South-east lobby": "South-east lobby", "Link corridor": "Link to the surgical wing",
    "Surgical corridor": "Surgical wing corridor", "Sterile store": "Sterile store", "Pre-op": "Pre-op",
    "Scrub room": "Scrub room", "Operating theatre": "Operating theatre", "PACU": "Recovery (PACU)",
    "Main lobby (start)": "Back to the start: loop closed"}


class Data:
    def __init__(self, run_dir, edit_dir, cam_dir, route_yaml, static_map=None):
        self.ev = [json.loads(ln) for ln in open(os.path.join(run_dir, "survey_events.jsonl"))]
        self.route = yaml.safe_load(open(route_yaml))
        self.wps = self.route["waypoints"]
        self.maps = json.load(open(os.path.join(edit_dir, "maps", "index.json")))
        self.map_t = [m["t"] for m in self.maps]
        self.edit = edit_dir
        self.static_map = static_map
        self.plans = json.load(open(os.path.join(edit_dir, "plans.json")))
        self.plan_t = [p["t"] for p in self.plans]
        sc = np.load(os.path.join(edit_dir, "scans.npz"))
        self.scan_t = list(sc["t"])
        self.scans = [sc[f"s{i}"] for i in range(len(self.scan_t))]
        tr = np.loadtxt(os.path.join(run_dir, "trail_map.csv"), delimiter=",", ndmin=2)
        self.trail = tr[np.argsort(tr[:, 0])]
        poses = json.load(open(os.path.join(edit_dir, "poses.json")))
        self.pose = np.array(sorted(poses))
        rows = [ln.strip().split(",") for ln in open(os.path.join(cam_dir, "index.csv")) if ln.strip()]
        rows.sort(key=lambda r: float(r[0]))
        self.cam_t = [float(r[0]) for r in rows]
        self.cam_f = [os.path.join(cam_dir, r[2]) for r in rows]
        self._map_cache = (None, None)
        st = next(e for e in self.ev if e["event"] == "walk_start")
        fin = [e for e in self.ev if e["event"] == "finish"]
        self.s0, self.s1 = st["sim"], (fin[-1]["sim"] if fin else self.ev[-1]["sim"])
        self.dist = np.concatenate([[0], np.cumsum(np.hypot(np.diff(self.trail[:, 1]), np.diff(self.trail[:, 2])))])

    def latest(self, ts, t):
        i = bisect.bisect_right(ts, t) - 1
        return max(i, 0) if ts else None

    def map_at(self, t):
        if self.static_map is not None:
            return self.static_map
        i = self.latest(self.map_t, t)
        if self._map_cache[0] != i:
            m = self.maps[i]
            g = np.array(Image.open(os.path.join(self.edit, "maps", m["file"])))
            rgb = np.empty(g.shape + (3,), np.uint8)
            rgb[:] = UNKNOWN
            rgb[g == 0] = FREE
            rgb[g == 100] = OCC
            known = np.nonzero(g != 255)
            # bbox in world: rows top-down
            r0, r1, c0, c1 = known[0].min(), known[0].max(), known[1].min(), known[1].max()
            H = g.shape[0]
            bb = (m["ox"] + c0 * m["res"], m["oy"] + (H - 1 - r1) * m["res"],
                  m["ox"] + (c1 + 1) * m["res"], m["oy"] + (H - r0) * m["res"])
            self._map_cache = (i, (Image.fromarray(rgb), m, bb))
        return self._map_cache[1]

    def robot(self, t):
        k = np.clip(np.searchsorted(self.pose[:, 0], t), 0, len(self.pose) - 1)
        return self.pose[k, 1:4]

    def wp_states(self, t):
        st = {i: "pending" for i in range(len(self.wps))}
        cur = None
        for e in self.ev:
            if e["sim"] > t:
                break
            if e["event"] == "goal":
                cur = e["index"]
            elif e["event"] == "goal_result" and e["outcome"] == "succeeded":
                st[e["index"]] = "reached"
            elif e["event"] == "waypoint_skipped":
                st[e["index"]] = "skipped"
        if cur is not None and st[cur] == "pending":
            st[cur] = "current"
        return st, cur

    def walked(self, t):
        k = np.searchsorted(self.trail[:, 0], t)
        return float(self.dist[min(max(k - 1, 0), len(self.dist) - 1)])

    def cam(self, t):
        i = self.latest(self.cam_t, t)
        return self.cam_f[i] if i is not None else None


class View:
    """smoothed view box (centre + half height in metres) that contains the known map and the robot."""

    def __init__(self, aspect):
        self.aspect = aspect
        self.c = None
        self.h = None

    def update(self, bb, robot, alpha=0.06, min_half=7.0):
        x0, y0, x1, y1 = bb
        rx, ry = robot[0], robot[1]
        x0, y0, x1, y1 = min(x0, rx - 4), min(y0, ry - 4), max(x1, rx + 4), max(y1, ry + 4)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        half = max((y1 - y0) / 2 + 2.0, (x1 - x0) / 2 / self.aspect + 2.0, min_half)
        if self.c is None:
            self.c, self.h = np.array([cx, cy]), half
        else:
            self.c += alpha * (np.array([cx, cy]) - self.c)
            self.h += alpha * (half - self.h)
        return self.c, self.h


def draw_map_pane(D, t, view, size, show_route=True):
    pw, ph = size
    img_m, m, bb = D.map_at(t)
    robot = D.robot(t)
    (cx, cy), half_h = view.update(bb, robot)
    half_w = half_h * pw / ph
    res = m["res"]
    H = m["h"]
    # world box -> map pixel box (image row 0 = top = max y)
    left = (cx - half_w - m["ox"]) / res
    right = (cx + half_w - m["ox"]) / res
    top = H - (cy + half_h - m["oy"]) / res
    bottom = H - (cy - half_h - m["oy"]) / res
    canvas = Image.new("RGB", (pw, ph), UNKNOWN)
    crop = img_m.transform((pw, ph), Image.EXTENT, (left, top, right, bottom), resample=Image.NEAREST,
                           fillcolor=UNKNOWN)
    canvas.paste(crop)
    d = ImageDraw.Draw(canvas, "RGBA")
    sc = pw / (2 * half_w)  # px per metre

    def P(x, y):
        return ((x - (cx - half_w)) * sc, ((cy + half_h) - y) * sc)

    if show_route:
        st, cur = D.wp_states(t)
        start = D.route["start"]
        line = [P(start["x"], start["y"])] + [P(w["x"], w["y"]) for w in D.wps]
        d.line(line, fill=(140, 140, 150, 110), width=max(1, int(sc * 0.05)))
        r = max(3, int(sc * 0.18))
        for i, w in enumerate(D.wps):
            x, y = P(w["x"], w["y"])
            rr = r * 1.5 if st[i] == "current" else r
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=WP[st[i]] + (235,), outline=(10, 10, 10, 200))
    k = np.searchsorted(D.trail[:, 0], t)
    if k > 1:
        tr = D.trail[:k, 1:3][::2]
        cut = [0] + [j for j in range(1, len(tr)) if np.hypot(*(tr[j] - tr[j - 1])) > 1.5] + [len(tr)]
        for c0, c1 in zip(cut[:-1], cut[1:]):  # no line across gaps in the trail log
            if c1 - c0 > 1:
                d.line([P(x, y) for x, y in tr[c0:c1]], fill=TRAIL + (255,), width=max(2, int(sc * 0.12)), joint="curve")
    i = D.latest(D.plan_t, t)
    if i is not None and t - D.plan_t[i] < 3.0 and D.plans[i]["pts"]:
        d.line([P(x, y) for x, y in D.plans[i]["pts"]], fill=PLAN + (230,), width=max(2, int(sc * 0.08)))
    j = D.latest(D.scan_t, t)
    if j is not None and t - D.scan_t[j] < 6.0:
        rr = max(1.0, sc * 0.05)
        for x, y in D.scans[j]:
            u, v = P(x, y)
            d.ellipse((u - rr, v - rr, u + rr, v + rr), fill=SCAN + (255,))
    rx, ry, yaw = robot
    u, v = P(rx, ry)
    L = max(16.0, sc * 0.9)
    tip = (u + L * math.cos(yaw), v - L * math.sin(yaw))
    l1 = (u + 0.45 * L * math.cos(yaw + 2.5), v - 0.45 * L * math.sin(yaw + 2.5))
    l2 = (u + 0.45 * L * math.cos(yaw - 2.5), v - 0.45 * L * math.sin(yaw - 2.5))
    d.polygon([tip, l1, (u, v), l2], fill=ROBOT + (255,), outline=(20, 20, 20, 255))
    # scale bar
    for m_ in (1, 2, 5, 10, 20):
        if m_ * sc > 90:
            break
    x0, y0 = 24, ph - 30
    d.line((x0, y0, x0 + m_ * sc, y0), fill=(230, 235, 242, 255), width=4)
    d.text((x0 + m_ * sc + 10, y0 - 15), f"{m_} m", font=font(22), fill=(230, 235, 242))
    return canvas


def info_panel(D, t, size, speed, title_area=True):
    pw, ph = size
    img = Image.new("RGB", (pw, ph), BG)
    d = ImageDraw.Draw(img)
    st, cur = D.wp_states(t)
    area = D.wps[cur]["area"] if cur is not None else "Starting"
    d.text((24, 16), "Autonomous survey: Nav2 drives, lidar SLAM maps", font=font(24, bold=True), fill=(154, 164, 178))
    d.text((24, 52), AREA_CAPTIONS.get(area, area), font=font(40, bold=True), fill=(255, 255, 255))
    done = sum(v in ("reached", "skipped") for v in st.values())
    d.text((24, 110), f"waypoint {min(done + 1, len(D.wps))} of {len(D.wps)}   ·   walked {D.walked(t):.0f} m   ·   "
           f"sim time {hms(t - D.s0)}", font=font(24), fill=(223, 229, 238))
    d.rounded_rectangle((24, 152, pw - 24, 164), 6, fill=(38, 44, 56))
    d.rounded_rectangle((24, 152, 24 + (pw - 48) * done / len(D.wps), 164), 6, fill=(60, 230, 100))
    items = [(TRAIL, "robot trail"), (PLAN, "Nav2 plan"), (SCAN, "2-D lidar scan"), (ROBOT, "robot"),
             (WP["reached"], "waypoint reached"), (WP["pending"], "waypoint pending"), (OCC, "map: wall / obstacle"),
             (FREE, "map: free floor")]
    for k, (c, txt) in enumerate(items):
        x = 24 + (k % 2) * (pw // 2)
        y = 186 + (k // 2) * 30
        d.rectangle((x, y + 4, x + 24, y + 18), fill=c)
        d.text((x + 34, y), txt, font=font(20), fill=(200, 208, 220))
    return img


def frame(D, t, view, speed, cap=None, cap_a=0.0, portrait=False):
    if portrait:
        W, H = 1080, 1350
        img = Image.new("RGB", (W, H), BG)
        cam = D.cam(t)
        if cam:
            c = Image.open(cam).convert("RGB").resize((1080, 608), Image.LANCZOS)
            img.paste(c, (0, 64))
        pane = draw_map_pane(D, t, view, (1080, 618))
        img.paste(pane, (0, 672))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle((0, 0, W, 64), fill=(8, 10, 15))
        rounded(d, (16, 12, 196, 52), 8, (200, 30, 40, 235))
        d.text((30, 17), "SIMULATION", font=font(22, bold=True), fill=(255, 255, 255))
        d.text((214, 16), "Unitree G1 · lidar SLAM + Nav2", font=font(26, bold=True), fill=(255, 207, 64))
        d.rectangle((0, H - 60, W, H), fill=(8, 10, 15))
        st, cur = D.wp_states(t)
        area = D.wps[cur]["area"] if cur is not None else ""
        d.text((20, H - 48), AREA_CAPTIONS.get(area, area), font=font(28, bold=True), fill=(255, 255, 255))
        txt = f"{speed:.0f}× sim speed · {hms(t - D.s0)}"
        f = font(24)
        d.text((W - 20 - d.textlength(txt, font=f), H - 45), txt, font=f, fill=(225, 230, 238))
        d.text((16, 640), "camera rendered afterwards from the recorded walk", font=font(18), fill=(150, 160, 175))
        if cap and cap_a > 0:
            f3 = font(40, bold=True)
            tw = d.textlength(cap, font=f3)
            x = (W - tw) / 2
            rounded(d, (x - 22, 692, x + tw + 22, 754), 12, (10, 12, 18, int(225 * cap_a)))
            d.text((x, 700), cap, font=f3, fill=(255, 255, 255, int(255 * cap_a)))
        return img
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), BG)
    pane = draw_map_pane(D, t, view, (1140, 1020))
    img.paste(pane, (0, 0))
    cam = D.cam(t)
    if cam:
        c = Image.open(cam).convert("RGB").resize((780, 439), Image.LANCZOS)
        img.paste(c, (1140, 30))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((1140, 0, W, 30), fill=(8, 10, 15))
    d.text((1150, 4), "Head camera (forward view) · rendered afterwards in Isaac Sim from the recorded walk",
           font=font(17), fill=(170, 180, 195))
    img.paste(info_panel(D, t, (780, 1020 - 469), speed), (1140, 469))
    d.rectangle((0, H - 60, W, H), fill=(8, 10, 15))
    d.text((24, H - 46), "Unitree G1 · NVIDIA Isaac Sim · lidar SLAM (slam_toolbox) + Nav2", font=font(26, bold=True),
           fill=(255, 207, 64))
    txt = f"{speed:.0f}× faster than simulated time   ·   sim time {hms(t - D.s0)}"
    f = font(24)
    d.text((W - 24 - d.textlength(txt, font=f), H - 44), txt, font=f, fill=(225, 230, 238))
    rounded(d, (18, 16, 200, 56), 8, (200, 30, 40, 235))
    d.text((32, 22), "SIMULATION", font=font(22, bold=True), fill=(255, 255, 255))
    if cap and cap_a > 0:
        f3 = font(46, bold=True)
        tw = d.textlength(cap, font=f3)
        x = (1140 - tw) / 2
        rounded(d, (x - 26, 70, x + tw + 26, 142), 14, (10, 12, 18, int(225 * cap_a)))
        d.text((x, 80), cap, font=f3, fill=(255, 255, 255, int(255 * cap_a)))
    return img


def captions(D):
    out, last = [], None
    for e in D.ev:
        if e["event"] != "goal" or not (D.s0 <= e["sim"] <= D.s1):
            continue
        c = AREA_CAPTIONS.get(e.get("area"), e.get("area"))
        if c != last:
            out.append((e["sim"], c))
            last = c
    return out


def walk_section(enc, D, speed, portrait, s0=None, s1=None, extra_caps=()):
    s0 = D.s0 if s0 is None else s0
    s1 = D.s1 if s1 is None else s1
    view = View((1080 / 618) if portrait else (1140 / 1020))
    caps = sorted(captions(D) + list(extra_caps))
    n = int((s1 - s0) / speed * 30)
    last = None
    for i in range(n):
        t = s0 + i * speed / 30.0
        cap, a = None, 0.0
        for cs, ct in caps:
            dt = (t - cs) / speed
            if 0 <= dt < 2.4:
                cap, a = ct, min(1.0, dt / 0.3, (2.4 - dt) / 0.4)
        last = frame(D, t, view, speed, cap, a, portrait)
        enc.put(last)
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--edit", required=True)
    ap.add_argument("--cam", required=True)
    ap.add_argument("--route", default="ros2_ws/src/hospital-sim-ros2/g1_navigation/config/survey_route.yaml")
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed", type=float, default=70.0)
    ap.add_argument("--portrait", action="store_true")
    ap.add_argument("--map-png", default="")
    ap.add_argument("--nav-run", default="")
    ap.add_argument("--nav-edit", default="")
    ap.add_argument("--nav-cam", default="")
    ap.add_argument("--nav-route", default="ros2_ws/src/hospital-sim-ros2/g1_navigation/config/nav_check_route.yaml")
    ap.add_argument("--nav-speed", type=float, default=40.0)
    ap.add_argument("--nav-map", default="ros2_ws/src/hospital-sim-ros2/g1_navigation/maps/hospital_full.yaml")
    ap.add_argument("--test-seconds", type=float, default=0, help="only this many video seconds of the walk")
    a = ap.parse_args()
    W, H = (1080, 1350) if a.portrait else (1920, 1080)
    D = Data(a.run_dir, a.edit, a.cam, a.route)
    enc = Encoder(a.out, W, H)
    view = View((1080 / 618) if a.portrait else (1140 / 1020))
    first = frame(D, D.s0, view, a.speed, portrait=a.portrait)

    def mk_card(lines, sub, bg):
        if (W, H) == (1920, 1080):
            return card(lines, sub, bg)
        c = card(lines, sub, None).resize((1080, 608), Image.LANCZOS)  # keep the aspect ratio
        out = Image.new("RGB", (W, H), (12, 15, 22))
        if bg is not None:
            from PIL import ImageFilter
            out = Image.blend(bg.filter(ImageFilter.GaussianBlur(6)), out, 0.75)
        out.paste(c, (0, (H - 608) // 2))
        return out

    title = mk_card([("Unitree G1 mapping a hospital with lidar SLAM", 58, True, (255, 255, 255)),
                     ("simulation", 40, False, (255, 207, 64))],
                    ["NVIDIA Isaac Sim hospital + surgical wing · Livox MID-360 lidar · slam_toolbox · Nav2",
                     "The robot walks a 60-waypoint route on its own: Nav2 on the live SLAM map, nobody drives it."],
                    first)
    for _ in range(int(3.5 * 30)):
        enc.put(title)
    fade(enc, title, first, 12)
    s1 = D.s1 if not a.test_seconds else D.s0 + a.test_seconds * a.speed
    last = walk_section(enc, D, a.speed, a.portrait, D.s0, s1)
    if a.map_png and os.path.exists(a.map_png):
        m = Image.open(a.map_png).convert("RGB")
        endc = Image.new("RGB", (W, H), BG)
        sc = min((W - 60) / m.width, (H - 230) / m.height)
        m2 = m.resize((int(m.width * sc), int(m.height * sc)), Image.LANCZOS)
        endc.paste(m2, ((W - m2.width) // 2, 30))
        dd = ImageDraw.Draw(endc)
        for k, (txt, f, col) in enumerate([
                ("Map saved: built from the robot's own lidar during the walk", font(34 if W > 1500 else 30, bold=True),
                 (255, 255, 255)),
                ("Now the default map for localisation (AMCL) and Nav2 navigation", font(26, light=True),
                 (170, 180, 195))]):
            dd.text(((W - dd.textlength(txt, font=f)) / 2, H - 170 + k * 50), txt, font=f, fill=col)
        fade(enc, last, endc, 18)
        for _ in range(int(4.0 * 30)):
            enc.put(endc)
        last = endc
    if a.nav_run:
        y = yaml.safe_load(open(a.nav_map))
        g = np.array(Image.open(os.path.join(os.path.dirname(a.nav_map), y["image"])))
        rgb = np.empty(g.shape + (3,), np.uint8)
        rgb[:] = UNKNOWN
        rgb[g > 250] = FREE
        rgb[g < 100] = OCC
        kn = np.nonzero(g != 205)
        Hh = g.shape[0]
        res, ox, oy = y["resolution"], y["origin"][0], y["origin"][1]
        bb = (ox + kn[1].min() * res, oy + (Hh - 1 - kn[0].max()) * res, ox + (kn[1].max() + 1) * res,
              oy + (Hh - kn[0].min()) * res)
        static = (Image.fromarray(rgb), {"res": res, "ox": ox, "oy": oy, "h": Hh}, bb)
        N = Data(a.nav_run, a.nav_edit, a.nav_cam, a.nav_route, static_map=static)
        nf = frame(N, N.s0, View(1), a.nav_speed, portrait=a.portrait)
        sec = mk_card([("Nav2 on the new map", 54, True, (255, 255, 255)),
                       ("simulation", 36, False, (255, 207, 64))],
                      ["Fresh start: AMCL localises on the saved map from the spawn pose,",
                       "then three goals: operating theatre, east wing corridor, main lobby."], nf)
        fade(enc, last, sec, 15)
        for _ in range(int(3.0 * 30)):
            enc.put(sec)
        fade(enc, sec, nf, 12)
        last = walk_section(enc, N, a.nav_speed, a.portrait)
    enc.close()
    print(f"{enc.n} frames, {enc.n / 30:.1f} s -> {a.out}")


if __name__ == "__main__":
    main()
