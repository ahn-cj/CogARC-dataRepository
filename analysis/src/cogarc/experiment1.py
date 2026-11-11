"""Experiment 1: the remote-supervised sample.

The repository holds the 39 participants of the main collection. Ten lab
pilot sessions that preceded it were excluded before release; the pilot list
below is kept so the exclusion can be checked against the private collection
log.

Experiment 1 needs no example-viewing exclusion. Its interface showed the
examples permanently on the left of the edit screen, so the logs contain no
``showex``/``hideex`` actions and there is no trial on which a participant
could have solved a problem without the examples in front of them. The
separate example view, and therefore that exclusion, is specific to
Experiment 2.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import paths

# The collection log carries participant initials and is not distributed; the
# pilot list below is derived from it and is what the analyses use.
SUBJECT_LOG = paths.SUBJECT_LOG
EDIT_DIR = paths.EDIT_SEQUENCES_EXP1
SUBMISSIONS = paths.SUBMISSIONS_EXP1

# Lab pilots, from the subject log. Listed explicitly so the exclusion does not
# depend on the spreadsheet remaining readable.
PILOTS = [
    "rklhy665",  # ARC-OBT-01  2021-09-15
    "se1fxe04",  # ARC-OBT-02  2021-09-21
    "l8pamw0d",  # ARC-OBT-03  2021-09-21  ran over time
    "18k9066z",  # ARC-OBT-04  2021-09-29
    "3e8hhg80",  # ARC-OBT-05  2021-10-25
    "9zpwh2sh",  # ARC-OBT-06  2021-11-01
    "0790qgik",  # ARC-OBT-07  2021-11-05
    "eyqm34e5",  # ARC-OBT-08  2021-11-05  technical error
    "tytiuucm",  # ARC-OBT-09  2021-11-09
    "99evhyea",  # ARC-OBT-10  2021-11-18  technical error
]


def read_subject_log() -> pd.DataFrame:
    """The collection log, if openpyxl can read it; used to verify PILOTS."""
    import openpyxl

    wb = openpyxl.load_workbook(SUBJECT_LOG, data_only=True)
    rows = list(wb["Sheet1"].iter_rows(values_only=True))
    df = pd.DataFrame(rows[1:], columns=rows[0])
    return df[df["Study ID"].notna()].reset_index(drop=True)


def verify_pilots() -> dict:
    """Check the pilot list against the collection log, when it is available."""
    if SUBJECT_LOG is None or not SUBJECT_LOG.exists():
        return {"checked": False, "reason": "collection log not available "
                                            "(set COGARC_PRIVATE)"}
    try:
        log = read_subject_log()
    except Exception as exc:                      # noqa: BLE001
        return {"checked": False, "reason": str(exc)}
    verbal = set(
        log.loc[
            log["Consented?"].astype(str).str.strip().str.lower() == "verbal",
            "MongoDB ID",
        ]
    )
    return {
        "checked": True,
        "log_verbal": len(verbal),
        "matches": verbal == set(PILOTS),
        "only_in_log": sorted(verbal - set(PILOTS)),
        "only_in_code": sorted(set(PILOTS) - verbal),
    }


def load_sample(exclude_pilots: bool = True) -> pd.DataFrame:
    """Per-trial measures for Experiment 1."""
    df = pd.read_csv(paths.SEQ_MEASURES_ZOOM)
    if exclude_pilots:
        df = df[~df["subject"].isin(PILOTS)]
    df = df.copy()
    df["difficulty"] = df["success_try"].fillna(4).astype(float)
    df["solved"] = df["final_outcome"] == "success"
    df["solved_1"] = df["success_try"] == 1
    df["deliberation_ok"] = (
        df["deliberation_time"].notna()
        & (df["deliberation_time"] <= paths.DELIBERATION_MAX_MS)
    )
    return df


def participant_summary(df: pd.DataFrame | None = None) -> pd.DataFrame:
    d = load_sample() if df is None else df
    return d.groupby("subject").agg(
        n_attempted=("trial", "size"),
        accuracy=("solved", "mean"),
        first_attempt=("solved_1", "mean"),
    )


def problem_summary(df: pd.DataFrame | None = None) -> pd.DataFrame:
    d = load_sample() if df is None else df
    timed = d[d["deliberation_ok"]]
    out = d.groupby("trial").agg(
        n=("subject", "nunique"),
        accuracy=("solved", "mean"),
        first_attempt_success=("solved_1", "mean"),
        difficulty=("difficulty", "mean"),
    )
    out["deliberation_mean_s"] = timed.groupby("trial")["deliberation_time"].mean() / 1000
    out["deliberation_median_s"] = timed.groupby("trial")["deliberation_time"].median() / 1000
    return out


# --- common errors, for the Experiment 1 replication -----------------------

def _flatten(grid) -> tuple:
    return tuple(c for row in grid for c in row)


def load_submissions(exclude_pilots: bool = True) -> pd.DataFrame:
    """First-attempt submitted grids."""
    rows = []
    for task_dir in sorted(SUBMISSIONS.iterdir()):
        if not task_dir.is_dir():
            continue
        task = task_dir.name.replace(".json", "")
        for f in task_dir.iterdir():
            if not f.name.endswith("_submission1.json"):
                continue
            try:
                subject = f.name.split("_")[1]
                grid = _flatten(json.load(open(f))["grid_data"])
            except (OSError, json.JSONDecodeError, KeyError, IndexError):
                continue
            if exclude_pilots and subject in PILOTS:
                continue
            rows.append({"task": task, "subject": subject, "grid": grid})
    return pd.DataFrame(rows)


def replication_of_exp2_errors() -> pd.DataFrame:
    """How often each Experiment 2 common error recurs in Experiment 1.

    Counted against the Experiment 2 common errors, so this measures how far
    the shared errors of one sample recur in an independently collected one.
    """
    from .common_errors import find_common_errors
    
    exp2 = find_common_errors()
    exp2 = exp2[exp2["qualifies"]]

    subs = load_submissions()
    per_task = {t: b for t, b in subs.groupby("task")}

    rows = []
    for r in exp2.itertuples():
        block = per_task.get(r.task)
        if block is None or block.empty:
            rows.append({"task": r.task, "error": r.error,
                         "exp2_participants": r.n_participants,
                         "exp1_n": 0, "exp1_participants": 0,
                         "exp1_rate": np.nan})
            continue
        n_match = int(sum(1 for g in block["grid"] if g == r.grid))
        rows.append({
            "task": r.task, "error": r.error,
            "exp2_participants": int(r.n_participants),
            "exp1_n": int(len(block)),
            "exp1_participants": n_match,
            "exp1_rate": n_match / len(block),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    check = verify_pilots()
    print("pilot list check:", check)

    raw = pd.read_csv(paths.SEQ_MEASURES_ZOOM)
    df = load_sample()
    print(f"\nsessions in file: {raw.subject.nunique()}")
    print(f"pilots excluded:  {len(PILOTS)}")
    print(f"analysis sample:  {df.subject.nunique()} participants, {len(df):,} trials")

    people = participant_summary(df)
    problems = problem_summary(df)
    print(f"\naccuracy: mean {people.accuracy.mean()*100:.2f}%  "
          f"SD {people.accuracy.std()*100:.2f}%  "
          f"median {people.accuracy.median()*100:.2f}%")
    print(f"problems attempted: mean {people.n_attempted.mean():.1f}  "
          f"median {people.n_attempted.median():.0f}")

    fa = problems.first_attempt_success
    print(f"\nfirst-attempt success: median {fa.median()*100:.1f}%  "
          f"range {fa.min()*100:.1f}-{fa.max()*100:.1f}%")
    print(f"  solved by at least half: {(fa >= .5).mean()*100:.1f}%")
    print(f"  above 75%: {(fa > .75).mean()*100:.1f}%")
    print(f"  above 90%: {(fa > .90).mean()*100:.1f}%")

    print(f"\nmean difficulty: {problems.difficulty.mean():.3f} "
          f"(SD {problems.difficulty.std():.3f})")
    dm = problems.deliberation_mean_s
    print(f"deliberation, mean per problem: {dm.mean():.1f}s "
          f"(SD {dm.std():.1f}, range {dm.max()-dm.min():.1f})")
    dmd = problems.deliberation_median_s
    print(f"deliberation, median per problem: {dmd.mean():.1f}s "
          f"(SD {dmd.std():.1f}, range {dmd.max()-dmd.min():.1f})")

    perfect = problems[problems["accuracy"] == 1.0]
    print(f"\nproblems solved by everyone: {len(perfect)}")
    if len(perfect):
        q = perfect["deliberation_mean_s"]
        print(f"  their deliberation: mean {q.mean():.1f}s (SD {q.std():.1f}, "
              f"range {q.max()-q.min():.1f})")

    problems.to_csv(paths.TABLES / "exp1_problem_summary.csv")
    people.to_csv(paths.TABLES / "exp1_participant_summary.csv")
    print(f"\nwrote {paths.TABLES / 'exp1_problem_summary.csv'}")
