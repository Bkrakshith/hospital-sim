#!/usr/bin/env python3
"""Build the LinkedIn videos of the G1 hospital SLAM survey from what the run recorded (no re-simulation).

Inputs (one run directory, datasets/slam_survey/<run>/, written by the survey tooling):
  screen.mkv               ffmpeg x11grab of the RViz layout (ros2_ws/src/hospital-sim-ros2/g1_navigation/rviz/slam_survey.rviz)
                           + caption bar, 1920x1080, 30 fps, wall-clock time; screen_start_wall.txt = start (unix s)
  bag/                     rosbag2: /sim/status (sim_time) gives the wall <-> sim time mapping (bag stamps = wall)
  camera_frames/           every head-camera frame as JPEG (+ index.csv: sim_s, wall_s, file)
  survey_events.jsonl      survey_runner.py events (wall, sim, waypoint, area, outcome)
Outputs go to media/linkedin/. Encoding: imageio-ffmpeg's static ffmpeg (libx264), frames composed with PIL, so no
drawtext escaping. Every sped-up clip states its speed factor relative to SIMULATED time on screen.

    python3 media/linkedin/make_videos.py <run_dir> all|full|linkedin|portrait|camera [--speed 70]
"""
import argparse
import bisect
import io
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/ubuntu"
W, H = 1920, 1080


def font(size, bold=False, light=False):
    name = "Ubuntu-B.ttf" if bold else ("Ubuntu-L.ttf" if light else "Ubuntu-R.ttf")
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    except OSError:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


class Encoder:
    """raw RGB frames -> H.264 MP4 (yuv420p, +faststart: plays in browsers / LinkedIn)."""

    def __init__(self, path, w=W, h=H, fps=30, crf=19, preset="slow"):
        self.p = subprocess.Popen(
            [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
             "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt",
             "yuv420p", "-profile:v", "high", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
        self.n = 0
        self.w, self.h = w, h

    def put(self, img):
        if img.size != (self.w, self.h):
            img = img.resize((self.w, self.h), Image.LANCZOS)
        self.p.stdin.write(img.convert("RGB").tobytes())
        self.n += 1

    def close(self):
        self.p.stdin.close()
        self.p.wait()


class ScreenReader:
    """Sequential reader of screen.mkv at a reduced frame rate: frame k is at wall start + k / fps."""

    def __init__(self, path, fps=2.0, crop=None):
        vf = f"fps={fps}"
        self.fps = fps
        self.p = subprocess.Popen([ffmpeg_exe(), "-loglevel", "error", "-i", path, "-vf", vf, "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.k = -1
        self.cur = None

    def frame_at(self, t):
        """latest frame with time <= t (seconds since the recording started)."""
        want = int(math.floor(t * self.fps))
        while self.k < want:
            buf = self.p.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            self.k += 1
            self.cur = buf
        return Image.frombuffer("RGB", (W, H), self.cur, "raw", "RGB", 0, 1) if self.cur else None


class Run:
    def __init__(self, d):
        self.d = d
        self.screen_t0 = float(open(os.path.join(d, "screen_start_wall.txt")).read().split()[0])
        self.events = [json.loads(line) for line in open(os.path.join(d, "survey_events.jsonl"))]
        tm = os.path.join(d, "timing.json")
        if not os.path.exists(tm):
            self.make_timing(tm)
        t = json.load(open(tm))
        self.wall, self.sim = np.array(t["wall"]), np.array(t["sim"])
        idx = os.path.join(d, "camera_frames", "index.csv")
        rows = [ln.strip().split(",") for ln in open(idx) if ln.strip()]
        rows.sort(key=lambda r: float(r[0]))
        self.cam_sim = [float(r[0]) for r in rows]
        self.cam_file = [os.path.join(d, "camera_frames", r[2]) for r in rows]

    def make_timing(self, out):
        from rclpy.serialization import deserialize_message
        from rosbag2_py import ConverterOptions, SequentialReader, StorageFilter, StorageOptions
        from std_msgs.msg import String
        r = SequentialReader()
        r.open(StorageOptions(uri=os.path.join(self.d, "bag"), storage_id="sqlite3"),
               ConverterOptions("cdr", "cdr"))
        r.set_filter(StorageFilter(topics=["/sim/status"]))
        wall, sim = [], []
        while r.has_next():
            _, data, t = r.read_next()
            s = json.loads(deserialize_message(data, String).data)
            wall.append(t * 1e-9)
            sim.append(float(s["sim_time"]))
        json.dump({"wall": wall, "sim": sim}, open(out, "w"))

    def wall_of_sim(self, s):
        return float(np.interp(s, self.sim, self.wall))

    def sim_of_wall(self, w):
        return float(np.interp(w, self.wall, self.sim))

    def cam_at(self, s):
        i = bisect.bisect_right(self.cam_sim, s) - 1
        return self.cam_file[max(0, i)] if self.cam_file else None

    def walk_span(self):
        st = next(e for e in self.events if e["event"] == "walk_start")
        fin = [e for e in self.events if e["event"] == "finish"]
        end = fin[-1] if fin else self.events[-1]
        return st["sim"], end["sim"]

    def area_at(self, s):
        """area of the waypoint being driven to at sim time s."""
        area = None
        for e in self.events:
            if e["sim"] > s:
                break
            if e["event"] == "goal":
                area = e.get("area")
        return area


def hms(s):
    s = int(max(0, s))
    return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, r, fill=fill)


def banner(img, top_text, bottom_left, bottom_right, caption=None, caption_alpha=1.0):
    """overlay: top-left SIMULATION tag, bottom bar, optional centred caption."""
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((0, H - 60, W, H), fill=(8, 10, 15, 255))
    d.text((24, H - 46), bottom_left, font=font(26, bold=True), fill=(255, 207, 64))
    f = font(24)
    tw = d.textlength(bottom_right, font=f)
    d.text((W - 24 - tw, H - 44), bottom_right, font=f, fill=(225, 230, 238))
    if top_text:
        f2 = font(22, bold=True)
        tw = d.textlength(top_text, font=f2)
        rounded(d, (18, 16, 18 + tw + 28, 56), 8, (200, 30, 40, 230))
        d.text((32, 22), top_text, font=f2, fill=(255, 255, 255))
    if caption and caption_alpha > 0:
        f3 = font(44, bold=True)
        tw = d.textlength(caption, font=f3)
        x = (1136 - tw) / 2
        a = int(225 * caption_alpha)
        rounded(d, (x - 26, 70, x + tw + 26, 140), 14, (10, 12, 18, a))
        d.text((x, 80), caption, font=f3, fill=(255, 255, 255, int(255 * caption_alpha)))
    return img


def card(lines, sub=None, bg=None):
    img = bg.copy() if bg is not None else Image.new("RGB", (W, H), (12, 15, 22))
    if bg is not None:
        img = img.filter(ImageFilter.GaussianBlur(6))
        img = Image.blend(img, Image.new("RGB", (W, H), (8, 10, 15)), 0.72)
    d = ImageDraw.Draw(img)
    y = H / 2 - 40 * len(lines) - (40 if sub else 0)
    for i, (txt, size, bold, col) in enumerate(lines):
        f = font(size, bold=bold)
        tw = d.textlength(txt, font=f)
        d.text(((W - tw) / 2, y), txt, font=f, fill=col)
        y += size * 1.35
    if sub:
        y += 20
        for txt in sub:
            f = font(28, light=True)
            tw = d.textlength(txt, font=f)
            d.text(((W - tw) / 2, y), txt, font=f, fill=(170, 180, 195))
            y += 40
    return img


def fade(enc, a, b, n):
    for i in range(n):
        enc.put(Image.blend(a, b, (i + 1) / n))


# ----------------------------------------------------------------------------------------------------- videos
CAM_BOX = (1149, 30, 1911, 467)  # camera image inside the RViz layout (recording coordinates)
MASK_BOXES = [(1138, 467, 1920, 501)]  # RViz dock title strip ("Views") under the camera panel


def compose_walk_frame(run, sr, s, speed, caption, cap_a, sim0):
    w = run.wall_of_sim(s) - run.screen_t0
    img = sr.frame_at(w).copy()
    cam = run.cam_at(s)
    if cam:  # paste the full-resolution camera frame with the same sim stamp over the RViz image panel
        c = Image.open(cam).convert("RGB")
        bw, bh = CAM_BOX[2] - CAM_BOX[0], CAM_BOX[3] - CAM_BOX[1]
        sc = min(bw / c.width, bh / c.height)
        c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
        img.paste((12, 15, 22), CAM_BOX)
        for b in MASK_BOXES:
            img.paste((18, 22, 30), b)
        img.paste(c, (CAM_BOX[0] + (bw - c.width) // 2, CAM_BOX[1] + (bh - c.height) // 2))
    return banner(img, "SIMULATION", "Unitree G1 · NVIDIA Isaac Sim · lidar SLAM + Nav2",
                  f"{speed:.0f}× faster than simulated time   ·   sim time {hms(s - sim0)}", caption, cap_a)


def captions_for(run, s0, s1):
    """(sim_start, text) when the area changes; collapses consecutive equal areas."""
    out, last = [], None
    groups = {"Main lobby": "Main lobby", "Central hall": "Main hospital: central hall",
              "West hall": "Main hospital: west hall", "North-west ward": "North-west ward",
              "West corridor": "West wing corridor", "West wing room": "West wing rooms",
              "South-west hall": "West wing", "Stair hall (kept 1.5 m from the stairs)": "Stair hall (stairs avoided)",
              "East wing": "East wing", "East wing corridor": "East wing corridor", "East wing room": "East wing rooms",
              "East wing north": "East wing", "South-east lobby": "South-east lobby",
              "Link corridor": "Link to the surgical wing", "Surgical corridor": "Surgical wing corridor",
              "Sterile store": "Sterile store", "Pre-op": "Pre-op", "Scrub room": "Scrub room",
              "Operating theatre": "Operating theatre", "PACU": "Recovery (PACU)", "Main lobby (start)": "Back to the start"}
    for e in run.events:
        if e["event"] != "goal" or not (s0 <= e["sim"] <= s1):
            continue
        t = groups.get(e.get("area"), e.get("area"))
        if t != last:
            out.append((e["sim"], t))
            last = t
    return out


def make_linkedin(run, out, speed, nav_clip=None, map_png=None, portrait=False):
    s0, s1 = run.walk_span()
    caps = captions_for(run, s0, s1)
    enc = Encoder(out)
    sr = ScreenReader(os.path.join(run.d, "screen.mkv"), fps=2.0)
    first = compose_walk_frame(run, sr, s0, speed, None, 0, s0)
    title = card([("Unitree G1 mapping a hospital with lidar SLAM", 58, True, (255, 255, 255)),
                  ("simulation", 40, False, (255, 207, 64))],
                 sub=["NVIDIA Isaac Sim hospital + surgical wing · Livox MID-360 lidar · slam_toolbox · Nav2",
                      "The robot walks the route on its own (Nav2 on the live SLAM map); nobody drives it."],
                 bg=first)
    for _ in range(int(3.5 * 30)):
        enc.put(title)
    fade(enc, title, first, 15)
    n = int((s1 - s0) / speed * 30)
    ci = 0
    for i in range(n):
        s = s0 + i * speed / 30.0
        while ci + 1 < len(caps) and caps[ci + 1][0] <= s:
            ci += 1
        cap, a = None, 0.0
        if caps and caps[ci][0] <= s:
            dt = (s - caps[ci][0]) / speed  # video seconds since the caption started
            if dt < 2.6:
                cap, a = caps[ci][1], min(1.0, dt / 0.3, (2.6 - dt) / 0.4)
        last = compose_walk_frame(run, sr, s, speed, cap, a, s0)
        enc.put(last)
    if map_png:
        m = Image.open(map_png).convert("RGB")
        endc = Image.new("RGB", (W, H), (12, 15, 22))
        sc = min((W - 80) / m.width, (H - 200) / m.height)
        m2 = m.resize((int(m.width * sc), int(m.height * sc)), Image.LANCZOS)
        endc.paste(m2, ((W - m2.width) // 2, 40))
        dd = ImageDraw.Draw(endc)
        txt = "Map saved: hospital_full, built by the robot's own lidar during the walk (simulation)"
        f = font(32, bold=True)
        dd.text(((W - dd.textlength(txt, font=f)) / 2, H - 140), txt, font=f, fill=(255, 255, 255))
        txt2 = "Saved into the robot's Nav2 setup as the default map for localisation and navigation"
        f2 = font(26, light=True)
        dd.text(((W - dd.textlength(txt2, font=f2)) / 2, H - 92), txt2, font=f2, fill=(170, 180, 195))
        fade(enc, last, endc, 20)
        for _ in range(int(4.5 * 30)):
            enc.put(endc)
        last = endc
    if nav_clip:
        nav_frames(enc, nav_clip, last)
    enc.close()
    return enc.n


def nav_frames(enc, clip, prev):
    """append a prepared clip (list of PIL frames generator)."""
    first = True
    for im in clip():
        if first:
            fade(enc, prev, im, 15)
            first = False
        enc.put(im)


def make_camera(run, out, speed=7.5, fps=30):
    s0, s1 = run.walk_span()
    enc = Encoder(out, fps=fps, crf=20)
    t_end = (s1 - s0) / speed
    n = int(t_end * fps)
    for i in range(n):
        s = s0 + i * speed / fps
        img = Image.open(run.cam_at(s)).convert("RGB").resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(img, "RGBA")
        rounded(d, (18, 16, 230, 56), 8, (200, 30, 40, 220))
        d.text((32, 22), "SIMULATION", font=font(22, bold=True), fill=(255, 255, 255))
        txt = (f"Unitree G1 head camera (forward view) · NVIDIA Isaac Sim · {speed:g}× speed · "
               f"sim time {hms(s - s0)}")
        area = run.area_at(s)
        if area:
            txt += f" · {area}"
        f = font(24)
        tw = d.textlength(txt, font=f)
        rounded(d, (18, H - 58, 18 + tw + 28, H - 16), 8, (8, 10, 15, 200))
        d.text((32, H - 52), txt, font=f, fill=(230, 235, 242))
        enc.put(img)
    enc.close()
    return enc.n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("what", choices=["timing", "linkedin", "camera", "full"])
    ap.add_argument("--speed", type=float, default=70.0, help="linkedin: video speed vs simulated time")
    ap.add_argument("--camera-speed", type=float, default=7.5)
    ap.add_argument("--map-png", default=os.path.join(HERE, "hospital_full_map.png"))
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    run = Run(a.run_dir)
    if a.what == "timing":
        s0, s1 = run.walk_span()
        print(f"walk sim {s0:.1f} .. {s1:.1f} ({(s1 - s0) / 60:.1f} min); wall {run.wall_of_sim(s1) - run.wall_of_sim(s0):.0f} s;"
              f" camera frames {len(run.cam_file)}")
        return
    if a.what == "linkedin":
        n = make_linkedin(run, a.out or os.path.join(HERE, "g1_hospital_slam_linkedin.mp4"), a.speed,
                          map_png=a.map_png if os.path.exists(a.map_png) else None)
    elif a.what == "camera":
        n = make_camera(run, a.out or os.path.join(HERE, "g1_head_camera_walk.mp4"), a.camera_speed)
    print(f"{n} frames ({n / 30:.1f} s)")


if __name__ == "__main__":
    sys.exit(main())
