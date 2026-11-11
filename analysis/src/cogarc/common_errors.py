"""Identify common errors: incorrect outputs submitted by many participants.

Definition
----------
For each problem, first-attempt submissions are compared cell by cell against
the correct output. Among the incorrect submissions, any distinct grid produced
by at least ``COMMON_ERROR_MIN_PARTICIPANTS`` distinct PEOPLE is a common
error. Grids are compared exactly -- every cell must match -- so no clustering
is involved and two solutions are counted together only when identical.

Three properties of the definition, each ruling out a way of over-counting:

1. The threshold counts people, not sessions. Seventeen participants completed
   Experiment 2 more than once under separate subject identifiers; a person who
   submitted the same wrong grid twice counts once.

2. Candidates are ranked and counted on first attempts. A grid that is common
   only as a later-attempt correction is a different thing from a common first
   response: it is what someone produced after being told they were wrong.

3. Every qualifying grid is counted, so a problem that elicited four or
   five distinct shared errors contributes all of them.

Trivial submissions
-------------------
Two grids are never candidates, however many people submitted them: an
all-background grid, which is both the editor's starting state and what the
reset button produces, and a grid identical to the test input, which is what
the copy-input button produces. Someone who submits either has not applied a
transformation.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from . import paths
from .sample import trial_level_sample


def _flatten(grid) -> tuple:
    return tuple(cell for row in grid for cell in row)


def _load_grid(path: Path) -> tuple | None:
    try:
        with open(path) as fh:
            return _flatten(json.load(fh)["grid_data"])
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def _parse_submission_name(filename: str) -> tuple[str, str, int]:
    """``<task>_<subject>_submission<n>.json`` -> (task, subject, n)."""
    stem = filename.replace(".json", "")
    task, subject, sub = stem.split("_")
    return task, subject, int(sub.replace("submission", ""))


def load_submissions(first_attempt_only: bool = True) -> pd.DataFrame:
    """Read every submitted grid as one row.

    Returns columns: task, subject, submission_num, grid (flattened tuple).
    """
    rows = []
    for task_dir in sorted(paths.SUBMISSIONS.iterdir()):
        if not task_dir.is_dir():
            continue
        for f in sorted(task_dir.iterdir()):
            if f.suffix != ".json":
                continue
            try:
                task, subject, num = _parse_submission_name(f.name)
            except ValueError:
                continue
            if first_attempt_only and num != 1:
                continue
            grid = _load_grid(f)
            if grid is None:
                continue
            rows.append(
                {"task": task, "subject": subject, "submission_num": num, "grid": grid}
            )
    return pd.DataFrame(rows)


def load_test_inputs() -> dict[str, tuple]:
    """The test input grid for each problem, used to spot unedited submissions."""
    out = {}
    for f in sorted(paths.ARC_TASKS.glob("*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            out[f.stem] = _flatten(data["test"][0]["input"])
        except (OSError, json.JSONDecodeError, KeyError, IndexError):
            continue
    return out


def is_trivial(grid: tuple, test_input: tuple | None) -> bool:
    """An all-background grid, or the test input returned unedited."""
    if not grid:
        return True
    if set(grid) == {0}:
        return True
    return test_input is not None and grid == test_input


def load_success_grids() -> dict[str, tuple]:
    """The correct output grid for each problem, from `Common solutions/`."""
    out = {}
    for task_dir in sorted(paths.COMMON_SOLUTIONS.iterdir()):
        if not task_dir.is_dir():
            continue
        task = task_dir.name.replace(".json", "")
        grid = _load_grid(task_dir / f"{task}_Success.json")
        if grid is not None:
            out[task] = grid
    return out


def find_common_errors(
    deduplicate: bool = True,
    rank_on: str = "first_attempt",
    count_on: str = "first_attempt",
    rank_metric: str = "people",
    min_participants: int | None = None,
    max_per_problem: int | None = None,
    exclude_trivial: bool = True,
) -> pd.DataFrame:
    """Return one row per candidate common error.

    The defaults implement the definition in `docs/common_errors.md`. Each step
    is exposed as a parameter so a reader can vary one choice at a time and see
    what it costs.

    Parameters
    ----------
    deduplicate
        Restrict to the analysis sample, so each person contributes at most one
        submission per problem and the threshold counts people rather than
        sessions.
    rank_on
        'first_attempt' or 'all_attempts' -- which submissions determine the
        candidate grids for a problem. A grid common only as a later-attempt
        correction is a different thing from a common first response.
    count_on
        'first_attempt' or 'all_attempts' -- which submissions are counted
        against the threshold.
    rank_metric
        'people' or 'submissions' -- what the ranking maximizes. Ranking on
        people matches the quantity the threshold measures; ranking on raw
        submissions lets one participant who submitted the same grid twice
        move it up twice.
    min_participants
        Threshold; defaults to ``paths.COMMON_ERROR_MIN_PARTICIPANTS``.
    max_per_problem
        Candidates kept per problem; defaults to
        ``paths.COMMON_ERROR_MAX_PER_PROBLEM``, which keeps every grid meeting
        the threshold.
    exclude_trivial
        Drop all-background and unedited-input submissions, neither of which
        reflects an inferred transformation.

    Columns: task, error, n_participants, n_submissions, qualifies, grid.
    """
    if min_participants is None:
        min_participants = paths.COMMON_ERROR_MIN_PARTICIPANTS
    if max_per_problem is None:
        max_per_problem = paths.COMMON_ERROR_MAX_PER_PROBLEM
    if rank_on not in {"first_attempt", "all_attempts"}:
        raise ValueError(f"rank_on: {rank_on!r}")
    if count_on not in {"first_attempt", "all_attempts"}:
        raise ValueError(f"count_on: {count_on!r}")
    if rank_metric not in {"people", "submissions"}:
        raise ValueError(f"rank_metric: {rank_metric!r}")

    subs = load_submissions(first_attempt_only=False)
    success = load_success_grids()
    test_inputs = load_test_inputs()

    if deduplicate:
        # Every participant with valid trials. A common error is a tally of
        # how many people submitted one grid, not a mean, and nobody submits
        # more than once per problem, so a participant with few trials
        # contributes one observation of the same quality as anyone else's.
        # Analyses that average over participants or over problems use
        # load_sample() instead.
        sample = trial_level_sample()
        keep = set(zip(sample["subject"], sample["trial"]))
        subs = subs[
            [(s, t) in keep for s, t in zip(subs["subject"], subs["task"])]
        ].copy()
        person_of = dict(zip(sample["subject"], sample["person_id"]))
        subs["person_id"] = subs["subject"].map(person_of)
    else:
        subs = subs.copy()
        subs["person_id"] = subs["subject"]

    records = []
    for task, block in subs.groupby("task"):
        correct = success.get(task)
        if correct is None:
            continue

        wrong = block[[g != correct for g in block["grid"]]]
        if exclude_trivial:
            ti = test_inputs.get(task)
            wrong = wrong[[not is_trivial(g, ti) for g in wrong["grid"]]]
        if wrong.empty:
            continue

        rank_pool = wrong if rank_on == "all_attempts" else wrong[wrong.submission_num == 1]
        count_pool = wrong if count_on == "all_attempts" else wrong[wrong.submission_num == 1]
        if rank_pool.empty:
            continue

        if rank_metric == "people":
            ranked = rank_pool.groupby("grid")["person_id"].nunique()
        else:
            ranked = rank_pool["grid"].value_counts()
        ranked = ranked.sort_values(ascending=False)
        candidates = ranked.index if max_per_problem == 0 else ranked.head(
            max_per_problem).index

        for idx, grid in enumerate(candidates, start=1):
            matched = count_pool[[g == grid for g in count_pool["grid"]]]
            n_people = matched["person_id"].nunique()
            records.append(
                {
                    "task": task,
                    "error": f"error_{idx}",
                    "n_participants": int(n_people),
                    "n_submissions": int(len(matched)),
                    "qualifies": bool(n_people >= min_participants),
                    "grid": grid,
                }
            )

    return pd.DataFrame(records).sort_values(["task", "error"]).reset_index(drop=True)


def diff_against(baseline: pd.DataFrame, revised: pd.DataFrame) -> pd.DataFrame:
    """Error-by-error comparison of two runs, keyed on task and label."""
    b = baseline.set_index(["task", "error"])
    r = revised.set_index(["task", "error"])
    out = b[["n_participants", "qualifies"]].join(
        r[["n_participants", "qualifies"]], how="outer", lsuffix="_full", rsuffix="_dedup"
    )
    out["delta"] = out["n_participants_dedup"] - out["n_participants_full"]
    out["status"] = "unchanged"
    out.loc[
        out["qualifies_full"].fillna(False) & ~out["qualifies_dedup"].fillna(False),
        "status",
    ] = "dropped"
    out.loc[
        ~out["qualifies_full"].fillna(False) & out["qualifies_dedup"].fillna(False),
        "status",
    ] = "added"
    return out.reset_index()


if __name__ == "__main__":
    errors = find_common_errors()
    q = errors[errors["qualifies"]]
    per = q.groupby("task").size()

    print(f"common errors: {len(q)} across {q.task.nunique()} of 75 problems")
    print(f"  problems with none: {75 - q.task.nunique()}")
    print(f"  per problem: {per.value_counts().sort_index().to_dict()}")
    print(f"  participants per error: median {q.n_participants.median():.0f}, "
          f"range {q.n_participants.min()}-{q.n_participants.max()}")
    print(f"  submissions in common errors: {int(q.n_submissions.sum()):,}")

    out = q.drop(columns="grid")
    out.to_csv(paths.TABLES / "common_errors.csv", index=False)
    print(f"\nwrote {paths.TABLES / 'common_errors.csv'}")
