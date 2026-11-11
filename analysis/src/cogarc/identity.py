"""Link subject IDs to Mechanical Turk worker IDs.

Two independent sources map a session to the person who ran it:

``subjectID_1`` / ``subjectID_2`` in the screening survey
    Filled in by hand during data collection. Covers 175 of the 233 subject
    IDs.

``Actual Completion Code`` in the CloudResearch completion-code exports
    The code a participant pasted back into Mechanical Turk to claim payment
    is their subject ID, recorded against their ``AmazonIdentifier``. Covers
    187 subject IDs, and was produced by a different process than the survey
    columns.

The two agree on every subject ID they both cover and each independently
identifies the same 16 workers holding two subject IDs, so they corroborate
rather than merely supplement each other. Used together they link 162 of the
199 people in the analysis sample.
"""

from __future__ import annotations

import glob

import pandas as pd

from . import paths


def survey_links() -> dict[str, str]:
    """subject ID -> worker ID, from the survey's hand-entered columns.

    Empty without the private survey; the derived duplicate list is shipped
    instead, at `Behavioral data/duplicate_participants.csv`.
    """
    from .duplicates import _load_survey

    if paths.DEMOGRAPHICS_LINKED is None or not paths.DEMOGRAPHICS_LINKED.exists():
        return {}
    out = {}
    for _, row in _load_survey().iterrows():
        for col in ("subjectID_1", "subjectID_2"):
            sid = str(row[col]).strip()
            if sid and sid.lower() not in {"nan", "none"}:
                out[sid] = row["workerId"]
    return out


def completion_code_links() -> dict[str, str]:
    """subject ID -> worker ID, from the CloudResearch completion codes."""
    frames = []
    if paths.COMPLETION_CODES is None:
        return {}
    pattern = str(paths.COMPLETION_CODES / "*.csv")
    for f in glob.glob(pattern):
        d = pd.read_csv(f, dtype=str, low_memory=False)
        if "Actual Completion Code" not in d.columns:
            continue
        d = d[["AmazonIdentifier", "Actual Completion Code"]].dropna()
        frames.append(d)
    if not frames:
        return {}
    cc = pd.concat(frames)
    cc.columns = ["workerId", "code"]
    cc["code"] = cc["code"].str.strip().str.lower()
    cc["workerId"] = cc["workerId"].str.strip()
    return dict(zip(cc["code"], cc["workerId"]))


def subject_to_worker() -> dict[str, str]:
    """Combined mapping, preferring the survey where both sources cover an ID."""
    combined = completion_code_links()
    combined.update(survey_links())
    return combined


def check_agreement() -> pd.DataFrame:
    """Subject IDs where the two sources disagree about the worker."""
    a, b = survey_links(), completion_code_links()
    rows = [
        {"subject_id": sid, "survey": a[sid], "completion_code": b[sid]}
        for sid in set(a) & set(b)
        if a[sid] != b[sid]
    ]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    a, b = survey_links(), completion_code_links()
    both = set(a) & set(b)
    print(f"survey links:           {len(a)}")
    print(f"completion-code links:  {len(b)}")
    print(f"covered by both:        {len(both)}")
    disagree = check_agreement()
    print(f"disagreements:          {len(disagree)}")
    if len(disagree):
        print(disagree.to_string(index=False))
    print(f"combined:               {len(subject_to_worker())}")
