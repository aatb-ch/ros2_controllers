#!/bin/bash
# usage: run.sh stock|fix   (inside the container; /w = this bundle)
set -e
V=$1
source /opt/ros/jazzy/setup.bash
source /w/install_$V/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST ROS_DOMAIN_ID=61
ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat /w/robot.urdf)" > /w/rsp_$V.log 2>&1 &
chrt -f 80 ros2 run controller_manager ros2_control_node --ros-args --params-file /w/controllers.yaml > /w/cm_$V.log 2>&1 &
sleep 4
ros2 run controller_manager spawner joint_state_broadcaster jtc > /w/spawn_$V.log 2>&1
grep -o "/w/install_[a-z]*/joint_trajectory_controller/lib/libjoint_trajectory_controller.so" /proc/$(pgrep -f ros2_control_node | head -1)/maps | sort -u
chrt -f 70 python3 -u /w/measure.py $V
pkill -f ros2_control_node; pkill -f robot_state_publisher; sleep 1
