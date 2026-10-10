# hospital-sim

A Unitree G1 humanoid working in a simulated hospital with a surgical wing. This is the master
repository: it holds no robot code of its own, only the interface contract, the shared environment
script and a manifest that checks out every component repository into the layout below. Clone this
one and you get the whole stack in the folder arrangement the code expects.

Each component is its own GitHub repository so that a different robot can reuse the hospital, the
ROS 2 packages and the operator UI while bringing its own description, simulator bindings and
controller. Repos prefixed `hospital-sim-` are robot agnostic. Repos prefixed `g1-` are specific to
the G1 29-DoF rev 1.0 with BrainCo Revo2 hands.

| Folder | Repository | What it holds |
|---|---|---|
| `hospital-sim-env/` | [hospital-sim-env](hospital-sim-env/README.md) | Isaac Sim hospital and surgical wing scene, the layout generator that is the single source of room geometry, and the surgical instruments with their placements |
| `g1-brainco-description/` | [g1-brainco-description](g1-brainco-description/README.md) | Canonical G1 + BrainCo model: URDF, MJCF, meshes, robot_spec.json, build and check scripts |
| `g1-mujoco-sim/` | [g1-mujoco-sim](g1-mujoco-sim/README.md) | MuJoCo version of the hospital, generated from the same layout, with the G1 placed in it |
| `g1-isaac-sim/` | [g1-isaac-sim](g1-isaac-sim/README.md) | G1 in the Isaac hospital: physics layer, lidar, cameras, DDS and ROS 2 bridge |
| `g1-whole-body-rl/` | [g1-whole-body-rl](g1-whole-body-rl/README.md) | Whole-body controller training in MuJoCo/MJX and the ONNX export the controller node loads |
| `ros2_ws/src/hospital-sim-ros2/` | [hospital-sim-ros2](ros2_ws/src/hospital-sim-ros2/README.md) | ROS 2 Humble packages: interfaces, controller, mode manager, keyboard teleop, MuJoCo sim node, navigation, mission, perception node, bringup |
| `g1-webcam-teleop/` | [g1-webcam-teleop](g1-webcam-teleop/README.md) | Seated webcam teleoperation (OBSBOT Tiny 3) through a fork of xr_teleoperate |
| `hospital-sim-ui/` | [hospital-sim-ui](hospital-sim-ui/README.md) | Operator UI: iPad PWA, engineering console and the aiohttp + rclpy server behind them |
| `docs/` | this repo | [interfaces.md](docs/interfaces.md) is the binding contract between the parts. [architecture.md](docs/architecture.md) has the system map |
| `datasets/` | Hugging Face | Recorded data. Not in git, see [datasets/README.md](datasets/README.md) |

The instrument detector that the mission can use is developed in a separate private repository. Nothing here depends on it: the perception node runs in ground-truth mode in simulation, and any ONNX detector can be supplied through a parameter.

`ros2_ws/` is the colcon workspace. Only its `src/hospital-sim-ros2` folder is a repository; `build/`,
`install/` and `log/` are produced by the build.

## Getting the whole stack

```bash
git clone https://github.com/Bkrakshith/hospital-sim.git Hospital_G1
cd Hospital_G1
pip install vcstool                       # or: sudo apt install python3-vcstool
vcs import < hospital-sim.repos           # clones every component into place
```

Two things are not in any git repository and have to be fetched separately:

- NVIDIA's Isaac for Healthcare assets. `hospital-sim-env/isaac/i4h_assets` is a symlink that must
  point at your local copy. [hospital-sim-env/isaac/README.md](hospital-sim-env/isaac/README.md) says
  which version and how to download it.
- Recorded datasets. `datasets/README.md` lists them and the Hugging Face repositories they live in.

## Environments

```bash
source env.sh
```

`env.sh` strips conda libraries from `LD_LIBRARY_PATH` (they break rclpy), sources ROS 2 Humble,
activates the shared `.venv` and sources the `ros2_ws` overlay once it has been built. It also exports
`HG1_ROOT`, which the launch files and scripts use to find sibling components.

| Environment | Used by | Notes |
|---|---|---|
| `.venv/` | ROS 2 nodes, UI server, teleop, objects, robot checks, MuJoCo | system python 3.10 with system site-packages so rclpy works. Install with `.venv/bin/pip` |
| conda `g1-mjx` | `g1-whole-body-rl` | JAX / MJX. Keep it out of `.venv` |
| conda `ultra-sim2sim` | `g1-whole-body-rl/ultra_eval` | the released ULTRA teacher |
| `~/isaacsim` python | `g1-isaac-sim`, `hospital-sim-env/isaac` | Isaac Sim 6.0 |

## Quick starts

```bash
# build the ROS 2 packages (first time, and after changing a package)
source env.sh && (cd ros2_ws && colcon build --symlink-install) && source env.sh

# MuJoCo hospital with the G1, controller and mode manager
ros2 launch g1_bringup sim.launch.py

# the same stack on Isaac Sim (start the simulator first, in another terminal)
./g1-isaac-sim/run.sh --headless
ros2 launch g1_bringup sim.launch.py backend:=isaac

# open the hospital scene in the Isaac Sim editor
./hospital-sim-env/isaac/launch_isaac.sh --open

# operator UI and engineering console
ros2 launch g1_bringup dashboard.launch.py        # https://localhost:8443 and /console
```

Each component README has its own build, test and run instructions.

## Working across repositories

The contract in `docs/interfaces.md` is what lets the repos change independently. Read it before
changing a topic, a joint order, a config path or a folder name, and update it in the same change.
Components find each other through `HG1_ROOT` or relative to their own location, never through
absolute paths, so the checkout can live anywhere.

Machine notes for the development workstation are at the bottom of `docs/interfaces.md`.
