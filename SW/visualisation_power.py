import matplotlib.pyplot as plt
import numpy as np

# Force subplots to use a wider-than-tall figsize (overrides explicit figsize if present)
_original_subplots = plt.subplots
def _wide_subplots(*args, **kwargs):
    wide_figsize = (12, 4)  # wider than tall
    if 'figsize' in kwargs:
        kwargs['figsize'] = wide_figsize
    elif len(args) >= 1 and isinstance(args[0], tuple):
        args = (wide_figsize,) + args[1:]
    return _original_subplots(*args, **kwargs)
plt.subplots = _wide_subplots

# Power consumption data (means, parentheses are peaks - not plotted here)
platforms = ["CPU-10W", "GPU-10W", "CPU-MAXN", "GPU-MAXN", "FPGA"]
models = ["Cls Tiny", "Cls Base", "KWS"]

# Average power consumption in W
data = {
    "Cls Tiny": {
        "CPU-10W": 3.881,
        "GPU-10W": 3.442,
        "CPU-MAXN": 8.191,
        "GPU-MAXN": 4.229,
        "FPGA": 1.08,  # not provided (using same as Rec Base)
    },
    "Cls Base": {
        "CPU-10W": 3.838,
        "GPU-10W": 3.919,
        "CPU-MAXN": 8.182,
        "GPU-MAXN": 5.222,
        "FPGA": 1.08,
    },
    "KWS": {
        "CPU-10W": 3.922,
        "GPU-10W": 4.050,
        "CPU-MAXN": 8.235,
        "GPU-MAXN": 5.529,
        "FPGA": 1.184,
    },
}

# Plot grouped bars
x = np.arange(len(platforms))
width = 0.25

fig, ax = plt.subplots(figsize=(9, 5))

offsets = {
    "Cls Tiny": width,
    "Cls Base": 0,
    "KWS": -width,
}

colors = {
    "Cls Tiny": "#7CD66B", # teal
    "Cls Base": "#F5B15A", # orange
    "KWS": "#65DBE0",      # green
}

for model in models:
    vals = [data[model].get(p, None) for p in platforms]
    ax.bar(
        x + offsets[model],
        [v if v is not None else 0 for v in vals],
        width,
        label=model,
        color=colors[model],
        # edgecolor="black",
        # linewidth=0.6,
    )
    # Annotate values
    for xi, v in zip(x + offsets[model], vals):
        if v is not None:
            ax.text(xi, v + 0.1, f"{v:.2f}", ha="center", va="bottom", fontsize=12)

ax.set_ylabel("Power consumption [W]")
ax.set_xticks(x)
ax.set_xticklabels(platforms, rotation=20)
ax.legend(frameon=False, ncol=3, fontsize=12)
ax.yaxis.grid(True, linestyle=":", linewidth=0.6, alpha=0.7)
ax.set_ylim(0, 9)
fig.tight_layout()

# change text size for x and y labels
ax.xaxis.label.set_size(14)
ax.yaxis.label.set_size(14)

svg_path = "media/power_consumption_bar.svg"
fig.savefig(svg_path, bbox_inches="tight")