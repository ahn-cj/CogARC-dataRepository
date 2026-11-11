"""Figures 5 and 6, in the style of the submitted manuscript.

Layout, palette, and labelling follow the published figures; only the data
behind them is new. Colours were sampled from the images embedded in
``Caroline_Ahn_MS_Jul16_noTC.docx``.

Figure 5  A completed trials, binned · B accuracy · C deliberation time
Figure 6  A distribution of mean difficulty · B per-problem composition of
          difficulty scores · C correlation of task features with difficulty
Figure 7  A deliberation time by trial order · B difficulty by trial order ·
          C per-participant regression coefficients

SVG output keeps text as text (``svg.fonttype = "none"``) so every label stays
selectable and editable in Illustrator. Fonts are named rather than converted
to outlines, so the file renders with whatever Helvetica or Arial the opening
application resolves.

One departure from the published figure: panel 6C plots Spearman rather than
Pearson correlations. Two of the measures are strongly right-skewed, and for
normalized extra steps the Pearson coefficient understates a real monotonic
relationship (r = .02 against rho = .42). The axis label states which
coefficient is shown.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from . import paths
from .correlates import build as build_correlates
from .descriptives import difficulty_score, participant_summary

# --- palette sampled from the published figures ----------------------------
VIRIDIS_BARS = ["#46327e", "#3f4a8a", "#386e83", "#2c8580",
                "#35a778", "#6cbe6f", "#a3c845"]
BLUE_FILL, BLUE_EDGE = "#4178ab", "#202e64"
PINK_FILL, PINK_EDGE = "#ef5793", "#be1f3d"
GREEN_FILL, GREEN_EDGE = "#76b576", "#1c5b2d"
DASH = "#28418c"          # median / mean reference line
INK = "#262626"

# Difficulty score 1-4, panel 6B
SCORE_COLORS = ["#73be52", "#4178ab", "#f2d64b", "#f59ba8"]

plt.rcParams.update({
    "svg.fonttype": "none",        # keep text editable in Illustrator
    "pdf.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": INK,
    "axes.linewidth": 1.0,
    "axes.labelcolor": INK,
    "axes.labelsize": 14.5,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.labelsize": 12.5,
    "ytick.labelsize": 12.5,
    "font.size": 13,
    "legend.frameon": True,
    "legend.fontsize": 11.5,
    "axes.grid": False,
    "figure.dpi": 150,
})


def _panel_letter(ax, letter, x=-0.18, y=1.06):
    """Plain capital, upper left, outside the axes -- as published.

    Registers the letter for repositioning by ``place_panel_letters``; the
    coordinates here are only a fallback for figures that do not call it.
    """
    t = ax.text(x, y, letter, transform=ax.transAxes, fontsize=18,
                color="black", va="top", ha="left")
    ax.figure._panel_letters = getattr(ax.figure, "_panel_letters", [])
    ax.figure._panel_letters.append((ax, t))
    return t


def place_panel_letters(fig, gap_x_pt=18.0, gap_y_pt=16.0):
    """Set each panel letter clear of its axes, above and to the left.

    An axes' tight bounding box includes its tick labels and axis title, so
    anchoring to it keeps every letter clear of the y-label regardless of how
    long that label is, and lines the letters up with each other.

    The gaps are the space between the letter and the panel, in points: the
    letter's right edge sits ``gap_x_pt`` to the left of the panel and its
    bottom edge ``gap_y_pt`` above it. Measuring from the letter's own edges
    rather than its anchor keeps the spacing even whatever the glyph's width.
    """
    letters = getattr(fig, "_panel_letters", None)
    if not letters:
        return
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    dpi = fig.dpi
    for ax, text in letters:
        text.set_transform(fig.transFigure)
        text.set_va("bottom")
        text.set_ha("left")
        text.set_visible(False)                 # exclude it from the bbox
        bb = ax.get_tightbbox(renderer)
        text.set_visible(True)
        size = text.get_window_extent(renderer)
        x = bb.x0 - gap_x_pt / 72.0 * dpi - size.width
        y = bb.y1 + gap_y_pt / 72.0 * dpi
        text.set_position(inv.transform((x, y)))


def _box(ax):
    """All four spines, as in the published figures."""
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(True)


# --- Figure 5 ---------------------------------------------------------------

def _breathe(ax, side=0.012, top=1.09):
    """Leave air around the data.

    Bars drawn to the axes edge read as though they were clipped. ``side``
    is the padding on each side as a fraction of the x range; ``top`` lifts
    the upper limit above the tallest bar.
    """
    x0, x1 = ax.get_xlim()
    pad = (x1 - x0) * side
    ax.set_xlim(x0 - pad, x1 + pad)
    y0, y1 = ax.get_ylim()
    ax.set_ylim(y0, y1 * top if y0 == 0 else y0 + (y1 - y0) * top)


def figure_5(people: pd.DataFrame, sample: pd.DataFrame) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(15.6, 4.1))

    # A. completed trials, in the published bins
    ax = axes[0]
    _box(ax)
    edges = [10, 20, 30, 40, 50, 60, 70, 76]
    labels = ["10- 20", "20- 30", "30- 40", "40- 50",
              "50- 60", "60- 70", "70- 75"]
    counts, _ = np.histogram(people["n_attempted"], bins=edges)
    ax.bar(range(len(counts)), counts, color=VIRIDIS_BARS, width=.85,
           edgecolor="none")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("# of Completed Trials")
    ax.set_ylabel("# of Participants")
    _panel_letter(ax, "A")

    # B. accuracy
    ax = axes[1]
    _box(ax)
    acc = people["accuracy"] * 100
    ax.hist(acc, bins=np.arange(10, 102.5, 2.5), color=BLUE_FILL,
            edgecolor=BLUE_EDGE, linewidth=.8)
    ax.axvline(acc.median(), color=DASH, linewidth=2, linestyle=(0, (5, 3)))
    ax.set_xlabel("Accuracy (%)")
    ax.set_ylabel("# of Participants")
    _panel_letter(ax, "B")

    # C. deliberation time, log scale
    ax = axes[2]
    _box(ax)
    d = sample.loc[sample["deliberation_ok"], "deliberation_time"] / 1000
    d = d[d > 0]
    ax.hist(d, bins=np.logspace(np.log10(d.min()), np.log10(d.max()), 40),
            color=PINK_FILL, edgecolor=PINK_EDGE, linewidth=.8)
    ax.axvline(d.median(), color=DASH, linewidth=2, linestyle=(0, (5, 3)))
    ax.set_xscale("log")
    ax.set_xlabel("Deliberation Time (s, log scale)")
    ax.set_ylabel("Trials")
    _panel_letter(ax, "C")

    fig.tight_layout(w_pad=3.2)
    return fig


# --- Figure 6 ---------------------------------------------------------------

FEATURES = [
    ("complexity", "Complexity rating"),
    ("deliberation_median", "Mean deliberation time"),
    ("edit_similarity", "Pairwise Jaccard similarity"),
    ("norm_extra_steps", "Normalized extra steps"),
    ("test_output_size", "Test grid size"),
    ("num_test_colors", "# of colors used"),
    ("levenshtein", "Minimum # of edits"),
]


def _stars(p: float) -> str:
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


def figure_6(df: pd.DataFrame, sample: pd.DataFrame) -> plt.Figure:
    # A and B read as cramped when the row is narrow and C takes half the
    # figure, so the figure is wider and the two rows closer in height.
    fig = plt.figure(figsize=(13.6, 10.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[.88, 1.2], hspace=.30, wspace=.28)

    # A. distribution of mean difficulty across problems
    ax = fig.add_subplot(gs[0, 0])
    _box(ax)
    ax.hist(df["difficulty"], bins=np.arange(1.0, 4.05, .1),
            color=GREEN_FILL, edgecolor=GREEN_EDGE, linewidth=.8)
    ax.axvline(df["difficulty"].mean(), color=DASH, linewidth=2,
               linestyle=(0, (5, 3)))
    ax.set_xlim(1, 4)
    ax.set_xlabel("Mean Difficulty Score")
    ax.set_ylabel("# of Problems")
    _breathe(ax)
    _panel_letter(ax, "A", x=-0.20)

    # B. per-problem composition, ordered by the share solved first time
    ax = fig.add_subplot(gs[0, 1])
    _box(ax)
    s = sample.copy()
    s["score"] = difficulty_score(s)
    comp = (
        s.pivot_table(index="trial", columns="score", values="person_id",
                      aggfunc="count")
        .reindex(columns=[1.0, 2.0, 3.0, 4.0])
        .fillna(0)
    )
    comp = comp.loc[comp[1.0].sort_values().index]
    x = np.arange(len(comp))
    bottom = np.zeros(len(comp))
    for i, score in enumerate([1.0, 2.0, 3.0, 4.0]):
        ax.bar(x, comp[score].values, bottom=bottom, width=1.0,
               color=SCORE_COLORS[i], edgecolor="white", linewidth=.4,
               label=str(int(score)))
        bottom += comp[score].values
    ax.set_xlim(-.5, len(comp) - .5)
    ax.set_xticks([])
    ax.set_xlabel("Problems")
    ax.set_ylabel("# of Subjects")
    _breathe(ax)
    leg = ax.legend(title="Difficulty Score", loc="lower right", fontsize=10,
                    title_fontsize=10, framealpha=.92, borderpad=.6)
    leg.get_frame().set_edgecolor("#cccccc")
    _panel_letter(ax, "B", x=-0.20)

    # C. correlation of task features with difficulty
    ax = fig.add_subplot(gs[1, :])
    _box(ax)
    rows = []
    for col, label in FEATURES:
        sub = df[["difficulty", col]].dropna()
        rho, p = stats.spearmanr(sub["difficulty"], sub[col])
        rows.append((label, rho, p))

    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    ax.bar(range(len(vals)), vals, color=BLUE_FILL, width=.72, edgecolor="none")
    ax.axhline(0, color="black", linewidth=1.2, linestyle=(0, (5, 3)))

    for i, (_, rho, p) in enumerate(rows):
        star = _stars(p)
        if not star:
            continue
        offset = .035 if rho >= 0 else -.035
        ax.text(i, rho + offset, star, ha="center",
                va="bottom" if rho >= 0 else "top", fontsize=14, color="black")

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Spearman correlation with difficulty score")
    ax.set_xlabel("Task features and measures")
    lim = max(abs(min(vals)), abs(max(vals))) + .18
    ax.set_ylim(-lim, lim)
    _panel_letter(ax, "C", x=-0.09, y=1.05)

    return fig


# --- Figure 7 ---------------------------------------------------------------

def _weighted_mean(slopes: "pd.DataFrame", col: str) -> float:
    """Inverse-variance weighted mean of the per-participant slopes.

    The same estimator the text reports. Each slope is weighted by 1/SE^2
    plus the between-participant variance, so a slope from a short session
    counts for less than one from a full session.
    """
    v = slopes[[col, col + "_se"]].rename(columns={col + "_se": "se"}).dropna()
    v = v[v["se"] > 0]
    if not len(v):
        return float(slopes[col].dropna().mean())
    w = 1/v["se"]**2
    fe = (w*v[col]).sum()/w.sum()
    q = (w*(v[col]-fe)**2).sum()
    dfree = len(v)-1
    c = w.sum() - (w**2).sum()/w.sum()
    tau2 = max(0.0, (q-dfree)/c) if c > 0 else 0.0
    w2 = 1/(v["se"]**2 + tau2)
    return float((w2*v[col]).sum()/w2.sum())


def figure_7(by_order: "pd.DataFrame", slopes: "pd.DataFrame") -> plt.Figure:
    """Change over the session, in the published three-panel layout.

    Panel C plots the log-scale deliberation coefficient. On the raw scale a
    participant's fit is dominated by their few slowest trials: the raw slopes
    have four times the coefficient of variation of the log slopes, which is
    why the raw-scale group test reaches only t = -4.7 against t = -12.4 on the
    log scale. The direction is the same either way.
    """
    fig = plt.figure(figsize=(12.4, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.15], hspace=.62, wspace=.44)

    # A. deliberation time by trial order
    ax = fig.add_subplot(gs[0, 0])
    _box(ax)
    # Median rather than mean: at a given trial position the mean is pulled
    # around by a handful of very slow trials, which adds scatter without
    # changing the trend.
    ax.scatter(by_order.index, by_order["deliberation_median_s"], s=22,
               color=PINK_FILL, edgecolor="none")
    ax.set_xlabel("Trial Order")
    ax.set_ylabel("Deliberation Time (s, median)")
    _panel_letter(ax, "A", x=-0.22)

    # B. difficulty by trial order
    ax = fig.add_subplot(gs[1, 0])
    _box(ax)
    ax.scatter(by_order.index, by_order["difficulty"], s=22,
               color=BLUE_FILL, edgecolor="none")
    ax.set_xlabel("Trial Order")
    ax.set_ylabel("Difficulty Score")
    _panel_letter(ax, "B", x=-0.22)

    # C. per-participant coefficients
    # Panel C gives each variable its own axis. The two slopes are not on a
    # comparable scale: difficulty score takes values 1 to 4, so across a
    # 75-trial session its slope cannot exceed about 0.04, while the log
    # deliberation slope has no such bound. Sharing one axis made the
    # difficulty slopes look like a flat line at zero.
    import seaborn as sns
    from matplotlib.gridspec import GridSpecFromSubplotSpec

    inner = GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[:, 1], wspace=0.55)
    panels = [("Deliberation time", "deliberation_slope_log", PINK_FILL,
               "Coefficient (log s per trial)"),
              ("Difficulty score", "difficulty_slope", BLUE_FILL,
               "Coefficient (points per trial)")]
    for i, (label, col, color, ylab) in enumerate(panels):
        ax = fig.add_subplot(inner[0, i])
        _box(ax)
        vals = slopes[col].dropna()
        ax.axhline(0, color="#999999", linewidth=1.4, linestyle=(0, (5, 4)),
                   zorder=1)
        sns.swarmplot(y=vals, color=color, size=4.2, ax=ax, zorder=3)
        # The diamond is the inverse-variance weighted mean, which is the
        # estimate reported in the text; an unweighted mean would give a
        # 17-trial session the same influence as a 75-trial one.
        ax.scatter([0], [_weighted_mean(slopes, col)], marker="D", s=42,
                   color="black", edgecolor="white", linewidth=.8, zorder=5)
        ax.set_xlabel(label)
        ax.set_ylabel(ylab)
        ax.set_xticks([])
        if i == 0:
            _panel_letter(ax, "C", x=-0.30, y=1.03)

    return fig


def _save(fig, name):
    place_panel_letters(fig)
    fig.savefig(paths.FIGURES / f"{name}.svg", bbox_inches="tight",
                pad_inches=0.28, facecolor="white")
    fig.savefig(paths.FIGURES / f"{name}.png", dpi=300, bbox_inches="tight",
                pad_inches=0.28, facecolor="white")
    plt.close(fig)


# --- Figure 4: Experiment 1 -------------------------------------------------

def figure_4(exp1: "pd.DataFrame") -> plt.Figure:
    """Experiment 1, in the published seven-panel layout.

    Panel D reports Spearman alongside Pearson: deliberation time is
    right-skewed here as in Experiment 2, and the two coefficients differ
    enough to matter (.43 against .54).
    """
    from scipy import stats as st

    from .experiment1 import participant_summary, problem_summary

    people = participant_summary(exp1)
    problems = problem_summary(exp1)

    fig = plt.figure(figsize=(11.4, 17))
    gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1.25, 1],
                          hspace=.78, wspace=.44)

    # A. accuracy
    ax = fig.add_subplot(gs[0, 0])
    _box(ax)
    acc = people["accuracy"] * 100
    ax.hist(acc, bins=np.arange(55, 102.5, 2.5), color=BLUE_FILL,
            edgecolor=BLUE_EDGE, linewidth=.8)
    ax.axvline(acc.median(), color=DASH, linewidth=2, linestyle=(0, (5, 3)))
    ax.set_xlabel("Accuracy (%)")
    ax.set_ylabel("# of Participants")
    _panel_letter(ax, "A", x=-0.20)

    # B. deliberation time
    ax = fig.add_subplot(gs[0, 1])
    _box(ax)
    d = exp1.loc[exp1["deliberation_ok"], "deliberation_time"] / 1000
    d = d[d > 0]
    ax.hist(d, bins=np.logspace(np.log10(d.min()), np.log10(d.max()), 40),
            color=PINK_FILL, edgecolor=PINK_EDGE, linewidth=.8)
    ax.axvline(d.median(), color=DASH, linewidth=2, linestyle=(0, (5, 3)))
    ax.set_xscale("log")
    ax.set_xlabel("Deliberation Time (s, log scale)")
    ax.set_ylabel("Trials")
    _panel_letter(ax, "B", x=-0.20)

    # C. difficulty distribution
    ax = fig.add_subplot(gs[1, 0])
    _box(ax)
    ax.hist(problems["difficulty"], bins=np.arange(1.0, 4.05, .1),
            color=GREEN_FILL, edgecolor=GREEN_EDGE, linewidth=.8)
    ax.axvline(problems["difficulty"].mean(), color=DASH, linewidth=2,
               linestyle=(0, (5, 3)))
    ax.set_xlim(1, 4)
    ax.set_xlabel("Difficulty Score")
    ax.set_ylabel("# of Problems")
    _breathe(ax)
    _panel_letter(ax, "C", x=-0.20)

    # D. difficulty against deliberation time
    ax = fig.add_subplot(gs[1, 1])
    _box(ax)
    x = problems["deliberation_median_s"]
    y = problems["difficulty"]
    ok = x.notna() & y.notna()
    x, y = x[ok], y[ok]
    b, a = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 100)
    resid = y - (a + b * x)
    se = resid.std() * np.sqrt(1 / len(x) + (xs - x.mean()) ** 2 /
                               ((x - x.mean()) ** 2).sum())
    ax.fill_between(xs, a + b * xs - 1.96 * se, a + b * xs + 1.96 * se,
                    color=PINK_FILL, alpha=.22, linewidth=0)
    ax.plot(xs, a + b * xs, color=PINK_EDGE, linewidth=1.8)
    ax.scatter(x, y, s=16, color=PINK_FILL, edgecolor="none", zorder=3)
    rho, p_s = st.spearmanr(x, y)
    r, p_p = st.pearsonr(x, y)
    ax.text(.04, .96, f"ρ = {rho:.3f}\n(r = {r:.3f})\np < .001",
            transform=ax.transAxes, va="top", ha="left", fontsize=10,
            linespacing=1.4,
            bbox=dict(boxstyle="square,pad=0.4", facecolor="white",
                      edgecolor=INK, linewidth=.8))
    ax.set_xlabel("Deliberation Time (s, median)")
    ax.set_ylabel("Difficulty Score")
    _panel_letter(ax, "D", x=-0.20)

    # E. per-problem composition of difficulty scores
    ax = fig.add_subplot(gs[2, :])
    _box(ax)
    comp = (
        exp1.pivot_table(index="trial", columns="difficulty", values="subject",
                         aggfunc="count")
        .reindex(columns=[1.0, 2.0, 3.0, 4.0])
        .fillna(0)
    )
    comp = comp.loc[comp[1.0].sort_values().index]
    bottom = np.zeros(len(comp))
    for i, score in enumerate([1.0, 2.0, 3.0, 4.0]):
        ax.bar(np.arange(len(comp)), comp[score].values, bottom=bottom,
               width=1.0, color=SCORE_COLORS[i], edgecolor="white",
               linewidth=.4, label=str(int(score)))
        bottom += comp[score].values
    ax.set_xlim(-.5, len(comp) - .5)
    ax.set_xticks([])
    ax.set_xlabel("Problems")
    ax.set_ylabel("# of Participants")
    # Bars stop short of 39 where fewer participants reached the problem:
    # Experiment 1 presented the problems in a fixed order, so the later ones
    # were attempted by fewer people. The gap is information, not a defect.
    # The axis runs a little past 39 so a full bar does not touch the frame.
    ax.set_ylim(0, exp1["subject"].nunique() * 1.08)
    ax.set_xlim(-2.0, len(comp) + 1.0)
    leg = ax.legend(title="Difficulty Score", loc="lower right", fontsize=10,
                    title_fontsize=10, framealpha=.92, borderpad=.6)
    leg.get_frame().set_edgecolor("#cccccc")
    _panel_letter(ax, "E", x=-0.09)

    # F. core knowledge category
    from .descriptives import task_properties
    props = task_properties()
    merged = problems.join(props, how="left")

    ax = fig.add_subplot(gs[3, 0])
    _box(ax)
    order = ["Obj", "Geo", "Num", "GoD"]
    data = [merged.loc[merged["core_knowledge"] == c, "difficulty"].dropna()
            for c in order]
    bp = ax.boxplot(data, patch_artist=True, widths=.6,
                    flierprops=dict(marker="D", markersize=4,
                                    markerfacecolor="black",
                                    markeredgecolor="black"),
                    medianprops=dict(color="black", linewidth=1.2),
                    boxprops=dict(facecolor=BLUE_FILL, edgecolor="black",
                                  linewidth=.9),
                    whiskerprops=dict(color="black", linewidth=.9),
                    capprops=dict(color="black", linewidth=.9))
    ax.set_xticklabels(order)
    # Difficulty starts at 1, so a whisker reaching the floor would be drawn
    # on the axis itself.
    ax.set_ylim(0.92, 4.08)
    ax.set_xlabel("Main Core knowledge category")
    ax.set_ylabel("Difficulty score")
    _panel_letter(ax, "F", x=-0.20)

    # G. rated complexity, with pairwise brackets
    ax = fig.add_subplot(gs[3, 1])
    _box(ax)
    levels = [1, 2, 3]
    data = [merged.loc[merged["complexity"] == lv, "difficulty"].dropna()
            for lv in levels]
    ax.boxplot(data, patch_artist=True, widths=.6,
               flierprops=dict(marker="D", markersize=4,
                               markerfacecolor="black",
                               markeredgecolor="black"),
               medianprops=dict(color="black", linewidth=1.2),
               boxprops=dict(facecolor=GREEN_FILL, edgecolor="black",
                             linewidth=.9),
               whiskerprops=dict(color="black", linewidth=.9),
               capprops=dict(color="black", linewidth=.9))
    ax.set_xticklabels([str(v) for v in levels])
    ax.set_ylim(0.92, 4.9)
    ax.set_xlabel("Level of Complexity")
    ax.set_ylabel("Difficulty Score")

    from .correlates import _benjamini_hochberg
    from itertools import combinations
    raw, pairs = [], []
    for i, j in combinations(range(3), 2):
        raw.append(st.ttest_ind(data[i], data[j], equal_var=False).pvalue)
        pairs.append((i, j))
    fdr = _benjamini_hochberg(raw)

    # Stack only the brackets actually drawn, so a non-significant pair does
    # not leave a gap and the remaining brackets stay clear of each other.
    y0, step, drawn = 3.62, .40, 0
    for (i, j), p in zip(pairs, fdr):
        star = _stars(p)
        if not star:
            continue
        yb = y0 + drawn * step
        ax.plot([i + 1, i + 1, j + 1, j + 1],
                [yb, yb + .10, yb + .10, yb], color="black", linewidth=1)
        ax.text((i + j) / 2 + 1, yb + .13, star, ha="center", va="bottom",
                fontsize=13)
        drawn += 1
    _panel_letter(ax, "G", x=-0.20)

    return fig


# --- Supplementary Figure 1: Experiment 1 replication -----------------------

# Success, then the three Experiment 2 common errors in rank order, then
# everything else. Sampled from the published supplementary figure.
SOLUTION_COLORS = ["#73be52", "#4178ab", "#f2d64b", "#a0715c", "#7b6bb0",
                   "#e08a3c", "#f59ba8"]
SOLUTION_LABELS = ["Success", "Most Common Error", "Second Most Common Error",
                   "Third Most Common Error", "Fourth Most Common Error",
                   "Fifth Most Common Error", "Miscellaneous"]
N_ERROR_SLOTS = len(SOLUTION_LABELS) - 2      # Success and Miscellaneous aside


# Supp. Figure 1 is the inclusion flowchart, which is built outside this
# repository; the numbers below follow the manuscript, not the order the
# functions were written in.
def supp_figure_1() -> plt.Figure:
    """Do the Experiment 2 common errors recur in Experiment 1?

    Each first-attempt submission in Experiment 1 is matched against the
    correct grid and against the Experiment 2 common errors for that problem,
    so the figure shows how far the shared errors of one sample recur in the
    other.
    """
    from .common_errors import find_common_errors, load_success_grids
    from .experiment1 import load_submissions

    exp2 = find_common_errors()
    exp2 = exp2[exp2["qualifies"]]
    by_task = {}
    for r in exp2.itertuples():
        by_task.setdefault(r.task, {})[r.error] = r.grid

    success = load_success_grids()
    subs = load_submissions()

    rows = []
    for task, block in subs.groupby("task"):
        correct = success.get(task)
        errs = by_task.get(task, {})
        counts = [0] * len(SOLUTION_LABELS)
        for g in block["grid"]:
            if correct is not None and g == correct:
                counts[0] += 1
                continue
            slot = next((k for k in range(1, N_ERROR_SLOTS + 1)
                         if errs.get(f"error_{k}") == g), None)
            counts[slot if slot else len(SOLUTION_LABELS) - 1] += 1
        rows.append({"task": task,
                     **{SOLUTION_LABELS[i]: counts[i]
                        for i in range(len(SOLUTION_LABELS))}})

    df = pd.DataFrame(rows).set_index("task")
    df = df.loc[df["Success"].sort_values().index]

    fig, ax = plt.subplots(figsize=(15, 6))
    _box(ax)
    x = np.arange(len(df))
    bottom = np.zeros(len(df))
    for label, colour in zip(SOLUTION_LABELS, SOLUTION_COLORS):
        ax.bar(x, df[label].values, bottom=bottom, width=.86, color=colour,
               edgecolor="white", linewidth=.5, label=label)
        bottom += df[label].values
    ax.set_xlim(-.6, len(df) - .4)
    ax.set_xticks([])
    _breathe(ax)
    ax.set_xlabel("Problems")
    ax.set_ylabel("# of First Attempt Solutions")
    leg = ax.legend(title="Solution Type", loc="lower right", fontsize=11,
                    title_fontsize=11, framealpha=.92, borderpad=.7)
    leg.get_frame().set_edgecolor("#cccccc")
    fig.tight_layout()
    return fig


# --- Figures 8, 10, 11 ------------------------------------------------------

# Solution-type colours, sampled from the published Figures 10 and 11.
GROUP_COLORS = {
    "Success": "#41b649",
    "Top error 1": "#1b79b6",
    "Top error 2": "#fec112",
    "Top error 3": "#e25364",
    "Top error 4": "#7b6bb0",
    "Top error 5": "#e08a3c",
    "Miscellaneous": "#f59ba8",
}

# The two problems used as case studies, identified from the published panels:
# 12eac192 matches Figure 10 (success 39, errors 18 and 15) and 1b60fb0c
# matches Figure 11 (54 correct against 71 in errors, and four solution types).
FIG10_TASK = "12eac192"
FIG11_TASK = "1b60fb0c"

# Supplementary case studies. Each figure's caption names its problem, and each
# task is confirmed by the participant counts in its panel B.
SUPP2_TASK = "12eac192"     # counting-and-coloring, vs correct outcome
SUPP3_TASK = "0e671a1a"     # path-connecting
SUPP4_TASK = "1f0c79e5"     # path-extension


def figure_8(sample: "pd.DataFrame") -> plt.Figure:
    """First-attempt solution types per problem, Experiment 2."""
    from .common_errors import find_common_errors, load_submissions, load_success_grids
    
    errors = find_common_errors()
    errors = errors[errors["qualifies"]]
    by_task = {}
    for r in errors.itertuples():
        by_task.setdefault(r.task, {})[r.error] = r.grid

    success = load_success_grids()
    subs = load_submissions(first_attempt_only=True)
    keep = set(zip(sample["subject"], sample["trial"]))
    subs = subs[[(a, b) in keep for a, b in zip(subs["subject"], subs["task"])]]

    rows = []
    for task, block in subs.groupby("task"):
        correct = success.get(task)
        errs = by_task.get(task, {})
        counts = [0] * len(SOLUTION_LABELS)
        for g in block["grid"]:
            if correct is not None and g == correct:
                counts[0] += 1
                continue
            slot = next((k for k in range(1, N_ERROR_SLOTS + 1)
                         if errs.get(f"error_{k}") == g), None)
            counts[slot if slot else len(SOLUTION_LABELS) - 1] += 1
        rows.append({"task": task,
                     **{SOLUTION_LABELS[i]: counts[i]
                        for i in range(len(SOLUTION_LABELS))}})

    df = pd.DataFrame(rows).set_index("task")
    df = df.loc[df["Success"].sort_values().index]

    fig, ax = plt.subplots(figsize=(15, 6))
    _box(ax)
    x = np.arange(len(df))
    bottom = np.zeros(len(df))
    for label, colour in zip(SOLUTION_LABELS, SOLUTION_COLORS):
        # A thin white outline separates adjacent problems, which otherwise
        # merge into a continuous band where neighbours share a colour.
        ax.bar(x, df[label].values, bottom=bottom, width=.86, color=colour,
               edgecolor="white", linewidth=.5, label=label)
        bottom += df[label].values

    # Both case-study problems are marked, so a reader can place each of
    # Figures 10 and 11 in the distribution.
    # The two case-study problems are marked with a caret above their bar.
    # A leader line and label would need a clear band above the tallest bar,
    # which costs the plot a fifth of its height; the caption names them.
    tallest = bottom.max()
    for task_id in (FIG10_TASK, FIG11_TASK):
        if task_id not in df.index:
            continue
        pos = list(df.index).index(task_id)
        ax.plot([pos], [bottom[pos] + tallest * 0.018], marker="v",
                markersize=8, color=INK, clip_on=False, zorder=6)
    ax.set_ylim(0, tallest * 1.06)

    ax.set_xlim(-.6, len(df) - .4)
    ax.set_xticks([])
    ax.set_xlabel("Problems")
    ax.set_ylabel("# of First Attempt Solutions")
    leg = ax.legend(title="Solution Type", loc="lower right", fontsize=11,
                    title_fontsize=11, framealpha=.92, borderpad=.7)
    leg.get_frame().set_edgecolor("#cccccc")
    fig.tight_layout()
    return fig


def _draw_grid(ax, grid, edge=None, lw=4):
    from .visualize_grids import CMAP, NORM

    a = np.array(grid)
    ax.imshow(a, cmap=CMAP, norm=NORM, interpolation="nearest")
    ax.set_xticks(np.arange(-.5, a.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-.5, a.shape[0], 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=.4, alpha=.3)
    ax.set_xticks([]); ax.set_yticks([])
    ax.tick_params(which="both", length=0)
    for sp in ax.spines.values():
        sp.set_visible(edge is not None)
        if edge is not None:
            sp.set_edgecolor(edge); sp.set_linewidth(lw)


def solution_figure(task: str, reference: str = "submitted",
                    show_blank: bool = True) -> plt.Figure:
    """The four-panel case-study layout used for Figures 10, 11 and Supp 2-4.

    ``reference="correct"`` measures panel C against the correct output rather
    than the participant's own submission, so only successful trajectories
    reach zero and the test-input and blank-grid levels become meaningful
    reference lines.

    ``show_blank=False`` drops the blank-grid reference lines from panel C.
    On a problem where no group starts near a blank grid the lines sit far
    below every trajectory, and the empty space they open up costs more than
    the reference is worth.
    """
    import json
    from scipy.stats import gaussian_kde

    from .trajectories import (reference_levels, solution_groups,
                               trial_trajectories)

    arc = json.load(open(paths.ARC_TASKS / f"{task}.json"))
    train = arc["train"]
    test_in = arc["test"][0]["input"]
    groups = solution_groups(task)
    traj = trial_trajectories(task, reference=reference)

    shape = (len(test_in), len(test_in[0]))
    n_ex = min(len(train), 3)
    n_groups = len(groups)

    fig = plt.figure(figsize=(10.4, 14.5))
    gs = fig.add_gridspec(4, 1, height_ratios=[1.15, .85, 1.5, 1.15],
                          hspace=.62, left=.20, right=.97, top=.955, bottom=.05)

    # A. examples and test input
    gsA = gs[0].subgridspec(2, n_ex + 1, hspace=.18, wspace=.22)
    for k in range(n_ex):
        for row, key in enumerate(("input", "output")):
            ax = fig.add_subplot(gsA[row, k])
            _draw_grid(ax, train[k][key])
            if row == 0:
                ax.set_title(f"Example #{k + 1}", fontsize=11, pad=6)
            if k == 0:
                ax.set_ylabel(key.capitalize(), fontsize=11)
    ax = fig.add_subplot(gsA[0, n_ex])
    _draw_grid(ax, test_in)
    ax.set_title("Test", fontsize=11, pad=6)
    ax = fig.add_subplot(gsA[1, n_ex])
    ax.text(.5, .5, "?", ha="center", va="center", fontsize=42)
    ax.axis("off")
    fig.text(.015, .965, "A", fontsize=17, va="top")

    # B. solution grids with counts
    gsB = gs[1].subgridspec(1, n_groups, wspace=.38)
    counts = traj["group"].value_counts() if len(traj) else {}
    for k, (name, grid) in enumerate(groups.items()):
        ax = fig.add_subplot(gsB[0, k])
        _draw_grid(ax, np.array(grid).reshape(shape),
                   edge=GROUP_COLORS.get(name, "#888888"))
        ax.set_xlabel(f"{name}\nn = {int(counts.get(name, 0))}", fontsize=11,
                      labelpad=8, linespacing=1.5)
    fig.text(.015, .715, "B", fontsize=17, va="top")

    # C. trajectories to the submitted solution
    ax = fig.add_subplot(gs[2])
    _box(ax)
    rng = np.random.default_rng(0)
    for name in groups:
        block = traj[traj["group"] == name] if len(traj) else []
        for _, r in getattr(block, "iterrows", lambda: iter([]))():
            y = np.array(r["trajectory"])
            if len(y) < 2:
                continue
            # A small vertical jitter separates otherwise identical paths.
            ax.plot(np.arange(len(y)), y + rng.uniform(-.004, .004),
                    color=GROUP_COLORS[name], linewidth=.9, alpha=.75)
    # Trajectories are scaled from the test input to the target, so the input
    # sits at 0 and the target at 1 for every trajectory. Both distances are
    # exact per solution group; rescaling puts groups that sit at different
    # raw heights onto one shared pair of reference lines.
    target_label = ("Submitted\noutput" if reference == "submitted"
                    else "Correct\nsolution")
    for level in (0, 1):
        ax.axhline(level, color="#999999", linestyle=(0, (5, 4)),
                   linewidth=1.2, zorder=1)
    ticks, labels = [0, 1], ["Input", target_label]

    # A blank grid sits at a different depth for each group, so each is drawn
    # in its own colour and labelled once.
    blanks = []
    for group, pair in (reference_levels(task, reference).items()
                        if show_blank else ()):
        span = pair["Input"]
        if span <= 0:
            continue
        level = 1 - pair["Blank"] / span
        colour = GROUP_COLORS.get(group, "#999999") if group else "#999999"
        ax.axhline(level, color=colour, linestyle=(0, (2, 3)),
                   linewidth=1.0, alpha=.8, zorder=1)
        blanks.append(level)
    if blanks:
        ticks.append(float(np.mean(blanks)))
        labels.append("Blank")
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Steps")
    ax.set_ylabel("Trajectory to Correct Solution" if reference == "correct"
                  else "Trajectory to Submitted Solution")
    handles = [plt.Line2D([], [], color=GROUP_COLORS[n], linewidth=1.6, label=n)
               for n in groups]
    leg = ax.legend(handles=handles, loc="lower right", fontsize=10,
                    framealpha=.92)
    leg.get_frame().set_edgecolor("#cccccc")
    _panel_letter(ax, "C", x=-0.155, y=1.05)

    # D. normalized extra steps by solution type
    ax = fig.add_subplot(gs[3])
    _box(ax)
    for name in groups:
        vals = traj.loc[traj["group"] == name, "norm_extra_steps"].dropna()
        if len(vals) < 3 or vals.nunique() < 2:
            continue
        kde = gaussian_kde(vals)
        xs = np.linspace(1, max(3, vals.quantile(.99)), 300)
        ax.fill_between(xs, kde(xs), color=GROUP_COLORS[name], alpha=.45,
                        linewidth=0)
        ax.plot(xs, kde(xs), color=GROUP_COLORS[name], linewidth=1.4,
                label=name)
    ax.set_xlabel("Extra steps in edit sequence relative to minimum (normalized)")
    ax.set_ylabel("Density")
    leg = ax.legend(loc="upper right", fontsize=10, framealpha=.92)
    leg.get_frame().set_edgecolor("#cccccc")
    _panel_letter(ax, "D", x=-0.155, y=1.06)

    return fig


if __name__ == "__main__":
    from .sample import load_sample, trial_level_sample

    # Two sets, by what the analysis groups on. Figures grouped by
    # participant (5, 7) use the participant-level set; figures grouped by
    # problem (6, 8, 10, 11) use the problem-level set, which keeps the
    # participants who have too few trials to carry a mean of their own.
    sample = load_sample()
    problem_sample = trial_level_sample()
    people = participant_summary(sample)
    df = build_correlates()

    print(f"figure 5: {len(people)} participants, {len(sample):,} trials")
    _save(figure_5(people, sample), "figure5_performance")

    print(f"figure 6: {len(df)} problems, "
          f"{problem_sample['person_id'].nunique()} participants")
    _save(figure_6(df, problem_sample), "figure6_difficulty")

    from .experiment1 import load_sample as load_exp1
    exp1 = load_exp1()
    print(f"figure 4: {exp1.subject.nunique()} Experiment 1 participants")
    _save(figure_4(exp1), "figure4_experiment1")

    print("figure 8")
    _save(figure_8(problem_sample), "figure8_solution_types")

    print(f"figure 10: {FIG10_TASK}")
    _save(solution_figure(FIG10_TASK), "figure10_counting_coloring")

    print(f"figure 11: {FIG11_TASK}")
    _save(solution_figure(FIG11_TASK, show_blank=False),
          "figure11_pattern_completion")

    print(f"supp figure 2: {SUPP2_TASK} (vs correct)")
    _save(solution_figure(SUPP2_TASK, reference="correct"),
          "supp_figure2_vs_correct")

    print(f"supp figure 3: {SUPP3_TASK}")
    _save(solution_figure(SUPP3_TASK), "supp_figure3_path_connecting")

    print(f"supp figure 4: {SUPP4_TASK}")
    _save(solution_figure(SUPP4_TASK), "supp_figure4_path_extension")

    print("supplementary figure 1")
    _save(supp_figure_1(), "supp_figure1_exp1_errors")

    from .trends import by_trial_order, participant_slopes
    slopes = participant_slopes(sample)
    print(f"figure 7: {slopes['difficulty_slope'].notna().sum()} participants")
    _save(figure_7(by_trial_order(sample), slopes), "figure7_trends")

    print("\npanel 6C values (Spearman):")
    for col, label in FEATURES:
        sub = df[["difficulty", col]].dropna()
        rho, p = stats.spearmanr(sub["difficulty"], sub[col])
        print(f"  {label:28s} rho = {rho:+.3f}  p = {p:.2e}  {_stars(p)}")

    print(f"\nwrote {paths.FIGURES}/figure5_performance.[svg|png]")
    print(f"wrote {paths.FIGURES}/figure6_difficulty.[svg|png]")
    print(f"wrote {paths.FIGURES}/figure7_trends.[svg|png]")
    print(f"wrote {paths.FIGURES}/figure4_experiment1.[svg|png]")
    print(f"wrote {paths.FIGURES}/supp_figure1_exp1_errors.[svg|png]")
    print(f"wrote {paths.FIGURES}/figure8_solution_types.[svg|png]")
    print(f"wrote {paths.FIGURES}/figure10_counting_coloring.[svg|png]")
    print(f"wrote {paths.FIGURES}/figure11_pattern_completion.[svg|png]")
    print(f"wrote {paths.FIGURES}/supp_figure2_vs_correct.[svg|png]")
    print(f"wrote {paths.FIGURES}/supp_figure3_path_connecting.[svg|png]")
    print(f"wrote {paths.FIGURES}/supp_figure4_path_extension.[svg|png]")
