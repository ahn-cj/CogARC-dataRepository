"""Problem-level and participant-level descriptives for Experiment 2.

Everything here is computed from the deduplicated analysis sample, so each
person contributes at most one record per problem.

Two measures the manuscript reports need care:

*Difficulty score* runs 1 to 4: 1 if solved on the first attempt, 2 or 3 if
solved on a later attempt, 4 if never solved.

*Deliberation time* is the latency between trial onset and the first edit. One
trial records 44 hours and the distribution is heavily right-skewed, so
problem-level values are medians and any mean is taken on the log scale. The
aggregation is named explicitly wherever a number is reported.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import paths
from .sample import load_sample, trial_level_sample


# --- participant level -----------------------------------------------------

def participant_summary(sample: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per person: problems attempted, accuracy, cumulative by attempt.

    Attempt gains are computed within participant and then averaged, so each
    person contributes equally regardless of how many problems they completed.
    """
    df = load_sample() if sample is None else sample
    df = df.copy()
    df["solved"] = df["final_outcome"] == "success"
    for k in (1, 2, 3):
        df[f"solved_{k}"] = df["success_try"] == k

    out = df.groupby("person_id").agg(
        n_attempted=("trial", "size"),
        n_solved=("solved", "sum"),
        accuracy=("solved", "mean"),
        cum_1=("solved_1", "mean"),
        p2=("solved_2", "mean"),
        p3=("solved_3", "mean"),
    )
    out["cum_2"] = out["cum_1"] + out["p2"]
    out["cum_3"] = out["cum_2"] + out["p3"]
    out = out.rename(columns={"p2": "gain_attempt_2", "p3": "gain_attempt_3"})
    return out[
        ["n_attempted", "n_solved", "accuracy", "cum_1", "cum_2", "cum_3",
         "gain_attempt_2", "gain_attempt_3"]
    ]


# --- problem level ---------------------------------------------------------

def difficulty_score(df: pd.DataFrame) -> pd.Series:
    """1 solved first attempt, 2 or 3 solved later, 4 never solved."""
    score = df["success_try"].copy()
    return score.fillna(4).astype(float)


def problem_summary(sample: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per problem: accuracy, first-attempt success, difficulty, timing.

    Grouped by problem, so it uses the problem-level set: every participant
    with a valid trial on that problem, including those with too few trials
    overall to carry a participant-level mean.
    """
    df = trial_level_sample() if sample is None else sample
    df = df.copy()
    df["solved"] = df["final_outcome"] == "success"
    df["solved_1"] = df["success_try"] == 1
    df["difficulty"] = difficulty_score(df)

    timed = df[df["deliberation_ok"]].copy()
    timed["log_deliberation"] = np.log(timed["deliberation_time"].clip(lower=1))

    base = df.groupby("trial").agg(
        n_participants=("person_id", "nunique"),
        accuracy=("solved", "mean"),
        first_attempt_success=("solved_1", "mean"),
        difficulty=("difficulty", "mean"),
    )
    timing = timed.groupby("trial").agg(
        deliberation_median=("deliberation_time", "median"),
        deliberation_log_mean=("log_deliberation", "mean"),
        deliberation_mean_raw=("deliberation_time", "mean"),
    )
    return base.join(timing)


# --- task properties -------------------------------------------------------

def task_properties() -> pd.DataFrame:
    """Experimenter ratings and low-level features, keyed on ARC task id.

    Ratings come from `task_tags.csv`. The structural features are computed
    from the problem definitions in `Task JSONs/` rather than read from a
    precomputed file, so they cannot drift from the problems themselves.
    """
    import json

    tags = pd.read_csv(paths.TASK_TAGS)
    tags["trial"] = (
        tags["Task Name"].astype(str).str.replace(".json", "", regex=False)
    )
    tags = tags[["trial", "complexity", "primary_tag"]].rename(
        columns={"primary_tag": "core_knowledge"}
    )

    rows = []
    for f in sorted(paths.ARC_TASKS.glob("*.json")):
        try:
            task = json.load(open(f))
            test = task["test"][0]
            grid_in, grid_out = test["input"], test["output"]
        except (OSError, json.JSONDecodeError, KeyError, IndexError):
            continue
        flat_in = [c for row in grid_in for c in row]
        flat_out = [c for row in grid_out for c in row]
        # Minimum edits to reach the correct output, from whichever starting
        # point is cheaper: the test input, or a blank grid.
        from_input = (
            sum(1 for a, b in zip(flat_in, flat_out) if a != b)
            if len(flat_in) == len(flat_out) else len(flat_out)
        )
        from_blank = sum(1 for c in flat_out if c != 0)
        rows.append({
            "trial": f.stem,
            "num_train_examples": len(task.get("train", [])),
            "test_output_size": len(flat_out),
            # Colours the participant must actually draw, so background is
            # not counted.
            "num_test_colors": len(set(flat_out) - {0}),
            "levenshtein": min(from_input, from_blank),
        })
    props = pd.DataFrame(rows)

    return tags.merge(props, on="trial", how="outer").set_index("trial")


if __name__ == "__main__":
    sample = load_sample()              # grouped by participant
    problem_sample = trial_level_sample()   # grouped by problem

    people = participant_summary(sample)
    problems = problem_summary(problem_sample)

    print("=== participants ===")
    print(f"n = {len(people)}")
    print(f"problems attempted: mean {people.n_attempted.mean():.1f}, "
          f"median {people.n_attempted.median():.0f}")
    pct70 = (people.n_attempted >= 70).mean()
    print(f"completed at least 70 of 75: {pct70:.1%}")
    print(f"accuracy: mean {people.accuracy.mean():.3f} "
          f"(SD {people.accuracy.std():.3f}), median {people.accuracy.median():.3f}, "
          f"range {people.accuracy.min():.3f}-{people.accuracy.max():.3f}")
    print(f"cumulative accuracy by attempt (mean over participants):")
    print(f"  after 1: {people.cum_1.mean():.3f}   "
          f"after 2: {people.cum_2.mean():.3f}   "
          f"after 3: {people.cum_3.mean():.3f}")
    print(f"gain from attempt 2: {people.gain_attempt_2.mean():+.3f}   "
          f"from attempt 3: {people.gain_attempt_3.mean():+.3f}")

    print("\n=== problems ===")
    print(f"n = {len(problems)}")
    print(f"accuracy: mean {problems.accuracy.mean():.3f}")
    fa = problems.first_attempt_success
    print(f"first-attempt success: median {fa.median():.3f}, "
          f"range {fa.min():.3f}-{fa.max():.3f}")
    print(f"  solved by at least half: {(fa >= .5).mean():.1%}")
    print(f"  above 75%: {(fa > .75).mean():.1%}")
    print(f"  above 90%: {(fa > .90).mean():.1%}")
    print(f"difficulty: mean {problems.difficulty.mean():.3f} "
          f"(SD {problems.difficulty.std():.3f})")
    print(f"deliberation, median of per-problem medians: "
          f"{problems.deliberation_median.median() / 1000:.1f} s")

    problems.to_csv(paths.TABLES / "problem_summary.csv")
    people.to_csv(paths.TABLES / "participant_summary.csv")
    print(f"\nwrote {paths.TABLES / 'problem_summary.csv'}")
    print(f"wrote {paths.TABLES / 'participant_summary.csv'}")
