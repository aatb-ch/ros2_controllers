import csv, collections, statistics, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
S = sys.argv[1] if len(sys.argv) > 1 else "."; DT = 0.002
STOCK, PATCH = '#2a78d6', '#eb6834'
INK, MUTED, GRID, SURF = '#1a1a19', '#6b6a63', '#e6e5df', '#fcfcfb'
plt.rcParams.update({'font.size': 10, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED,
                     'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF})
def trials(lab):
    rows = list(csv.reader(open(f'{S}/trace_{lab}.csv'))); T = collections.defaultdict(list); n = 0; prev = None
    for _, v, d, w, st, q in rows:
        w = float(w)
        if prev is not None and w < prev - 1: n += 1
        prev = w; T[n].append((w, float(st), float(q)))
    return list(T.values())
def per_cycle(s):
    ks = [round((s[i][1] - s[i - 1][1]) / DT) for i in range(1, len(s))]
    out = []
    for i in range(1, len(s)):
        if ks[i - 1] != 1 or (i >= 2 and ks[i - 2] != 1) or (i < len(ks) and ks[i] != 1): continue
        out.append((s[i][0], abs(s[i][2] - s[i - 1][2])))
    v0 = statistics.median([x for t, x in out if -0.6 < t < -0.05])
    return [(t, x / v0) for t, x in out]
fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
for ax, lab, col, name in ((axes[0], 'stock', STOCK, 'Jazzy 4.43.1'), (axes[1], 'fix', PATCH, 'Jazzy 4.43.1 + this fix')):
    peaks = []
    for s in trials(lab):
        pc = per_cycle(s)
        # hand-off = the cycle just before 5 consecutive decelerating cycles
        j = next(i for i in range(len(pc) - 5) if pc[i][0] >= 0 and all(pc[i + k][1] < 0.995 for k in range(5)))
        i0 = j - 1
        xs = list(range(-10, 61)); ys = [pc[i0 + k][1] if 0 <= i0 + k < len(pc) else None for k in xs]
        ax.plot(xs, ys, color=col, lw=1.3, alpha=0.6, marker='o', ms=2.5)
        peaks.append(max(y for t, y in pc if 0 <= t < 0.2))
    hit = sum(p > 1.5 for p in peaks)
    ax.axvline(-0.5, color=MUTED, lw=1, ls=(0, (3, 3)))
    ax.set_title(f'{name}: {hit}/{len(peaks)} stops with a step > 1.5×', color=INK, fontsize=10, loc='left')
    ax.set_xlabel('control cycle (2 ms) from the hand-off')
    ax.set_ylim(0, 2.3); ax.grid(axis='y', color=GRID, lw=0.8)
axes[0].set_ylabel('command increment / increment before')
fig.suptitle('ros2_control_node + mock_components, JTC @ 500 Hz, SCHED_FIFO on PREEMPT_RT (Raspberry Pi 4)\n'
             'single-point stop goal while moving at 0.2 / 0.5 / 1.0 rad/s, 4 stops each', x=0.01, ha='left', color=INK, fontsize=10)
fig.tight_layout(); fig.savefig(f'{S}/jtc_replacement_step_rt.png', dpi=150)
print('ok')
