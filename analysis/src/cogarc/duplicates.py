"""Identify participants who completed Experiment 2 twice under separate IDs.

Two signals identify a repeat participant:

Class 1 -- one Mechanical Turk ``workerId`` linked to two subject IDs in the
screening/demographics survey. The worker ID is assigned by Amazon and is
stable across sessions, so this is unambiguous.

Class 2 -- an identical demographic fingerprint (initials, age, sex, years of
education, handedness, race) recorded under *different* worker IDs. A person
who re-registered with a second worker account is invisible to Class 1 but
still reports the same demographics. This signal is weaker: a fingerprint such
as "AC, 33, male, 16 years education, right-handed, White" is not by itself
identifying, so a match may be coincidence.

Only Class 1 is treated as a duplicate. Class 2 is computed and reported, but
no longer groups anyone, because of how it performed here. It fired three
times (see ``FINGERPRINT_MATCHES``), and in the two cases where independent
evidence could test it, it was wrong:

  person_02  d33m799j ran from a Los Angeles IP on a Pacific-time browser 75
             minutes before 0hrc9vve ran from a New York IP on an Eastern-time
             browser.
  person_10  8bgj1tsd ran 2023-07-05 22:36-00:07 under one worker, overlapping
             hpl7jugr 21:54-22:49 under another by 14 minutes, with both
             workers holding a HIT across that window. One person cannot have
             done both.

The third pair, kkeej6x5 and 4s9g1cze, is not contradicted -- but neither test
could reach it: the sessions are six days apart, so they cannot overlap, and
both IPs are in Chicago, so they cannot disagree on location. It is untested
rather than confirmed, and treating it as a duplicate while rejecting the two
that could be tested would apply the signal only where it cannot be checked.

A fingerprint is in any case thin evidence: these three are "T / 27 / Male /
16 / right-handed / Black or African American", "AC / 33 / Male / 16 /
right-handed / White" and "JM / 33 / Male / 12 / right-handed / White". Two
rest on initials of one or two letters, and one worker gave 17 and then 16
years of education on two occasions, so the fingerprint is not even stable
within a person.

The ``evidence`` column therefore reads "worker ID" throughout. It is kept so
that the file can still record a different signal if one is ever added.
"""

from __future__ import annotations

import pandas as pd

from . import paths


FINGERPRINT_COLS = ["intitals", "age", "sex", "years of education", "handedness", "race"]

# Every fingerprint match found, and what became of it. Kept as a record: the
# pairs are real matches on the fingerprint columns, and a later analysis may
# want to revisit them, but none of them groups anyone.
FINGERPRINT_MATCHES = {
    ("o2ho0580", "d33m799j"): "refuted: different IP, timezone 75 minutes apart",
    ("hpl7jugr", "8bgj1tsd"): "refuted: sessions overlap by 14 minutes",
    ("kkeej6x5", "4s9g1cze"): "untested: no overlap possible, same metro area",
}

# Whether a fingerprint match makes two subject IDs one person. See the module
# docstring: it was wrong in both testable cases, so it does not.
FINGERPRINT_GROUPS = False


def _load_survey() -> pd.DataFrame:
    """Read the screening survey, dropping repeated header rows and blanks.

    Reads the ``_with_subjectIDs`` export, the only one carrying the
    hand-entered subject ID columns. The exported CSV contains duplicated rows
    and header rows re-emitted mid-file. The subject ID columns are the last
    two columns and the worker ID the third from last; they are read by
    position because the header names are duplicated within the file.
    """
    df = pd.read_csv(paths.DEMOGRAPHICS_LINKED, dtype=str, keep_default_na=False)

    # Repeated header rows re-emit the literal column name in each cell.
    df = df[df.iloc[:, -3] != "workerId"]

    df = df.rename(
        columns={
            df.columns[-3]: "workerId",
            df.columns[-2]: "subjectID_1",
            df.columns[-1]: "subjectID_2",
        }
    )
    for c in ("workerId", "subjectID_1", "subjectID_2"):
        df[c] = df[c].astype(str).str.strip()

    df = df[df["workerId"] != ""]
    return df.reset_index(drop=True)


def _fingerprint(df: pd.DataFrame) -> pd.Series:
    present = [c for c in FINGERPRINT_COLS if c in df.columns]
    return (
        df[present]
        .apply(lambda s: s.astype(str).str.strip().str.lower())
        .agg("|".join, axis=1)
    )


def subjects_in_data() -> set[str]:
    """Subject IDs that actually have trials in the Experiment 2 measures."""
    seq = pd.read_csv(paths.SEQ_MEASURES_MTURK, usecols=["subject"])
    return set(seq["subject"].astype(str).unique())


def _build_from_private() -> pd.DataFrame:
    """Rebuild the duplicate table from the private sources.

    Class 1 uses the worker-ID links, taken from the survey's hand-entered
    subject ID columns and from the CloudResearch completion codes. Class 2
    matches demographic fingerprints recorded under different worker IDs.
    """
    from .identity import completion_code_links, survey_links

    in_data = subjects_in_data()

    links = completion_code_links()
    links.update(survey_links())

    worker_to_subjects: dict[str, set[str]] = {}
    for subject, worker in links.items():
        if subject in in_data:
            worker_to_subjects.setdefault(worker, set()).add(subject)

    groups: list[tuple[set[str], str]] = [
        (ids, "worker ID")
        for ids in worker_to_subjects.values()
        if len(ids) > 1
    ]

    # Class 2: same fingerprint under different worker IDs. Reported only.
    if FINGERPRINT_GROUPS:
        survey = _load_survey()
        survey = survey[_fingerprint(survey) != ""]
        survey["_fp"] = _fingerprint(survey)
        for _, block in survey.groupby("_fp"):
            if block["workerId"].nunique() < 2:
                continue
            ids = {
                sid
                for col in ("subjectID_1", "subjectID_2")
                for sid in block[col]
                if sid in in_data
            }
            if len(ids) > 1 and not any(ids <= g for g, _ in groups):
                groups.append((ids, "demographic fingerprint"))

    # A subject ID can surface in both classes, so groups sharing any ID are
    # merged into one person. The merged group carries every signal that went
    # into it: reporting only the stronger one hides that some members are
    # there on a fingerprint alone.
    merged: list[tuple[set[str], set[str]]] = []
    for ids, evidence in groups:
        hit = [g for g in merged if g[0] & ids]
        if not hit:
            merged.append((set(ids), {evidence}))
            continue
        keep = hit[0]
        for other in hit[1:]:
            keep[0].update(other[0])
            keep[1].update(other[1])
            merged.remove(other)
        keep[0].update(ids)
        keep[1].add(evidence)

    def label(signals: set[str]) -> str:
        if signals == {"worker ID"}:
            return "worker ID"
        if signals == {"demographic fingerprint"}:
            return "demographic fingerprint"
        return "worker ID and demographic fingerprint"

    rows = []
    for n, (ids, signals) in enumerate(sorted(merged, key=lambda g: sorted(g[0])), 1):
        for sid in sorted(ids):
            rows.append(
                {
                    "subject_id": sid,
                    "person_id": f"person_{n:02d}",
                    "evidence": label(signals),
                    "in_data": sid in in_data,
                }
            )
    return pd.DataFrame(rows)


def build_duplicate_table() -> pd.DataFrame:
    """People holding more than one subject ID.

    Reads the shipped `Behavioral data/duplicate_participants.csv`, which lists
    each subject ID, an opaque person label, which signal linked them, and the
    order of their sessions. The session start times that established that
    order are not distributed: a timestamp narrows down who a pseudonymous
    subject ID belongs to for anyone holding the collection records. That
    file is derived from the screening survey and the payment records, neither
    of which is distributed: both carry Mechanical Turk worker IDs, and the
    survey also holds initials and other responses.

    With `COGARC_PRIVATE` pointing at those sources, the table is rebuilt from
    them instead, and the two are checked against each other.
    """
    shipped = pd.read_csv(paths.DUPLICATES_PUBLIC)
    if paths.PRIVATE is None:
        return shipped
    rebuilt = _build_from_private()
    _check_against_shipped(rebuilt, shipped)
    return shipped


def _check_against_shipped(rebuilt: pd.DataFrame, shipped: pd.DataFrame) -> None:
    """Warn if the private sources no longer agree with the shipped file."""
    a = set(shipped.loc[shipped["in_data"], "subject_id"])
    b = set(rebuilt.loc[rebuilt["in_data"], "subject_id"])
    if a != b:
        import warnings

        warnings.warn(
            f"duplicate_participants.csv lists {len(a)} subject IDs in the "
            f"data; the private sources give {len(b)}. "
            f"Only in the file: {sorted(a - b)}. "
            f"Only in the sources: {sorted(b - a)}.",
            stacklevel=2,
        )


if __name__ == "__main__":
    table = build_duplicate_table()
    table.to_csv(paths.DUPLICATE_LIST, index=False)

    in_data = table[table["in_data"]]
    both_sessions = in_data.groupby("person_id")["subject_id"].nunique()

    print(f"wrote {paths.DUPLICATE_LIST}")
    print(f"people with >1 subject ID (any evidence): {table['person_id'].nunique()}")
    print(f"  by worker ID:   "
          f"{table[table.evidence == 'worker_id']['person_id'].nunique()}")
    print(f"  by fingerprint: "
          f"{table[table.evidence == 'fingerprint']['person_id'].nunique()}")
    print(f"subject IDs listed: {table['subject_id'].nunique()}")
    print(f"people with >=2 sessions present in the behavioral data: "
          f"{(both_sessions > 1).sum()}")
    print(f"subject IDs in data belonging to those people: "
          f"{in_data[in_data.person_id.isin(both_sessions[both_sessions > 1].index)].shape[0]}")
    print(f"people with 3+ sessions in data: {(both_sessions > 2).sum()}")
