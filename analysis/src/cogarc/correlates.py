"""What predicts problem difficulty (manuscript section 3.2.1, Figure 6).

Assembles one row per problem from the analysis sample, the edit-sequence
measures, and the experimenter ratings, then correlates each candidate against
mean difficulty.

Deliberation time is aggregated by median within problem. The distribution is
heavily right-skewed and one trial recorded 44 hours, so a raw mean is not
robust; the log mean is reported alongside to show the choice does not drive
the result.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import paths
from .descriptives import problem_summary, task_properties

CANDIDATES = [
    ("deliberation_median", "Deliberation time (median, s)"),
    ("deliberation_log_mean", "Deliberation time (mean of log)"),
    ("edit_similarity", "Edit sequence similarity"),
    ("complexity", "Rated rule complexity"),
    ("norm_extra_steps", "Normalized extra steps"),
    ("test_output_size", "Test grid size"),
    ("num_test_colors", "Number of colours"),
    ("levenshtein", "Edits required for correct output"),
    ("num_train_examples", "Number of examples"),
]


def build() -> pd.DataFrame:
    problems = problem_summary()

    # Built by edit_sequences, which takes about 30 seconds. Generate it on
    # demand so the modules can be run in any order from a fresh clone.
    measures = paths.TABLES / "edit_sequence_measures.csv"
    if not measures.exists():
        from .edit_sequences import (collect_edits, extra_steps_by_problem,
                                     jaccard_by_problem)

        edits_raw = collect_edits()
        pd.concat([jaccard_by_problem(edits_raw),
                   extra_steps_by_problem(edits_raw)[0]], axis=1).to_csv(measures)
    edits = pd.read_csv(measures, index_col=0)
    props = task_properties()

    df = problems.join(edits, how="left").join(props, how="left")
    df["deliberation_median_s"] = df["deliberation_median"] / 1000
    return df


def correlations(df: pd.DataFrame, target: str = "difficulty") -> pd.DataFrame:
    rows = []
    for col, label in CANDIDATES:
        if col not in df.columns:
            continue
        sub = df[[target, col]].dropna()
        if len(sub) < 3:
            continue
        r, p = stats.pearsonr(sub[target], sub[col])
        rho, p_s = stats.spearmanr(sub[target], sub[col])
        rows.append(
            {
                "measure": label,
                "column": col,
                "n": len(sub),
                "r": round(r, 3),
                "p": p,
                "rho": round(rho, 3),
                "p_spearman": p_s,
            }
        )
    out = pd.DataFrame(rows)
    # The manuscript reports Spearman for these problem-level measures, since
    # several are strongly right-skewed. Flag on the test actually reported.
    out["significant"] = out["p_spearman"] < .05
    return out.sort_values("r", key=abs, ascending=False).reset_index(drop=True)


def core_knowledge_test(df: pd.DataFrame) -> tuple:
    """One-way ANOVA of difficulty across core knowledge categories."""
    groups = [
        g["difficulty"].values
        for _, g in df.dropna(subset=["core_knowledge"]).groupby("core_knowledge")
        if len(g) > 1
    ]
    if len(groups) < 2:
        return None, None, {}
    f, p = stats.f_oneway(*groups)
    sizes = (
        df.dropna(subset=["core_knowledge"])
        .groupby("core_knowledge")["difficulty"]
        .agg(["size", "mean"])
        .round(3)
    )
    return f, p, sizes


def complexity_pairwise(df: pd.DataFrame) -> pd.DataFrame:
    """Welch t-tests between complexity ratings, with FDR correction."""
    from itertools import combinations

    levels = sorted(df["complexity"].dropna().unique())
    rows = []
    for a, b in combinations(levels, 2):
        x = df.loc[df["complexity"] == a, "difficulty"].dropna()
        y = df.loc[df["complexity"] == b, "difficulty"].dropna()
        t = stats.ttest_ind(x, y, equal_var=False)
        rows.append(
            {
                "comparison": f"{int(a)} vs {int(b)}",
                "n_a": len(x), "n_b": len(y),
                "mean_a": round(x.mean(), 3), "mean_b": round(y.mean(), 3),
                "t": round(t.statistic, 3),
                "df": round(t.df, 1),
                "p_raw": t.pvalue,
            }
        )
    out = pd.DataFrame(rows)

    out["p_fdr"] = _benjamini_hochberg(out["p_raw"].values)
    return out


def _benjamini_hochberg(pvals) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values, returned in the input order.

    The monotonicity step runs over p-values sorted ascending, so the ranks and
    the cumulative minimum must be taken in that sorted order and mapped back.
    """
    p = np.asarray(pvals, dtype=float)
    m = p.size
    order = np.argsort(p)
    ranked = p[order]
    adj = ranked * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(m, dtype=float)
    out[order] = np.clip(adj, 0, 1)
    return out


if __name__ == "__main__":
    df = build()
    df.to_csv(paths.TABLES / "problem_correlates.csv")

    print(f"problems: {len(df)}\n")
    print("=== correlations with mean difficulty ===")
    corr = correlations(df)
    disp = corr.copy()
    disp["p"] = disp["p"].map(lambda v: f"{v:.2e}" if v < .001 else f"{v:.3f}")
    disp["p_spearman"] = disp["p_spearman"].map(
        lambda v: f"{v:.2e}" if v < .001 else f"{v:.3f}")
    print(disp[["measure", "n", "r", "p", "rho", "p_spearman"]].to_string(index=False))
    corr.to_csv(paths.TABLES / "difficulty_correlations.csv", index=False)

    print("\n=== core knowledge category ===")
    f, p, sizes = core_knowledge_test(df)
    if f is not None:
        print(f"one-way ANOVA: F = {f:.3f}, p = {p:.3f}")
        print(sizes.to_string())

    print("\n=== rated complexity ===")
    pw = complexity_pairwise(df)
    show = pw.copy()
    for c in ("p_raw", "p_fdr"):
        show[c] = show[c].map(lambda v: f"{v:.4f}")
    print(show.to_string(index=False))
    pw.to_csv(paths.TABLES / "complexity_pairwise.csv", index=False)

    print(f"\nwrote {paths.TABLES / 'problem_correlates.csv'}")
    print(f"wrote {paths.TABLES / 'difficulty_correlations.csv'}")
    print(f"wrote {paths.TABLES / 'complexity_pairwise.csv'}")
