import numpy as np
import matplotlib.pyplot as plt

# ----- Data in milliseconds (ms) -----
platforms = ["CPU-10W", "CPU-MAXN", "GPU-10W", "GPU-MAXN", "FPGA"]

data_ms = {  # Base
    "Per-event gen": [0.001069904583, 0.0004182,        0.001069904583,     0.0004182,          0.0],   # FPGA has combined stage
    "Parse→Torch":   [3.695376667,    1.7102,           3.695376667,        1.7102,             0.0],
    "Model forward": [4546.19,        2766.25,          169.29,             107.47,             0.0],
    "Gen+features":  [0.0,            0.0,              0.0,                0.0,                0.00807],   # 8.07 µs = 0.00807 ms
    "Head forward":  [0.0,            0.0,              0.0,                0.0,                0.00085],   # 0.85 µs = 0.00085 ms
}

# data_ms = { # Tiny
#     "Per-event gen": [0.001069904583, 0.0004182,        0.001069904583,     0.0004182,          0.0],   # FPGA has combined stage
#     "Parse→Torch":   [3.695376667,    1.7102,           3.695376667,        1.7102,             0.0],
#     "Model forward": [4194.58,        2531.74,          109.16,             71.51,              0.0],
#     "Gen+features":  [0.0,            0.0,              0.0,                0.0,                0.00401],   # 8.07 µs = 0.00807 ms
#     "Head forward":  [0.0,            0.0,              0.0,                0.0,                0.00085],   # 0.85 µs = 0.00085 ms
# }

# data_ms = { # kws
#     "Per-event gen": [0.001069904583, 0.0004182,        0.001069904583,     0.0004182,          0.0],   # FPGA has combined stage
#     "Parse→Torch":   [3.695376667,    1.7102,           3.695376667,        1.7102,             0.0],
#     "Model forward": [66.968,         29.114,           24.071,             17.094,             0.0],
#     "Gen+features":  [0.0,            0.0,              0.0,                0.0,                0.00848],   # 8.07 µs = 0.00807 ms
#     "Head forward":  [0.0,            0.0,              0.0,                0.0,                0.00205],   # 0.85 µs = 0.00085 ms
# }

colors = {
    "Per-event gen": "#7CD66B",  # fresh green
    "Parse→Torch":   "#F5B15A",  # warm orange
    "Model forward": "#65DBE0",  # bright teal
    "Gen+features":  "#FFD8A8",  # light orange
    "Head forward":  "#A9E38F",  # light green
}

# Keep previous hatching and styling; only colors changed
hatches = {
    "Per-event gen": "//",
    "Parse→Torch":   "\\\\",
    "Model forward": "xx",
    "Gen+features":  "..",
    "Head forward":  "++",
}

# Compute totals
totals = np.array([
    sum(data_ms[k][0] for k in data_ms),
    sum(data_ms[k][1] for k in data_ms),
    sum(data_ms[k][2] for k in data_ms),
    sum(data_ms[k][3] for k in data_ms),
    sum(data_ms[k][4] for k in data_ms),
])

# ----- Plot -----
fig, ax = plt.subplots(figsize=(7.2, 4.6))
x = np.arange(len(platforms))
bottoms = np.zeros(len(platforms))

component_order = ["Per-event gen", "Parse→Torch", "Model forward", "Gen+features", "Head forward"]

for comp in component_order:
    heights = np.array(data_ms[comp], dtype=float)
    xs, hs, bs = [], [], []
    for i, h in enumerate(heights):
        if h > 0:
            xs.append(x[i]); hs.append(h); bs.append(bottoms[i])
            bottoms[i] += h
    if xs:
        ax.bar(
            xs, hs, bottom=bs, label=comp,
            color=colors[comp],
        )

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(platforms)
ax.set_ylabel("Latency per inference [ms]")

ax.yaxis.grid(True, which="both", linestyle=":", linewidth=0.6, alpha=0.7)
ax.set_axisbelow(True)

ymin = 1e-5  # ms
ymax = float(totals.max() * 40 if totals.max() > 0 else 1)
ax.set_ylim(ymin, ymax)

for xi, tot in zip(x, totals):
    ax.text(xi, tot, f"{tot:.3g} ms", ha="center", va="bottom", fontsize=11)

ax.legend(ncol=2, fontsize=11, frameon=False, handlelength=1.6, handletextpad=0.6)

# ---- Add vertical arrow from FPGA top to GPU-MAXN top at the center of FPGA ----
idx_fpga = platforms.index("FPGA")
idx_gpu_maxn = platforms.index("GPU-MAXN")

x_fpga = x[idx_fpga]
y_fpga = totals[idx_fpga]  # small offset above bar
y_gpu = totals[idx_gpu_maxn]

# Arrow
ax.annotate(
    "", xy=(x_fpga, y_gpu), xytext=(x_fpga, y_fpga  + 0.01),
    arrowprops=dict(arrowstyle="<->", linewidth=2, color="black")
)

# Multiplicative speedup factor (GPU / FPGA)
factor = y_gpu / y_fpga if y_fpga > 0 else np.nan
y_mid = np.sqrt(y_fpga * y_gpu) if (y_fpga > 0 and y_gpu > 0) else (y_fpga + y_gpu) / 2.0

# Use thousands separators and no decimals; add exclamation for emphasis
label = f"× {factor:,.0f}!" if np.isfinite(factor) else "× ?"

ax.text(
    x_fpga + 0.22, y_mid,
    label,
    va="center", ha="left", fontsize=15, rotation=90
)

fig.tight_layout()

# change axis text size
ax.tick_params(axis='x', labelsize=11)
ax.tick_params(axis='y', labelsize=11)

# change axis label size
ax.yaxis.label.set_size(14)

svg_path = "media/latency_stacked_log.svg"
fig.savefig(svg_path, bbox_inches="tight")