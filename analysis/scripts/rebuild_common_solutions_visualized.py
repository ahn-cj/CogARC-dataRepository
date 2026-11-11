"""Render every grid in `Common solutions/` to `Common solutions visualized/`.

Kept in step with the JSON folder by reading it rather than recomputing, so
the two cannot disagree.
"""

import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cogarc import paths
from cogarc.visualize_grids import CMAP, NORM

src = paths.COMMON_SOLUTIONS_OUT
dst = paths.COMMON_SOLUTIONS_OUT.with_name(
    paths.COMMON_SOLUTIONS_OUT.name.replace("Common solutions", "Common solutions visualized"))
if dst.exists():
    shutil.rmtree(dst)
dst.mkdir(parents=True)

index = pd.read_csv(src / "common_solutions_index.csv").set_index(
    ["task", "solution"])

n = 0
for task_dir in sorted(src.iterdir()):
    if not task_dir.is_dir():
        continue
    out_dir = dst / task_dir.name
    out_dir.mkdir()
    for f in sorted(task_dir.glob("*.json")):
        grid = np.array(json.load(open(f))["grid_data"])
        label = f.stem.split("_", 1)[1]
        task = task_dir.name.replace(".json", "")
        try:
            k = index.loc[(task, label), "n_participants"]
            sub = "" if pd.isna(k) else f"n = {int(k)}"
        except KeyError:
            sub = ""

        fig, ax = plt.subplots(figsize=(3.2, 3.4))
        ax.imshow(grid, cmap=CMAP, norm=NORM, interpolation="nearest")
        ax.set_xticks(np.arange(-.5, grid.shape[1], 1), minor=True)
        ax.set_yticks(np.arange(-.5, grid.shape[0], 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=.5, alpha=.35)
        ax.set_xticks([]); ax.set_yticks([])
        ax.tick_params(which="both", length=0)
        for sp in ax.spines.values():
            sp.set_edgecolor("#888888"); sp.set_linewidth(.8)
        ax.set_title(f"{task}  {label}", fontsize=10, pad=6)
        if sub:
            ax.set_xlabel(sub, fontsize=9, labelpad=5, color="#444444")
        fig.savefig(out_dir / f"{f.stem}.json.png", dpi=150,
                    bbox_inches="tight", facecolor="white")
        plt.close(fig)
        n += 1

print(f"wrote {dst}")
print(f"  {n} images across {len(list(dst.iterdir()))} problems")
