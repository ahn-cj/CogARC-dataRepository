"""Write Behavioral data/trial_validity.csv: the two trial-level validity checks.

A trial is a valid observation of someone attempting a problem when both hold:

  grid_edited     the participant worked the output grid directly. Checked on
                  what they submitted: a trial fails when EVERY submission it
                  contains is the test input copied over unchanged, or an
                  untouched background. The check is on the grid rather than
                  on click events because a click can be undone or reset, so
                  an `edit` row in the log does not prove an edited grid --
                  and indeed every trial in the data has at least one such row.

  examples_seen   the examples were opened at least once, at any point in the
                  trial. Opening them only after starting to draw still counts:
                  that is ordinary problem solving. What this removes is
                  trials where the participant never looked at all, and so had
                  nothing from which to infer the transformation.

Shipped as a file rather than computed on demand because it reads all 14,107
edit-sequence logs.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cogarc import paths
from cogarc.common_errors import load_submissions, load_test_inputs, is_trivial


def build() -> pd.DataFrame:
    seq = pd.read_csv(paths.SEQ_MEASURES_MTURK, usecols=["subject", "trial", "file"])

    rows = []
    for r in seq.itertuples(index=False):
        log = pd.read_csv(paths.DATA_REPO / r.file, usecols=["action"])
        a = log["action"].astype(str)
        rows.append((r.subject, r.trial, int((a == "edit").sum()),
                     int((a == "copy").sum()), int((a == "showex").sum())))
    df = pd.DataFrame(rows, columns=["subject", "trial", "n_edit_actions",
                                     "n_copies", "n_example_views"])

    sub = load_submissions(first_attempt_only=False)
    inputs = load_test_inputs()
    sub["trivial"] = [is_trivial(g, inputs.get(t)) for g, t in zip(sub["grid"], sub["task"])]
    per = (sub.groupby(["subject", "task"])
           .agg(n_submissions=("trivial", "size"), n_unedited_submissions=("trivial", "sum"))
           .reset_index().rename(columns={"task": "trial"}))

    df = df.merge(per, on=["subject", "trial"], how="left")
    df["grid_edited"] = ~(df["n_unedited_submissions"] == df["n_submissions"]).fillna(False)
    df["examples_seen"] = df["n_example_views"] > 0
    df["valid_trial"] = df["grid_edited"] & df["examples_seen"]
    return df


if __name__ == "__main__":
    df = build()
    df.to_csv(paths.TRIAL_VALIDITY, index=False)
    print(f"trials                                {len(df):,}")
    print(f"  every submission an unedited grid   {(~df.grid_edited).sum():,}")
    print(f"  examples never opened               {(~df.examples_seen).sum():,}")
    print(f"  failing either check                {(~df.valid_trial).sum():,}")
    print(f"wrote {paths.TRIAL_VALIDITY}")
