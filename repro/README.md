# JTC replacement step: repro

Runs in any Jazzy image with `controller_manager`, `joint_state_broadcaster` and `robot_state_publisher`. Uses two JTC overlays, `install_stock` and `install_fix`, built from the same source; they differ only in the one line.

```
docker run --cap-add SYS_NICE --ulimit rtprio=99 -v $PWD:/w ...
bash /w/run.sh stock
bash /w/run.sh fix
```

- `run.sh` starts `ros2_control_node` (500 Hz, `chrt -f 80`) with `mock_components`, spawns the JTC (`interpolate_from_desired_state: true`), and runs `measure.py`.
- `measure.py` moves at constant speed, then sends a single-point stop goal. It writes `trace_<label>.csv` with columns label, v, direction, t since goal sent, stamp, j1.
- `plot.py` takes the per-cycle command increment Δq / round(Δstamp / 2 ms) and skips samples next to stamp gaps.
