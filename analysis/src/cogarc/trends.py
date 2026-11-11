"""Change over the course of the session (manuscript section 3.2.2).

For each participant, deliberation time and difficulty score are regressed on
trial order, giving one slope per person per measure. The slopes are then
tested against zero at the group level.

Two constraints on which trials can be used:

* ``order`` positions a trial within its own session. For a repeat participant,
  a trial carried over from a later session has no defined position in their
  overall exposure, so these regressions use ``order_valid`` trials only --
  in practice, first sessions.

* Deliberation time is strongly right-skewed and one trial recorded 44 hours.
  Slopes are reported both on the raw scale, matching the published analysis,
  and on the log scale, where a single slow trial cannot dominate a
  participant's fit. Trials beyond the two-hour bound are excluded from both.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import paths
from .descriptives import difficulty_score
from .sample import load_sample

MIN_TRIALS = 10          # a slope from fewer points is not informative


def _slope(x, y) -> tuple[float, float]:
    """Slope of y on x, with its standard error.

    The standard error is carried alongside because the reported estimate
    pools these slopes by inverse-variance weighting: a slope from a short
    session is far less precise than one from a full session, and an
    unweighted mean would give them equal say.
    """
    if len(x) < 3:
        return np.nan, np.nan
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    sxx = ((x - x.mean())**2).sum()
    if sxx == 0:
        return np.nan, np.nan
    b = ((x - x.mean())*(y - y.mean())).sum()/sxx
    a = y.mean() - b*x.mean()
    resid = y - (a + b*x)
    if n <= 2:
        return b, np.nan
    se = np.sqrt((resid**2).sum()/(n - 2)/sxx)
    return b, se


def participant_slopes(sample: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per participant: slopes of each measure against trial order."""
    df = load_sample() if sample is None else sample
    df = df[df["order_valid"]].copy()
    df["difficulty"] = difficulty_score(df)

    rows = []
    for person, block in df.groupby("person_id"):
        timed = block[block["deliberation_ok"]]
        d_raw = d_log = d_raw_se = d_log_se = np.nan
        if len(timed) >= MIN_TRIALS:
            secs = timed["deliberation_time"].values / 1000
            d_raw, d_raw_se = _slope(timed["order"].values, secs)
            d_log, d_log_se = _slope(timed["order"].values,
                                     np.log(np.clip(secs, 1e-3, None)))

        diff = diff_se = np.nan
        if len(block) >= MIN_TRIALS:
            diff, diff_se = _slope(block["order"].values,
                                   block["difficulty"].values)

        rows.append(
            {
                "person_id": person,
                "n_trials": len(block),
                "n_timed": len(timed),
                "deliberation_slope": d_raw,
                "deliberation_slope_se": d_raw_se,
                "deliberation_slope_log": d_log,
                "deliberation_slope_log_se": d_log_se,
                "difficulty_slope": diff,
                "difficulty_slope_se": diff_se,
            }
        )
    return pd.DataFrame(rows).set_index("person_id")


def test_against_zero(slopes: pd.DataFrame, column: str) -> dict:
    s = slopes[column].dropna()
    t = stats.ttest_1samp(s, 0)
    w = stats.wilcoxon(s)
    return {
        "measure": column,
        "n": len(s),
        "mean": s.mean(),
        "median": s.median(),
        "sd": s.std(),
        "t": t.statistic,
        "df": len(s) - 1,
        "p": t.pvalue,
        "wilcoxon_p": w.pvalue,
    }


def _winsorize(s: pd.Series, lo=.01, hi=.99) -> pd.Series:
    a, b = s.quantile(lo), s.quantile(hi)
    return s.clip(a, b)


def slope_relationship(slopes: pd.DataFrame, log: bool = False) -> dict:
    """Are the two slopes related within participants?

    The published analysis winsorized both slopes at the 1st and 99th
    percentiles before correlating. Spearman on the untouched values is
    reported alongside, since it is insensitive to the same outliers without
    altering the data.
    """
    col = "deliberation_slope_log" if log else "deliberation_slope"
    sub = slopes[[col, "difficulty_slope"]].dropna()
    x, y = sub[col], sub["difficulty_slope"]

    xw, yw = _winsorize(x), _winsorize(y)
    r_w, p_w = stats.pearsonr(xw, yw)
    rho, p_s = stats.spearmanr(x, y)
    r_raw, p_raw = stats.pearsonr(x, y)

    n_clipped = int((x != xw).sum() + (y != yw).sum())
    return {
        "n": len(sub),
        "pearson_winsorized_r": r_w, "pearson_winsorized_p": p_w,
        "values_clipped": n_clipped,
        "pearson_raw_r": r_raw, "pearson_raw_p": p_raw,
        "spearman_rho": rho, "spearman_p": p_s,
    }


def by_trial_order(sample: pd.DataFrame | None = None) -> pd.DataFrame:
    """Mean of each measure at each trial position, for the figure panels."""
    df = load_sample() if sample is None else sample
    df = df[df["order_valid"]].copy()
    df["difficulty"] = difficulty_score(df)
    timed = df[df["deliberation_ok"]]

    out = df.groupby("order").agg(
        n=("person_id", "nunique"),
        difficulty=("difficulty", "mean"),
    )
    out["deliberation_mean_s"] = timed.groupby("order")["deliberation_time"].mean() / 1000
    out["deliberation_median_s"] = timed.groupby("order")["deliberation_time"].median() / 1000
    return out


if __name__ == "__main__":
    sample = load_sample()
    slopes = participant_slopes(sample)

    n_used = slopes["difficulty_slope"].notna().sum()
    print(f"participants with a usable slope: {n_used} of {len(slopes)}")
    print(f"  trials per participant: median {slopes.n_trials.median():.0f}\n")

    print("=== slopes against zero ===")
    rows = [
        test_against_zero(slopes, "deliberation_slope"),
        test_against_zero(slopes, "deliberation_slope_log"),
        test_against_zero(slopes, "difficulty_slope"),
    ]
    for r in rows:
        print(f"{r['measure']:26s} n={r['n']:3d}  mean={r['mean']:+.4f}  "
              f"median={r['median']:+.4f}  t({r['df']})={r['t']:+.2f}  "
              f"p={r['p']:.2e}  wilcoxon p={r['wilcoxon_p']:.2e}")
    pd.DataFrame(rows).to_csv(paths.TABLES / "trend_slopes.csv", index=False)

    print("\n=== relationship between the two slopes ===")
    for log in (False, True):
        rel = slope_relationship(slopes, log=log)
        label = "log deliberation" if log else "raw deliberation"
        print(f"{label}: n={rel['n']}")
        print(f"  winsorized Pearson r = {rel['pearson_winsorized_r']:+.3f}, "
              f"p = {rel['pearson_winsorized_p']:.3f} "
              f"({rel['values_clipped']} values clipped)")
        print(f"  raw Pearson        r = {rel['pearson_raw_r']:+.3f}, "
              f"p = {rel['pearson_raw_p']:.3f}")
        print(f"  Spearman         rho = {rel['spearman_rho']:+.3f}, "
              f"p = {rel['spearman_p']:.3f}")

    slopes.to_csv(paths.TABLES / "participant_trend_slopes.csv")
    by_trial_order(sample).to_csv(paths.TABLES / "measures_by_trial_order.csv")
    print(f"\nwrote {paths.TABLES / 'trend_slopes.csv'}")
    print(f"wrote {paths.TABLES / 'participant_trend_slopes.csv'}")
    print(f"wrote {paths.TABLES / 'measures_by_trial_order.csv'}")
