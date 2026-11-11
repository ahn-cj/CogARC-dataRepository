"""Construct the Experiment 2 analysis sample.

Deduplication happens here and nowhere else. Every downstream analysis reads
``analysis_sample.csv`` rather than the raw measures file, so the handling rule
is applied exactly once and is visible in one place.

The rule
--------
One record per person per problem.

* A problem attempted in more than one session contributes the FIRST session's
  trial, regardless of the outcome in either session. Sessions are ordered by
  their start time, carried in duplicate_participants.csv as ``session_order``. Repeat performance is
  inconsistent in both directions -- 63 problems failed in session 1 were
  solved later, and 75 solved in session 1 were failed later -- so preferring
  the successful attempt would bias accuracy upward while preferring the first
  is outcome-blind.

* A problem attempted only in a LATER session is retained as that person's
  single observation of it. These are genuine first exposures to the problem
  and show no reliable within-person accuracy penalty relative to the same
  person's session-1 trials (mean delta -.12, paired t(16) = -1.50, p = .15).

* Trial ``order`` is defined within a session, so a trial carried over from a
  later session has no well-defined position in the person's overall exposure.
  Such rows carry ``order_valid = False`` and are excluded from analyses of
  within-session trends.

Columns added to the raw measures
---------------------------------
person_id     stable identifier for the human being
source        'session_1' | 'novel_in_later' | 'sole_session'
order         trial position within the session (from trial_order_exp2.csv)
order_valid   whether ``order`` locates the trial in the person's exposure
deliberation_ok  False for trials above the 2 h bound (see paths.DELIBERATION_MAX_MS)
grid_edited      whether any submission was more than the input copied over
examples_seen    whether the examples were opened at any point in the trial
valid_trial      grid_edited and examples_seen
examples_viewed  old name for examples_seen, kept for callers
passes_qc        whether the person solved more than MIN_PROBLEMS_SOLVED
enough_trials    whether the person has at least MIN_TRIALS_ATTEMPTED valid
                 trials, so that their own mean is worth comparing
in_analysis      passes_qc, enough_trials and valid_trial; the analysis set
"""

from __future__ import annotations

import pandas as pd

from . import paths
from .duplicates import build_duplicate_table


def _session_order(dupes: pd.DataFrame) -> dict[str, int]:
    """Chronological rank of each session within its person, 1 = earliest.

    Comes from the ``session_order`` column of duplicate_participants.csv,
    which was derived from each session's own start time -- the browser clock
    in the session log, converted to UTC using the offset that log states.

    This used to be taken from ``last_time`` in the measures file. That column
    is a millisecond offset within a session, not a clock (see
    paths.ORDER_WARNING), so the ordering it gave was arbitrary: for 11 of the
    17 repeat participants the session kept in full was not the earliest one.
    """
    return dict(zip(dupes["subject_id"], dupes["session_order"]))


def _person_map(dupes: pd.DataFrame, seq: pd.DataFrame) -> dict[str, str]:
    """Map every subject ID to a person ID.

    Subject IDs not implicated in any duplicate map to themselves, so the
    person ID is a superset of the subject ID and can be used as a grouping
    key throughout without special-casing.
    """
    mapping = {s: s for s in seq["subject"].unique()}
    for _, row in dupes.iterrows():
        if row["subject_id"] in mapping:
            mapping[row["subject_id"]] = row["person_id"]
    return mapping


def _roster_grouping(seq: pd.DataFrame):
    """Person map and session order from an explicit roster file.

    The roster names every session in the sample and the person it belongs
    to, so it both restricts the data and defines the grouping. Sessions
    absent from it are dropped. Order within a person follows the file, which
    is written earliest session first.
    """
    r = pd.read_csv(paths.ROSTER, dtype=str)
    r["rank"] = r.groupby("person_id").cumcount() + 1
    mapping = dict(zip(r["subject_id"], r["person_id"]))
    order = dict(zip(r["subject_id"], r["rank"]))
    missing = set(r["subject_id"]) - set(seq["subject"])
    if missing:
        raise ValueError(f"roster names sessions with no trials: {sorted(missing)}")
    return mapping, order


def build_sample(write: bool = True) -> pd.DataFrame:
    seq = pd.read_csv(paths.SEQ_MEASURES_MTURK)

    if paths.ROSTER is not None:
        mapping, order = _roster_grouping(seq)
        seq = seq[seq["subject"].isin(mapping)].copy()
        seq["person_id"] = seq["subject"].map(mapping)
    else:
        dupes = build_duplicate_table()
        dupes_in_data = dupes[dupes["in_data"]]
        seq["person_id"] = seq["subject"].map(_person_map(dupes_in_data, seq))
        order = _session_order(dupes_in_data)

    # --- resolve each person to one trial per problem ---------------------
    keep_rows, sources = [], []
    for person, block in seq.groupby("person_id"):
        sessions = sorted(block["subject"].unique(), key=lambda s: order.get(s, 1))

        if len(sessions) == 1:
            keep_rows.append(block)
            sources.append(pd.Series("sole_session", index=block.index))
            continue

        first, later = sessions[0], sessions[1:]
        s1 = block[block["subject"] == first]
        seen = set(s1["trial"])

        novel = block[block["subject"].isin(later) & ~block["trial"].isin(seen)]
        # A person may meet the same new problem in two later sessions; keep
        # the earliest of those.
        if len(novel):
            novel = (
                novel.assign(_order=novel["subject"].map(order))
                .sort_values("_order")
                .drop_duplicates("trial", keep="first")
                .drop(columns="_order")
            )

        keep_rows.extend([s1, novel])
        sources.extend(
            [
                pd.Series("session_1", index=s1.index),
                pd.Series("novel_in_later", index=novel.index),
            ]
        )

    sample = pd.concat(keep_rows).sort_index()
    sample["source"] = pd.concat(sources).sort_index()

    # --- attach true trial order ------------------------------------------
    filt = pd.read_csv(paths.BEHAVIORAL_MEASURES, usecols=["trial", "subject", "order"])
    filt["trial"] = filt["trial"].str.replace(".json", "", regex=False)
    sample = sample.merge(filt, on=["trial", "subject"], how="left")

    # `order` positions a trial within its own session. For a trial carried
    # over from a later session that position does not describe where the
    # trial sat in the person's overall exposure to the task.
    sample["order_valid"] = sample["order"].notna() & (
        sample["source"] != "novel_in_later"
    )

    # --- trial validity -----------------------------------------------------
    # Two checks, from trial_validity.csv (scripts/build_trial_validity.py):
    #
    #   grid_edited     the participant worked the grid directly. A trial fails
    #                   when every submission in it is the test input copied
    #                   over unchanged, or an untouched background.
    #   examples_seen   the examples were opened at least once, at any point.
    #
    # `examples_seen` deliberately does not ask WHEN the examples were opened.
    # This flag used to require them to have been opened before the first edit,
    # which removed 106 trials where the participant started drawing and then
    # checked the examples -- ordinary problem solving, not an invalid trial.
    valid = pd.read_csv(paths.TRIAL_VALIDITY,
                        usecols=["subject", "trial", "grid_edited", "examples_seen"])
    sample = sample.merge(valid, on=["subject", "trial"], how="left")
    sample["grid_edited"] = sample["grid_edited"].fillna(True)
    sample["examples_seen"] = sample["examples_seen"].fillna(True)
    sample["valid_trial"] = sample["grid_edited"] & sample["examples_seen"]

    # Kept under the old name so existing callers do not break.
    sample["examples_viewed"] = sample["examples_seen"]

    # --- timing bound -------------------------------------------------------
    sample["deliberation_ok"] = (
        sample["deliberation_time"].notna()
        & (sample["deliberation_time"] <= paths.DELIBERATION_MAX_MS)
    )

    # --- quality control ----------------------------------------------------
    solved = (
        sample.assign(ok=sample["final_outcome"] == "success")
        .groupby("person_id")["ok"]
        .sum()
    )
    if paths.MIN_PROBLEMS_SOLVED < 0:
        retained = set(solved.index)
    else:
        retained = set(solved[solved > paths.MIN_PROBLEMS_SOLVED].index)
    sample["passes_qc"] = sample["person_id"].isin(retained)

    # --- enough evidence per person ----------------------------------------
    # Counted over VALID trials, since an invalid trial tells us nothing about
    # the person either. A participant below the bound keeps their trials in
    # the record but is not compared with anyone: their own mean rests on too
    # little to be worth a number.
    n_valid = sample[sample["valid_trial"]].groupby("person_id").size()
    if paths.MIN_TRIALS_ATTEMPTED < 0:
        enough = set(sample["person_id"].unique())
    else:
        enough = set(n_valid[n_valid >= paths.MIN_TRIALS_ATTEMPTED].index)
    sample["enough_trials"] = sample["person_id"].isin(enough)

    # Rows the analyses use by default.
    sample["in_analysis"] = (sample["passes_qc"] & sample["enough_trials"]
                             & sample["valid_trial"])

    if write:
        sample.to_csv(paths.ANALYSIS_SAMPLE, index=False)
    return sample


def load_sample(
    qc: bool = True, require_valid: bool = True, require_examples: bool | None = None
) -> pd.DataFrame:
    """Read the analysis sample, building it if it does not yet exist.

    Defaults give the analysis set: participants passing quality control, and
    trials that record an attempt at the problem -- the examples opened at
    some point, and at least one submission that was not the test input
    copied over. That is the same condition as ``in_analysis``.

    ``require_valid=False`` keeps the invalid trials for a sensitivity check,
    and ``qc=False`` gives the full deduplicated record. ``require_examples``
    is the old name for ``require_valid`` and still works.
    """
    if require_examples is not None:
        require_valid = require_examples
    if not paths.ANALYSIS_SAMPLE.exists():
        build_sample()
    df = pd.read_csv(paths.ANALYSIS_SAMPLE)
    if qc:
        # Both person-level rules, so that this and `in_analysis` cannot drift
        # apart: a participant is compared only if they solved enough problems
        # AND produced enough valid trials to have a meaningful mean.
        df = df[df["passes_qc"] & df["enough_trials"]]
    if require_valid:
        df = df[df["valid_trial"]]
    return df.copy()


def trial_level_sample() -> pd.DataFrame:
    """Every valid trial, with no person-level rule applied.

    The set for every analysis grouped by problem: per-problem difficulty
    and accuracy, common errors, edit-sequence measures, and the trajectory
    figures. A participant contributes at most one first attempt to any one
    problem, so how many trials they completed in total does not affect the
    quality of that one observation, and dropping them would discard a valid
    submission from the problem's tally.

    Analyses grouped by PARTICIPANT use ``load_sample()``: a participant's own
    mean rests on their trials, so it needs enough of them to be worth
    comparing with anyone else's. That is the only place the 12-trial rule
    applies.
    """
    return load_sample(qc=False, require_valid=True)


if __name__ == "__main__":
    s = build_sample()
    raw = pd.read_csv(paths.SEQ_MEASURES_MTURK)

    print(f"wrote {paths.ANALYSIS_SAMPLE}\n")
    print(f"raw trials:            {len(raw):>7,}   subject IDs: {raw.subject.nunique()}")
    print(f"after deduplication:   {len(s):>7,}   people:      {s.person_id.nunique()}")
    print(f"  removed as repeats:  {len(raw) - len(s):>7,}")
    print("\nby source")
    print(s["source"].value_counts().to_string())

    qc = s[s["passes_qc"]]
    print(f"\nafter QC (>{paths.MIN_PROBLEMS_SOLVED} solved):")
    print(f"  people: {qc.person_id.nunique()}   trials: {len(qc):,}")
    print(f"  excluded by QC: {s.person_id.nunique() - qc.person_id.nunique()} people")

    print(f"\norder available and valid: {qc['order_valid'].sum():,} trials "
          f"({qc['order_valid'].mean():.1%})")
    print(f"deliberation within 2 h bound: {qc['deliberation_ok'].sum():,} trials "
          f"({(~qc['deliberation_ok']).sum()} excluded)")
    nv = ~qc["examples_viewed"]
    solved = qc["final_outcome"] == "success"
    print(f"examples never viewed before first edit: {nv.sum():,} trials "
          f"({nv.mean():.1%}), of which {(nv & solved).sum()} were solved "
          f"({solved[nv].mean():.1%} vs {solved.mean():.1%} overall)")

    final = s[s["in_analysis"]]
    print(f"\nANALYSIS SET: {final.person_id.nunique()} people, "
          f"{len(final):,} trials")
    fsolved = final["final_outcome"] == "success"
    print(f"  mean accuracy: {fsolved.mean():.4f}")
    per = final.assign(ok=fsolved).groupby("person_id")["ok"].mean()
    print(f"  mean of per-participant accuracy: {per.mean():.4f} "
          f"(median {per.median():.4f})")

    print(f"\nmean accuracy: "
          f"{(qc['final_outcome'] == 'success').mean():.4f}")
    per_person = (
        qc.assign(ok=qc["final_outcome"] == "success")
        .groupby("person_id")["ok"].mean()
    )
    print(f"mean of per-participant accuracy: {per_person.mean():.4f} "
          f"(median {per_person.median():.4f})")
