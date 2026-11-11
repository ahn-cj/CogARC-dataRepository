"""Grid state at every step of an edit sequence (Figures 9 to 11).

The logged ``x`` is the ROW index and ``y`` the COLUMN, not the reverse.
Replaying with the intuitive ``y * cols + x`` reproduces the logged submission
for about 5% of trials; with ``x * cols + y`` it reproduces **100% of 1,875
trials sampled across all 75 problems**. The convention is verified on import
by ``verify_replay``.

A trajectory is the distance from the grid state at each step to the grid the
participant went on to submit, normalized to the number of cells. It starts
near the test input (most sequences begin by copying it) and reaches zero at
the submission. Whether that submission was correct is a separate matter, which
is what makes these plots informative: a participant can converge just as
directly on a wrong answer as on a right one.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import paths
from .edit_sequences import EDIT_DIR, _first_attempt_actions, test_inputs
from .sample import trial_level_sample


def replay_states(actions: pd.DataFrame, test_input: list[list[int]],
                  with_actions: bool = False):
    """Grid state after each action, in order.

    With ``with_actions``, returns ``(states, action_names)`` so a caller can
    tell which action produced each state.
    """
    rows, cols = len(test_input), len(test_input[0])
    flat = [c for row in test_input for c in row]
    grid = [0] * (rows * cols)
    states, names = [], []
    for r in actions.itertuples():
        act = r.action
        if act == "copy":
            grid = list(flat)
        elif act == "reset":
            grid = [0] * (rows * cols)
        elif act == "edit":
            if pd.isna(r.x) or pd.isna(r.y) or pd.isna(r.color):
                continue
            idx = int(r.x) * cols + int(r.y)      # x is the row, y the column
            if 0 <= idx < rows * cols:
                grid[idx] = int(r.color)
        else:
            continue
        states.append(tuple(grid))
        names.append(act)
    return (states, names) if with_actions else states


def _drop_reset_before_copy(states: list, names: list) -> tuple[list, list]:
    """Remove blank states that exist only because a reset preceded a copy.

    Clearing the grid and reloading the test input is one action from the
    participant's side, but the editor logs the reset and the copy separately,
    so the trajectory shows a dip to blank and straight back to the input that
    the participant never dwelt in. A reset followed by a copy, with nothing in
    between, is dropped. A reset the participant then edits from is real
    behaviour and is kept.
    """
    keep = []
    for i, name in enumerate(names):
        if name == "reset":
            nxt = next((n for n in names[i + 1:] if n != "reset"), None)
            if nxt == "copy":
                continue
        keep.append(i)
    return [states[i] for i in keep], [names[i] for i in keep]


def verify_replay(task: str, limit: int = 25) -> tuple[int, int]:
    """How often the replay reproduces the logged submission for one problem."""
    inputs = test_inputs()
    grid = inputs.get(task)
    if grid is None:
        return 0, 0
    ok = n = 0
    for f in sorted((paths.SUBMISSIONS / f"{task}.json").glob(
            f"{task}_*_submission1.json"))[:limit]:
        subject = f.name.split("_")[1]
        try:
            truth = tuple(c for row in json.load(open(f))["grid_data"] for c in row)
        except (OSError, json.JSONDecodeError, KeyError):
            continue
        ef = EDIT_DIR / f"{task}.json" / f"subj_{subject}_trial_{task}.json.csv"
        if not ef.exists():
            continue
        actions = _first_attempt_actions(ef)
        if actions is None:
            continue
        states = replay_states(actions, grid)
        n += 1
        ok += bool(states and states[-1] == truth)
    return ok, n


def reference_levels(task: str, reference: str = "correct") -> dict:
    """Where the test input and a blank grid sit on the trajectory axis.

    Panel C plots only participants who reached a shared solution, and every
    participant within a group submitted the same grid -- that is what defines
    the group. The levels are therefore exact, one pair per solution group,
    computed from the grids alone before any trajectory is drawn.

    Against the correct output the target is the same for every group, so a
    single pair applies. Against each participant's own submission the target
    is the group's grid, so groups can sit at different heights: on `12eac192`
    the input lies .250, .297 and .391 from the three group grids.

    Returns ``{group_name: {"Input": level, "Blank": level}}``.
    """
    from .common_errors import load_success_grids

    grid = test_inputs().get(task)
    if grid is None:
        return {}
    flat = tuple(c for row in grid for c in row)
    n = len(flat)

    def levels(target):
        return {
            "Input": sum(1 for a, b in zip(flat, target) if a != b) / n,
            "Blank": sum(1 for c in target if c != 0) / n,
        }

    groups = solution_groups(task)
    if reference == "correct":
        correct = load_success_grids().get(task)
        return {} if correct is None else {"": levels(correct)}
    return {name: levels(target) for name, target in groups.items()}


def _submitted_grids(task: str) -> list[tuple]:
    """First-attempt submitted grids for the retained participants."""
    sample = trial_level_sample()
    wanted = sample[sample["trial"] == task]
    grid = test_inputs().get(task)
    if grid is None or wanted.empty:
        return []
    out = []
    for r in wanted.itertuples():
        ef = EDIT_DIR / f"{task}.json" / f"subj_{r.subject}_trial_{task}.json.csv"
        if not ef.exists():
            continue
        actions = _first_attempt_actions(ef)
        if actions is None:
            continue
        states = replay_states(actions, grid)
        if states:
            out.append(states[-1])
    return out


def solution_groups(task: str) -> dict[str, tuple]:
    """Correct grid and the corrected common errors for one problem."""
    from .common_errors import find_common_errors, load_success_grids
    
    out = {}
    correct = load_success_grids().get(task)
    if correct is not None:
        out["Success"] = correct
    errors = find_common_errors()
    errors = errors[(errors["task"] == task) & errors["qualifies"]]
    for r in errors.sort_values("error").itertuples():
        n = r.error.replace("error_", "")
        out[f"Top error {n}"] = r.grid
    return out


def trial_trajectories(task: str, reference: str = "submitted",
                       normalize: str = "progress") -> pd.DataFrame:
    """One row per retained participant on this problem.

    ``reference`` selects what the trajectory is measured against:

    ``"submitted"``
        distance to the grid the participant went on to submit, so every
        trajectory ends at zero regardless of whether it was correct
    ``"correct"``
        distance to the correct output, so a trajectory ends at zero only if
        the participant solved the problem, and the reference levels for the
        test input and a blank grid are meaningful

    ``normalize`` selects the y-axis unit:

    ``"progress"``
        progress from the test input to the target, so the input sits at 0 and
        the target at 1 for every trajectory. The input and target distances
        are exact per solution group, but they differ between groups, so on the
        raw scale each group's input sits at a different height; rescaling puts
        them all on one line. The default.
    ``"grid"``
        distance as a fraction of the cells in the grid, matching the published
        definition. Each solution group's input then sits at its own exact
        height -- three separate levels on `12eac192`, one shared level on
        `1b60fb0c`.

    Columns: person_id, group, n_steps, trajectory, norm_extra_steps.
    """
    sample = trial_level_sample()
    wanted = sample[sample["trial"] == task]
    grid = test_inputs().get(task)
    if grid is None or wanted.empty:
        return pd.DataFrame()

    flat_input = tuple(c for row in grid for c in row)
    groups = solution_groups(task)
    n_cells = len(flat_input)
    if reference not in {"submitted", "correct"}:
        raise ValueError(f"reference: {reference!r}")
    target_correct = groups.get("Success")
    if reference == "correct" and target_correct is None:
        raise ValueError(f"no correct grid available for {task}")

    rows = []
    for r in wanted.itertuples():
        ef = EDIT_DIR / f"{task}.json" / f"subj_{r.subject}_trial_{task}.json.csv"
        if not ef.exists():
            continue
        actions = _first_attempt_actions(ef)
        if actions is None:
            continue
        states, names = replay_states(actions, grid, with_actions=True)
        states, names = _drop_reset_before_copy(states, names)
        # The editor opens on a blank canvas and logs a state before the
        # participant has put anything on it. Those leading blanks are where
        # the log starts, not something the participant did. Trim them so a
        # trajectory begins where the participant does; blank states the
        # participant then edited from are kept.
        first = next((i for i, g in enumerate(states) if any(g)), None)
        if first is None:
            continue
        states = states[first:]
        if not states:
            continue
        submitted = states[-1]

        label = "Miscellaneous"
        for name, g in groups.items():
            if submitted == g:
                label = name
                break

        target = submitted if reference == "submitted" else target_correct
        traj = [sum(1 for a, b in zip(s, target) if a != b) / n_cells
                for s in states]
        if normalize == "progress":
            # Distance from the test input to this group's target, exact.
            span = sum(1 for a, b in zip(flat_input, target) if a != b) / n_cells
            if span > 0:
                traj = [1 - v / span for v in traj]

        n_edits = int((actions["action"] == "edit").sum())
        from_blank = sum(1 for c in submitted if c != 0)
        from_input = sum(1 for a, b in zip(submitted, flat_input) if a != b)
        minimum = max(1, min(from_blank, from_input))

        rows.append({
            "person_id": r.person_id,
            "group": label,
            "n_steps": len(traj),
            "trajectory": traj,
            "norm_extra_steps": n_edits / minimum,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    for task in ("12eac192", "1b60fb0c"):
        ok, n = verify_replay(task)
        groups = solution_groups(task)
        df = trial_trajectories(task)
        print(f"=== {task} ===")
        print(f"  replay reproduces the submission: {ok}/{n}")
        print(f"  solution groups: {list(groups)}")
        if len(df):
            print(f"  participants: {len(df)}")
            print(df["group"].value_counts().to_string())
            print(f"  steps: median {df.n_steps.median():.0f}, max {df.n_steps.max()}")
        print()
