# Boston University CogARC Data Repository

Behavioral data, task files and analysis code for the Cognitive Abstraction and Reasoning Corpus (CogARC), a human behavioral dataset built on 75 problems from the Abstraction and Reasoning Corpus (ARC). The data come from the two experiments reported in the associated manuscript.

| | Sample | Setting | Participants | Trials |
|---|---|---|---|---|
| Experiment 1 | Boston University | Remote, supervised over video call | 39 | 2,787 |
| Experiment 2 | Amazon Mechanical Turk | Online, unsupervised | 192 | 11,600 |

The repository contains the trials analyzed in the manuscript. Exclusions are described under [Inclusion criteria](#inclusion-criteria).

## Contents

```
CogARC-dataRepository/
├── Behavioral data/
│   ├── Experiment 1/
│   │   ├── Edit sequences/
│   │   └── Submissions/
│   ├── Experiment 2/
│   │   ├── Edit sequences/
│   │   ├── Edit sequences typed/
│   │   └── Submissions/
│   ├── trial_measures_exp1.csv
│   ├── trial_measures_exp2.csv
│   ├── trial_order_exp2.csv
│   ├── trial_validity.csv
│   ├── trial_inclusion.csv
│   ├── participant_roster.csv
│   └── duplicate_participants.csv
├── Task JSONs/
├── Task example PNGs/
├── Common solutions/
├── Common solutions visualized/
├── task_tags.csv
├── edit_sequence_data_dictionary.md
└── analysis/
```

## Task files

| Path | Contents |
|---|---|
| `Task JSONs/<task_id>.json` | The ARC problem as shown to participants: the example input-output pairs (`train`) and the test input and output (`test`). |
| `Task example PNGs/<task_id>.json.png` | An image of each problem's examples. |
| `task_tags.csv` | Experimenter annotations for each problem: presentation order in Experiment 1, rated complexity (1 to 3), and up to three core knowledge tags. |

Core knowledge tags: `Obj` (objectness), `Geo` (geometry and patterns), `GoD` (goal-directedness), `Num` (numbers and counting).

## Behavioral data

### Raw trial records

Both experiments use the same folder structure, with one folder per problem.

**Submissions**

```
Behavioral data/Experiment <n>/Submissions/<task_id>.json/<task_id>_<subject_id>_submission<k>.json
```

One file per submission attempt. `grid_data` holds the submitted grid. A participant has more than one file for a problem if they made more than one attempt.

**Edit sequences**

```
Behavioral data/Experiment <n>/Edit sequences/<task_id>.json/subj_<subject_id>_trial_<task_id>.json.csv
```

One file per trial, with one row per action in the order it occurred: loading the problem, editing a cell, resetting the grid, copying the test input, opening and closing the examples (Experiment 2 only), and submitting. Columns are defined in `edit_sequence_data_dictionary.md`.

`Edit sequences typed/` (Experiment 2 only) holds the same files with an added `type` column, which labels each edit as a `click` or a `drag`.

### Trial-level measures

| File | Rows | Contents |
|---|---|---|
| `trial_measures_exp1.csv` | 2,787 | One row per trial in Experiment 1: deliberation time, time between edits, resets, submissions, outcome. |
| `trial_measures_exp2.csv` | 11,600 | The same for Experiment 2, plus the time and number of example views. |
| `trial_order_exp2.csv` | 11,600 | The position of each Experiment 2 trial within its session (`order`). |
| `trial_validity.csv` | 11,600 | For each Experiment 2 trial, the number of edits, example views and submissions that the validity criteria are based on. |

`last_time` in the trial measures is not a session clock. Use `order` in `trial_order_exp2.csv` for the position of a trial within a session.

### Participants

Subject IDs are random strings assigned at the start of a session. Some participants in Experiment 2 completed the study more than once and therefore have more than one subject ID.

| File | Contents |
|---|---|
| `participant_roster.csv` | Every Experiment 2 session, the participant it belongs to (`person_id`), and whether it was that participant's first or second session. |
| `duplicate_participants.csv` | The subject IDs that belong to the same participant. |

## Inclusion criteria

Trials were excluded before release according to the criteria below.

**Experiment 1.** Ten pilot sessions (634 trials) that preceded the main data collection were excluded. The remaining 39 participants contributed 2,787 trials.

**Experiment 2.** Of the 14,107 trials recorded in 233 sessions, 11,600 trials from 192 participants were retained.

| Trials excluded | Criterion |
|---|---|
| 1,335 | Repeat attempt: the participant had attempted the problem in an earlier session |
| 664 | The session could not be linked to a Mechanical Turk worker (15 sessions) |
| 476 | The examples were not opened during the trial |
| 32 | The grid was not edited: every submission was blank or a copy of the test input |

Twenty-six participants completed Experiment 2 twice under different subject IDs. Each of these participants contributes the trials from their first session and any problem that they attempted only in their second session, so every participant has one trial per problem.

Analyses grouped by problem use all 11,600 trials. Analyses grouped by participant use 11,563 trials from the 185 participants with at least 12 valid trials.

`Behavioral data/trial_inclusion.csv` has one row per trial.

| Column | Meaning |
|---|---|
| `experiment` | 1 or 2 |
| `subject` | Subject ID |
| `trial` | ARC problem ID |
| `person_id` | The participant, who may have more than one subject ID |
| `record` | Whether the trial comes from a participant's only session, first session, or second session |
| `in_trial_level` | True for every trial; the trial is in the problem-level set |
| `in_group_level` | Whether the trial is also in the participant-level set |
| `exclusion_reason` | The reason, for trials outside the participant-level set |

## Common solutions

```
Common solutions/<task_id>.json/<task_id>_Success.json
Common solutions/<task_id>.json/<task_id>_Top Error <k>.json
Common solutions/common_solutions_index.csv
```

For each problem, the correct solution and every common error among first-attempt submissions in Experiment 2. A common error is an incorrect output grid that at least five participants submitted. There are 94 common errors across 50 problems, with one to five per problem. The other 25 problems have only a `Success` file.

Participants are counted once, so repeat sessions do not add to a count. Submissions that are blank or an unedited copy of the test input are not counted.

`common_solutions_index.csv` lists every file with the number of participants who submitted that grid. `Common solutions visualized/` holds a PNG of each grid.

## Grid format

All grids (task files, submissions and common solutions) are 2D arrays of integers, indexed as `grid[row][column]`. Each integer from 0 to 9 is a color.

| Value | Color | Hex |
|---|---|---|
| 0 | black (background) | `#2B2B2B` |
| 1 | blue | `#248ADA` |
| 2 | red | `#C71010` |
| 3 | green | `#1FC719` |
| 4 | yellow | `#F7DE28` |
| 5 | grey | `#878494` |
| 6 | pink | `#F954F2` |
| 7 | orange | `#EE6000` |
| 8 | purple | `#6B23A9` |
| 9 | brown | `#8B5A28` |

### Coordinates in the edit sequences

In the edit-sequence files, `x` is the row index and `y` is the column index. An edit with `x = 2, y = 5` sets `grid[2][5]`, and the flat index of a cell is `x * n_columns + y`.

Replaying the edit sequences with this convention reproduces the logged submission in all 1,875 trials that we checked across the 75 problems. An earlier version of this README stated the opposite convention.

## Analysis code

`analysis/` holds the code that produces every number and figure in the manuscript. See `analysis/README.md` for details.

```bash
cd analysis
python3 run_all.py
```

The run takes about two minutes and requires Python 3.9+ with pandas, numpy, scipy, matplotlib, seaborn and openpyxl. Summary tables are stored in `analysis/outputs/tables/`. Figures are not stored; the run writes them to `analysis/outputs/figures/`.

The participant screening survey is not distributed, as it contains Mechanical Turk worker IDs. The demographics tables derived from it are provided in aggregate in `analysis/outputs/tables/`.

## Data use

- Subject IDs are anonymized.
- The repository contains no individual-level demographic or personally identifying information.
- The data are released for research and educational use.

## Citation

If you use this dataset, please cite:

Ahn, C., Do, Q., Bakst, L., Pascale, M. P., McGuire, J. T., Hasselmo, M. E., & Stern, C. E. (2026). Exploring human behavior during abstract rule inference and problem solving with the Cognitive Abstraction and Reasoning Corpus. *arXiv preprint arXiv:2602.22408*. https://arxiv.org/abs/2602.22408

```bibtex
@article{ahn2026cogarc,
  title   = {Exploring Human Behavior During Abstract Rule Inference and Problem Solving with the Cognitive Abstraction and Reasoning Corpus},
  author  = {Ahn, Caroline and Do, Quan and Bakst, Leah and Pascale, Michael P. and McGuire, Joseph T. and Hasselmo, Michael E. and Stern, Chantal E.},
  journal = {arXiv preprint arXiv:2602.22408},
  year    = {2026},
  url     = {https://arxiv.org/abs/2602.22408}
}
```

## Contact

For questions about the dataset, please contact the authors of the associated manuscript.
