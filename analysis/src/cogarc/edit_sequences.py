"""Measures derived from the logged edit sequences.

Each trial has a CSV of every interface action with a millisecond timestamp.
Two measures the manuscript reports are computed here, both restricted to the
first attempt and to the analysis sample, so each person contributes one
sequence per problem.

Edit similarity
    The mean pairwise Jaccard similarity between participants' sets of
    ``(x, y, colour)`` edits on a problem. The metric is over unordered sets,
    so it ignores the order of edits and is not inflated by sequence length.

Normalized extra steps
    Edits made before the first submission, divided by the minimum needed to
    reach the participant's own submitted grid. That minimum is the smaller of
    the distance from the test input and the distance from a blank grid, since
    a participant may start from either. A value of 1 means no redundant edits.

    The submitted grid is read from the submission files rather than
    reconstructed from the action log; see ``submitted_grid``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import paths
from .sample import trial_level_sample

EDIT_DIR = paths.DATA_REPO / "Experiment 2/Edit sequences"


def _first_attempt_actions(path: Path) -> pd.DataFrame | None:
    """Every action logged before the first submission."""
    try:
        df = pd.read_csv(path)
    except (OSError, pd.errors.ParserError):
        return None
    if "action" not in df.columns:
        return None
    submits = df.index[df["action"] == "submit"]
    cutoff = submits[0] if len(submits) else len(df)
    return df.loc[: cutoff - 1]


def _edits_only(actions: pd.DataFrame) -> list[tuple]:
    """The (x, y, colour) edits, in order."""
    e = actions[actions["action"] == "edit"].dropna(subset=["x", "y", "color"])
    return [(int(r.x), int(r.y), int(r.color)) for r in e.itertuples()]


def submitted_grid(task: str, subject: str) -> tuple | None:
    """The participant's first submitted grid, as logged at submission.

    Replaying the action log to reconstruct this grid was tried and abandoned:
    reconstructions matched the logged submission for only a handful of trials,
    so the editor's state transitions are not fully recoverable from the
    action names alone. The submission files are the authoritative record.
    """
    f = paths.SUBMISSIONS / f"{task}.json" / f"{task}_{subject}_submission1.json"
    try:
        with open(f) as fh:
            return tuple(c for row in json.load(fh)["grid_data"] for c in row)
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def test_inputs() -> dict[str, list[list[int]]]:
    out = {}
    for f in paths.ARC_TASKS.glob("*.json"):
        try:
            out[f.stem] = json.load(open(f))["test"][0]["input"]
        except (OSError, json.JSONDecodeError, KeyError, IndexError):
            continue
    return out


def collect_edits(sample: pd.DataFrame | None = None) -> dict[str, dict[str, dict]]:
    """Per problem and person, the first-attempt edits and submitted grid."""
    df = trial_level_sample() if sample is None else sample
    inputs = test_inputs()

    wanted = {}
    for r in df.itertuples():
        wanted.setdefault(r.trial, {})[r.subject] = r.person_id

    out = {}
    for trial, subjects in wanted.items():
        task_dir = EDIT_DIR / f"{trial}.json"
        grid = inputs.get(trial)
        if not task_dir.is_dir() or grid is None:
            continue
        per_person = {}
        for subject, person in subjects.items():
            f = task_dir / f"subj_{subject}_trial_{trial}.json.csv"
            if not f.exists():
                continue
            actions = _first_attempt_actions(f)
            if actions is None:
                continue
            final = submitted_grid(trial, subject)
            if final is None:
                continue
            per_person[person] = {
                "edits": _edits_only(actions),
                "final": final,
            }
        if per_person:
            out[trial] = per_person
    return out


def jaccard_by_problem(edits: dict[str, dict[str, list]]) -> pd.Series:
    """Mean pairwise Jaccard similarity of edit sets, per problem."""
    result = {}
    for trial, per_person in edits.items():
        sets = [set(v["edits"]) for v in per_person.values() if v["edits"]]
        n = len(sets)
        if n < 2:
            continue
        total, pairs = 0.0, 0
        for i in range(n):
            a = sets[i]
            for j in range(i + 1, n):
                b = sets[j]
                union = len(a | b)
                if union:
                    total += len(a & b) / union
                pairs += 1
        result[trial] = total / pairs if pairs else np.nan
    return pd.Series(result, name="edit_similarity")


def _levenshtein_grid(a: tuple, b: tuple) -> int:
    """Cells differing between two grids of equal length."""
    return sum(1 for x, y in zip(a, b) if x != y)


def extra_steps_by_problem(
    edits: dict[str, dict[str, list]]
) -> tuple[pd.Series, pd.DataFrame]:
    """Mean normalized extra steps per problem, and the per-trial values."""
    inputs = test_inputs()

    rows = []
    for trial, per_person in edits.items():
        grid = inputs.get(trial)
        if grid is None:
            continue
        flat_input = tuple(c for row in grid for c in row)

        for person, v in per_person.items():
            seq, final = v["edits"], v["final"]
            if not seq or len(final) != len(flat_input):
                continue
            # A participant may build from a blank grid or from a copy of the
            # test input, so the minimum is the cheaper of the two routes.
            from_blank = sum(1 for c in final if c != 0)
            from_input = _levenshtein_grid(final, flat_input)
            minimum = max(1, min(from_blank, from_input))
            rows.append(
                {
                    "trial": trial,
                    "person_id": person,
                    "n_edits": len(seq),
                    "minimum": minimum,
                    "norm_extra_steps": len(seq) / minimum,
                }
            )

    per_trial = pd.DataFrame(rows)
    by_problem = per_trial.groupby("trial")["norm_extra_steps"].mean()
    by_problem.name = "norm_extra_steps"
    return by_problem, per_trial


if __name__ == "__main__":
    print("reading edit sequences ...")
    edits = collect_edits()
    n_seq = sum(len(v) for v in edits.values())
    print(f"  {len(edits)} problems, {n_seq:,} first-attempt sequences\n")

    print("computing pairwise edit similarity ...")
    sim = jaccard_by_problem(edits)
    print(f"  mean over problems: {sim.mean():.4f}   "
          f"range {sim.min():.4f}-{sim.max():.4f}")

    print("computing normalized extra steps ...")
    extra, per_trial = extra_steps_by_problem(edits)
    print(f"  mean over problems: {extra.mean():.4f}   "
          f"range {extra.min():.4f}-{extra.max():.4f}")

    out = pd.concat([sim, extra], axis=1)
    out.to_csv(paths.TABLES / "edit_sequence_measures.csv")
    per_trial.to_csv(paths.DERIVED / "extra_steps_per_trial.csv", index=False)
    print(f"\nwrote {paths.TABLES / 'edit_sequence_measures.csv'}")
