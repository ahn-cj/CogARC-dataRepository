"""Write `Behavioral data/trial_inclusion.csv`.

One row for every trial in the repository. `in_trial_level` marks the
problem-level set, which is every trial. `in_group_level` marks the
participant-level set, which drops participants with fewer than 12 valid
trials. The repository holds the analyzed trials only; trials excluded before
release are described in the main README.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cogarc import paths
from cogarc.experiment1 import PILOTS
from cogarc.sample import build_sample

# --- Experiment 2 -----------------------------------------------------------
raw2 = pd.read_csv(paths.SEQ_MEASURES_MTURK)
sample = build_sample(write=False)

kept = sample.set_index(["subject", "trial"])
in_sample = set(sample["subject"].unique())
rows = []
for r in raw2.itertuples():
    key = (r.subject, r.trial)
    if key in kept.index:
        rec = kept.loc[key]
        valid = bool(rec["valid_trial"])
        if not valid:
            reason = ("never edited the grid: every submission was the input "
                      "copied over or left blank"
                      if not bool(rec["grid_edited"]) else
                      "examples never opened at any point in the trial")
        elif not bool(rec["passes_qc"]):
            reason = (f"person solved {paths.MIN_PROBLEMS_SOLVED} or fewer "
                      "problems")
        elif not bool(rec["enough_trials"]):
            reason = (f"person has fewer than {paths.MIN_TRIALS_ATTEMPTED} valid "
                      "trials, too few to compare their mean with anyone else's")
        else:
            reason = ""
        person, source = rec["person_id"], rec["source"]
        trial_level = valid
        group_level = valid and bool(rec["passes_qc"]) and bool(rec["enough_trials"])
    elif r.subject not in in_sample:
        reason = ("session could not be attributed to a person, so it may be "
                  "an unrecognised repeat visit")
        person, source = None, "unattributed_session"
        trial_level = group_level = False
    else:
        reason = "repeat session: this problem was already attempted earlier"
        person, source = None, "repeat_session"
        trial_level = group_level = False
    rows.append({
        "experiment": 2, "subject": r.subject, "trial": r.trial,
        "person_id": person, "record": source,
        "in_trial_level": trial_level, "in_group_level": group_level,
        "exclusion_reason": reason,
    })

# --- Experiment 1 -----------------------------------------------------------
raw1 = pd.read_csv(paths.SEQ_MEASURES_ZOOM)
for r in raw1.itertuples():
    pilot = r.subject in PILOTS
    rows.append({
        "experiment": 1, "subject": r.subject, "trial": r.trial,
        "person_id": r.subject, "record": "pilot" if pilot else "session",
        "in_trial_level": not pilot, "in_group_level": not pilot,
        "exclusion_reason": "lab pilot, run before the main collection" if pilot else "",
    })

out = pd.DataFrame(rows)
out.to_csv(paths.TRIAL_INCLUSION, index=False)

print(f"wrote {paths.TRIAL_INCLUSION}")
print(f"  {len(out):,} trials total\n")
for exp, block in out.groupby("experiment"):
    kept_n = int(block["in_trial_level"].sum())
    print(f"Experiment {exp}: {len(block):,} trials, {kept_n:,} in analysis "
          f"({block.loc[block['in_trial_level'], 'person_id'].nunique()} people)")
    for reason, n in block.loc[~block["in_trial_level"], "exclusion_reason"].value_counts().items():
        print(f"    {n:>6,}  {reason}")
    print()
