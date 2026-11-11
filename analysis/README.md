# CogARC analyses

Analysis code for the CogARC behavioural manuscript. Every path resolves inside
this repository, so a clone runs without configuration.

```bash
cd analysis
python3 run_all.py                          # everything, about two minutes
```

or individually, in any order:

```bash
PYTHONPATH=src python3 -m cogarc.sample     # build the analysis sample
PYTHONPATH=src python3 -m cogarc.figures    # regenerate every figure
```

Python 3.9+, with pandas, numpy, scipy, matplotlib, seaborn and openpyxl.

Figures are not stored in this repository. `run_all.py` writes them to
`outputs/figures/`, along with an image of every common error, in about two
minutes. The summary tables in `outputs/tables/` are kept, so the reported
numbers can be checked without running anything.

## Where to start

| | |
|---|---|
| `src/cogarc/sample.py` | **the sample definition; every analysis reads its output** |
| `src/cogarc/paths.py` | every file location and analysis constant, with the reasoning |
| `docs/common_errors.md` | how common errors are identified |
| `run_all.py` | runs everything, about two minutes |

## Modules

| module | purpose |
|---|---|
| `paths.py` | every file location and analysis constant, with the reasoning |
| `duplicates.py` | people holding more than one subject ID |
| `identity.py` | links subject IDs to worker IDs (needs the private survey) |
| `sample.py` | applies the inclusion rules; writes `analysis_sample.csv` |
| `demographics.py` | per-person demographics and their relation to accuracy |
| `common_errors.py` | common-error identification |
| `descriptives.py` | participant and problem summaries, task properties |
| `edit_sequences.py` | edit similarity and normalized extra steps |
| `correlates.py` | what predicts problem difficulty |
| `trends.py` | change over the course of a session |
| `trajectories.py` | grid state at every step of an edit sequence |
| `experiment1.py` | Experiment 1, with the ten lab pilots excluded |
| `figures.py` | every manuscript figure |

Inclusion happens only in `sample.py`. Everything downstream reads
`data_derived/analysis_sample.csv`, so the rules are applied once and are
visible in one place.

## The analysis sample

`Behavioral data/participant_roster.csv` names every session in the sample and
the person it belongs to, and is read by default, so a clone reproduces the
published sample without configuration. Fifteen sessions that could not be
attributed to a Mechanical Turk worker are absent from it and are excluded.

One record per person per problem:

* A problem attempted in more than one session contributes the **first**
  session's trial, regardless of outcome in either.
* A problem attempted **only in a later session** is kept as that person's
  single observation of it.

A trial is excluded if it records no attempt at its problem: the examples were
never opened at any point, or no submission differed from the test input or an
untouched grid. Opening the examples after editing has begun counts as having
seen them.

Experiment 2: **192 people, 11,600 trials**, used for every analysis grouped by
problem. Analyses grouped by participant use the **185 people with at least 12
valid trials, 11,563 trials**, since a mean over fewer trials is an unreliable
estimate of a participant's performance. Experiment 1: **39 people, 2,787
trials**, the ten lab pilots excluded.

`../Behavioral data/trial_inclusion.csv` records both sets for every trial in
the raw files, so the filtering can be reproduced, audited, or replaced.

No threshold is applied to how many problems a person solved. Such a rule
selects on the outcome rather than the behaviour: the participants it removes
here still rank problems the way everyone else does, and dropping them lowers
the split-half reproducibility of the problem ordering rather than raising it.
`COGARC_MIN_SOLVED` reinstates one for anyone who wants it.

## Notes on the data

* **`last_time` is not a session clock.** Ranking trials by it correlates about
  -0.2 with true order. Use `order` from `behavioral_measures.csv`.
* **In the edit sequences `x` is the row and `y` the column.** Replaying them
  the other way reproduces the logged submission for about 5% of trials.
* **One trial records 44 hours of deliberation**, 35 times the next largest,
  and reflects a browser left open. Timing analyses drop trials over two hours
  and aggregate by median or on the log scale.
* **The common-error threshold counts people**, not sessions or submissions.

## Scripts

| script | what it produces |
|---|---|
| `build_trial_validity.py` | `Behavioral data/trial_validity.csv` |
| `build_trial_inclusion.py` | `Behavioral data/trial_inclusion.csv` |
| `rebuild_common_solutions.py` | `Common solutions/` |
| `rebuild_common_solutions_visualized.py` | `Common solutions visualized/` |

Each regenerates a file shipped in this repository, so anyone can confirm
that what is distributed matches what the code produces.

## Results tables

`outputs/tables/` holds the summary results, so the reported numbers can be
checked without running anything:

| file | contents |
|---|---|
| `participant_summary.csv` | one row per participant: problems attempted, accuracy by attempt |
| `problem_summary.csv` | one row per problem: accuracy, first-attempt success, difficulty, timing |
| `problem_correlates.csv` | problem-level measures joined to task properties |
| `difficulty_correlations.csv` | what predicts difficulty, with Spearman and Pearson |
| `complexity_pairwise.csv` | difficulty by rated complexity, FDR corrected |
| `common_errors.csv` | every common error with its participant count |
| `edit_sequence_measures.csv` | edit similarity and normalized extra steps per problem |
| `trend_slopes.csv`, `participant_trend_slopes.csv` | change over the session |
| `measures_by_trial_order.csv` | each measure at each trial position |
| `exp1_participant_summary.csv`, `exp1_problem_summary.csv` | the same for Experiment 1 |
| `demographics.csv`, `demographics_vs_accuracy.csv`, `demographics_group_means.csv` | the demographics table and its relation to accuracy |

## Private input

The participant screening survey carries Mechanical Turk worker IDs and
participant initials and is not distributed. Tables derived from it are shipped
de-identified in `outputs/tables/`; the modules that read it fail with an
explanatory message rather than producing different numbers silently. Set
`COGARC_PRIVATE` to that directory to regenerate them. It must also hold
`recovered_response_ids.json`, which pairs worker IDs with the survey
responses the Qualtrics export failed to stamp on 13-14 June 2023.

## Running an alternative sample

The defaults reproduce the manuscript. These variables change what a run
analyses and where it writes.

| variable | effect |
|---|---|
| `COGARC_ROSTER` | another roster, replacing the shipped one. A roster that also carries a `worker` column allows the demographics table to be rebuilt from the private survey export. |
| `COGARC_MIN_SOLVED` | a threshold on problems solved. Default -1, which applies no threshold. |
| `COGARC_MIN_TRIALS` | valid trials a participant needs before their mean is compared with anyone else's. Default 12. |
| `COGARC_PRIVATE` | the directory holding the screening survey export, needed only to rebuild the demographics table. |
| `COGARC_OUTPUT_SUFFIX` | appended to `data_derived`, `outputs/tables`, `outputs/figures`, `trial_inclusion.csv` and the rebuilt `Common solutions`, so a run writes beside the shipped files rather than over them. |

Each run writes `RUN_INFO.txt` beside its tables and figures, recording these
settings and the resulting sample sizes, so a file's provenance can be checked
without rerunning anything.
