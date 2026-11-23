"""Constant-velocity motion on a JTC (interpolate_from_desired_state), then a single-point stop goal.
Records /joint_states every cycle; reports the joint velocity (dq/dstamp) right after the hand-off."""
import statistics, sys, time
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

J = ['j1', 'j2', 'j3']
LABEL = sys.argv[1]
CSV = open(f'/w/trace_{LABEL}.csv', 'w')


class N(Node):
    def __init__(self):
        super().__init__('jtc_handoff')
        self.s = []
        self.create_subscription(JointState, '/joint_states', self.cb, 2000)
        self.ac = ActionClient(self, FollowJointTrajectory, '/jtc/follow_joint_trajectory')

    def cb(self, m):
        i = [m.name.index(j) for j in J]
        self.s.append((m.header.stamp.sec + m.header.stamp.nanosec * 1e-9, [m.position[k] for k in i], time.monotonic()))

    def spin_for(self, d):
        e = time.monotonic() + d
        while time.monotonic() < e:
            rclpy.spin_once(self, timeout_sec=0.001)

    def goal(self, pos, t, vel=None):
        g = FollowJointTrajectory.Goal()
        tr = JointTrajectory(); tr.joint_names = J
        p = JointTrajectoryPoint(); p.positions = pos
        if vel is not None: p.velocities = vel
        p.time_from_start = Duration(sec=int(t), nanosec=int((t % 1) * 1e9))
        tr.points = [p]; g.trajectory = tr
        f = self.ac.send_goal_async(g)
        while not f.done(): rclpy.spin_once(self, timeout_sec=0.001)


rclpy.init(); n = N()
while not n.ac.server_is_ready(): rclpy.spin_once(n, timeout_sec=0.1)
n.spin_for(1.0)
res = []
for v in (0.2, 0.5, 1.0):
    for k in range(4):
        d = 1 if k % 2 == 0 else -1
        q = n.s[-1][1]
        n.goal([x + d * v * 3.0 for x in q], 3.0)          # positions only -> linear: constant v mid-way
        n.s.clear(); n.spin_for(1.2)
        q = n.s[-1][1]
        t0 = time.monotonic()
        n.goal([x + d * v * 0.25 for x in q], 0.5, [0.0] * 3)  # stop: to rest in 0.5 s (p + v*T/2)
        n.spin_for(0.8)
        s = n.s
        for st, qq, w in s: CSV.write(f'{LABEL},{v},{d},{w - t0:.6f},{st:.9f},{qq[0]:.9f}\n')
        vel = [(s[i][2] - t0, abs(s[i][1][0] - s[i - 1][1][0]) / (s[i][0] - s[i - 1][0])) for i in range(1, len(s)) if s[i][0] > s[i - 1][0]]
        v0 = statistics.median([x for t, x in vel if -0.6 < t < -0.05])
        after = [round(x / v0, 2) for t, x in vel if t >= 0][:6]
        dts = [round((s[i][0] - s[i - 1][0]) * 1e3, 2) for i in range(1, len(s))]
        res.append(max(after[:3]))
        print(f'v={v} trial {k}: first cycles after stop / v: {after}; cycle dt ms median {statistics.median(dts)} max {max(dts)}')
        n.spin_for(0.3)
print(f'{LABEL}: {sum(r > 1.5 for r in res)}/{len(res)} hand-offs > 1.5x in the first 3 cycles; max {max(res):.2f}')
