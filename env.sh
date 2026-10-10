# Source this (bash) before running anything ROS 2 / teleop / UI in the hospital-sim checkout:
#   source env.sh
# Strips conda libraries from LD_LIBRARY_PATH (they break rclpy), sources ROS 2 Humble,
# activates the shared venv (.venv, system python 3.10 + system site-packages) and the
# ros2_ws overlay if it has been built. Exports HG1_ROOT, the root of this checkout, which the
# component repos use to find each other.
HG1_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HG1_ROOT

if [ -n "$CONDA_PREFIX" ] && command -v conda >/dev/null 2>&1; then
    conda deactivate 2>/dev/null || true
fi
LD_LIBRARY_PATH="$(printf '%s' "$LD_LIBRARY_PATH" | tr ':' '\n' | grep -v -e miniconda3 -e '^$' | paste -sd: -)"
export LD_LIBRARY_PATH

source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source "$HG1_ROOT/.venv/bin/activate"
if [ -f "$HG1_ROOT/ros2_ws/install/setup.bash" ]; then
    source "$HG1_ROOT/ros2_ws/install/setup.bash"
fi
