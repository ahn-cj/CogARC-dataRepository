"""Render the correct solution and each common error as a grid image.

For every problem, writes one panel figure showing the correct output beside
each qualifying common error, annotated with how many people submitted it and
whether its status changed from the published analysis. Individual grids are
also written separately so they can be dropped into slides.

Output layout::

    outputs/figures/common_error_grids/
        <task>/
            <task>_correct.png
            <task>_top_cluster_1.png
            ...
        _panels/
            <task>.png            one row: correct + each common error
        _index.csv
"""

from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm

from . import paths
from .common_errors import find_common_errors, load_success_grids

# The ten ARC colours, in value order 0-9.
ARC_COLORS = [
    "#2b2b2b",  # 0 background
    "#0074D9",  # 1 blue
    "#FF4136",  # 2 red
    "#2ECC40",  # 3 green
    "#FFDC00",  # 4 yellow
    "#AAAAAA",  # 5 grey
    "#F012BE",  # 6 fuchsia
    "#FF851B",  # 7 orange
    "#7FDBFF",  # 8 teal
    "#870C25",  # 9 brown
]
CMAP = ListedColormap(ARC_COLORS)
NORM = BoundaryNorm(range(11), CMAP.N)

OUT = paths.FIGURES / "common_error_grids"


def grid_shapes() -> dict[str, tuple[int, int]]:
    """Rows and columns per problem, read from any submitted grid."""
    shapes = {}
    for task_dir in sorted(paths.SUBMISSIONS.iterdir()):
        if not task_dir.is_dir():
            continue
        task = task_dir.name.replace(".json", "")
        for f in task_dir.iterdir():
            if f.suffix != ".json":
                continue
            try:
                data = json.load(open(f))["grid_data"]
            except (OSError, json.JSONDecodeError, KeyError):
                continue
            shapes[task] = (len(data), len(data[0]))
            break
    return shapes


def _reshape(flat, shape):
    rows, cols = shape
    if len(flat) != rows * cols:
        return None
    return np.array(flat, dtype=int).reshape(rows, cols)


def _pretty(label: str) -> str:
    """error_2 -> Error 2."""
    return label.replace("error_", "Error ") if label else ""


def _draw(ax, grid, title=None, subtitle=None):
    ax.imshow(grid, cmap=CMAP, norm=NORM, interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, grid.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, grid.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.5, alpha=0.35)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#888888")
        spine.set_linewidth(0.8)
    if title:
        ax.set_title(title, fontsize=10, pad=6)
    if subtitle:
        ax.set_xlabel(subtitle, fontsize=7.5, labelpad=5,
                      color="#444444", linespacing=1.5)


def render_all(write_individual: bool = True) -> "list[dict]":
    cor = find_common_errors()
    pub = find_common_errors()
    success = load_success_grids()
    shapes = grid_shapes()

    pub_status = {
        (r["task"], r["grid"]): bool(r["qualifies"]) for _, r in pub.iterrows()
    }
    pub_label = {(r["task"], r["grid"]): r["error"] for _, r in pub.iterrows()}

    (OUT / "_panels").mkdir(parents=True, exist_ok=True)
    index = []

    for task in sorted(success):
        shape = shapes.get(task)
        if shape is None:
            continue

        correct = _reshape(success[task], shape)
        errors = cor[(cor["task"] == task) & cor["qualifies"]].sort_values("error")

        panels = [("correct", correct, "Correct", None)]
        for _, r in errors.iterrows():
            g = _reshape(r["grid"], shape)
            if g is None:
                continue
            key = (task, r["grid"])
            was = pub_status.get(key)
            if was is None:
                note = "new: not a published candidate"
            elif not was:
                note = f"newly qualifying (was {pub_label[key]}, below threshold)"
            elif pub_label[key] != r["error"]:
                note = f"relabelled from {_pretty(pub_label[key])}"
            else:
                note = "unchanged"
            panels.append(
                (r["error"], g, _pretty(r["error"]),
                 f"n = {int(r['n_participants'])}\n{note}")
            )
            index.append(
                {
                    "task": task,
                    "error": _pretty(r["error"]),
                    "n_participants": int(r["n_participants"]),
                    "published_label": pub_label.get(key),
                    "published_qualified": was,
                    "note": note,
                    "file": f"{task}/{task}_{_pretty(r['error'])}.png",
                }
            )

        # --- panel figure -------------------------------------------------
        n = len(panels)
        fig, axes = plt.subplots(1, n, figsize=(2.7 * n, 3.6))
        if n == 1:
            axes = [axes]
        for ax, (_, grid, title, sub) in zip(axes, panels):
            _draw(ax, grid, title, sub)
        ncommon = n - 1
        fig.suptitle(
            f"{task}   —   {ncommon} common error"
            f"{'' if ncommon == 1 else 's'}",
            fontsize=11, y=0.99,
        )
        fig.savefig(OUT / "_panels" / f"{task}.png", dpi=150,
                    facecolor="white", bbox_inches="tight")
        plt.close(fig)

        # --- individual grids ---------------------------------------------
        if write_individual:
            task_dir = OUT / task
            task_dir.mkdir(parents=True, exist_ok=True)
            for name, grid, title, sub in panels:
                fig, ax = plt.subplots(figsize=(3.4, 3.8))
                _draw(ax, grid, f"{task}  {title}", sub)
                fig.savefig(task_dir / f"{task}_{name}.png", dpi=150,
                            facecolor="white", bbox_inches="tight")
                plt.close(fig)

    return index


if __name__ == "__main__":
    import pandas as pd

    index = render_all()
    df = pd.DataFrame(index)
    df.to_csv(OUT / "_index.csv", index=False)

    print(f"rendered {df['task'].nunique()} problems, {len(df)} common-error grids")
    print(f"  panels:      {OUT / '_panels'}")
    print(f"  individual:  {OUT}/<task>/")
    print(f"  index:       {OUT / '_index.csv'}\n")
    print("grids by provenance")
    print(df["note"].value_counts().to_string())
