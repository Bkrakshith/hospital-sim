#!/usr/bin/env python3
"""Extract what the edit needs from a survey run's rosbag2 directories (system ROS python):

  maps/<sim_ms>.png + maps/index.json : /map snapshots (every --map-every sim s; 0 free, 100 occupied, 255 unknown;
                                         row 0 = top), with origin and resolution
  plans.json                          : /plan polylines (every --plan-every sim s)
  scans.npz                           : /scan endpoints in the map frame (every --scan-every sim s), placed with the
                                         robot pose from /survey/robot_pose (TF map->pelvis; the laser_level frame
                                         sits ~0.4 m above the pelvis with the pelvis heading)
  poses.json                          : /survey/robot_pose (map frame)
  timing.json                         : wall (bag receive time) <-> sim (/sim/status sim_time)

    source env.sh && python3 media/linkedin/extract_survey_data.py <run_dir> [--out <run_dir>/edit]
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image
from rclpy.serialization import deserialize_message
from rosbag2_py import ConverterOptions, SequentialReader, StorageFilter, StorageOptions
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import OccupancyGrid, Path
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


def stamp(m):
    return m.header.stamp.sec + 1e-9 * m.header.stamp.nanosec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", default="")
    ap.add_argument("--map-every", type=float, default=4.0)
    ap.add_argument("--plan-every", type=float, default=1.0)
    ap.add_argument("--scan-every", type=float, default=0.5)
    a = ap.parse_args()
    out = a.out or os.path.join(a.run_dir, "edit")
    os.makedirs(os.path.join(out, "maps"), exist_ok=True)
    bags = sorted(d for d in os.listdir(a.run_dir) if d.startswith("bag") and os.path.isdir(os.path.join(a.run_dir, d)))
    maps, plans, poses, scans, timing = [], [], [], [], {"wall": [], "sim": []}
    last = {"map": -1e9, "plan": -1e9, "scan": -1e9}
    clock_sim = 0.0
    for b in bags:
        r = SequentialReader()
        r.open(StorageOptions(uri=os.path.join(a.run_dir, b), storage_id="sqlite3"), ConverterOptions("cdr", "cdr"))
        r.set_filter(StorageFilter(topics=["/map", "/plan", "/scan", "/survey/robot_pose", "/sim/status"]))
        while r.has_next():
            topic, data, t = r.read_next()
            if topic == "/sim/status":
                s = json.loads(deserialize_message(data, String).data)
                timing["wall"].append(t * 1e-9)
                timing["sim"].append(float(s["sim_time"]))
                clock_sim = float(s["sim_time"])
            elif topic == "/survey/robot_pose":
                m = deserialize_message(data, PoseStamped)
                q = m.pose.orientation
                poses.append((stamp(m), m.pose.position.x, m.pose.position.y,
                              math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))))
            elif topic == "/map":
                m = deserialize_message(data, OccupancyGrid)
                ts = stamp(m) or clock_sim
                if ts - last["map"] < a.map_every:
                    continue
                last["map"] = ts
                i = m.info
                g = np.asarray(m.data, np.int16).reshape(i.height, i.width)
                img = np.full(g.shape, 255, np.uint8)
                img[(g >= 0) & (g <= 25)] = 0
                img[g >= 65] = 100
                name = f"{int(ts * 1000):09d}.png"
                Image.fromarray(img[::-1]).save(os.path.join(out, "maps", name), optimize=False, compress_level=3)
                maps.append({"t": ts, "file": name, "res": i.resolution, "ox": i.origin.position.x,
                             "oy": i.origin.position.y, "w": i.width, "h": i.height})
            elif topic == "/plan":
                m = deserialize_message(data, Path)
                ts = stamp(m) or clock_sim
                if ts - last["plan"] < a.plan_every:
                    continue
                last["plan"] = ts
                pts = [(round(p.pose.position.x, 2), round(p.pose.position.y, 2)) for p in m.poses[::4]]
                plans.append({"t": ts, "pts": pts})
            elif topic == "/scan":
                m = deserialize_message(data, LaserScan)
                ts = stamp(m)
                if ts - last["scan"] < a.scan_every:
                    continue
                last["scan"] = ts
                scans.append((ts, np.asarray(m.ranges, np.float32), m.angle_min, m.angle_increment))
    poses.sort()
    P = np.array(poses)
    pts_t, pts = [], []
    for ts, rg, a0, da in scans:
        if len(P) == 0:
            break
        k = np.clip(np.searchsorted(P[:, 0], ts), 0, len(P) - 1)
        _, x, y, yaw = P[k]
        ang = a0 + da * np.arange(len(rg)) + yaw
        ok = np.isfinite(rg) & (rg < 15.0)
        xy = np.stack([x + rg[ok] * np.cos(ang[ok]), y + rg[ok] * np.sin(ang[ok])], 1)[::2]
        pts_t.append(ts)
        pts.append(xy.astype(np.float32))
    np.savez_compressed(os.path.join(out, "scans.npz"), t=np.array(pts_t),
                        **{f"s{i}": p for i, p in enumerate(pts)})
    json.dump(maps, open(os.path.join(out, "maps", "index.json"), "w"))
    json.dump(plans, open(os.path.join(out, "plans.json"), "w"))
    json.dump(poses, open(os.path.join(out, "poses.json"), "w"))
    json.dump(timing, open(os.path.join(out, "timing.json"), "w"))
    print(f"{len(maps)} maps, {len(plans)} plans, {len(pts)} scans, {len(poses)} poses, bags {bags}")


if __name__ == "__main__":
    main()
