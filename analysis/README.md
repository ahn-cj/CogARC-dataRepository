# CogARC analysis code

Code for the analyses in the CogARC behavioral manuscript. All paths resolve inside this repository, so a clone runs without configuration.

```bash
cd analysis
python3 run_all.py
```

The run takes about two minutes. Modules can also be run individually:

```bash
PYTHONPATH=src python3 -m cogarc.sample     # build the analysis sample
PYTHONPATH=src python3 -m cogarc.figures    # regenerate the figures
```

Requires Python 3.9+ with pandas, numpy, scipy, matplotlib, seaborn and openpyxl.

## Layout

| Path | Contents |
|---|---|
| `src/cogarc/` | Analysis modules |
| `scripts/` | Scripts that regenerate data files shipped in this repository |
| `docs/common_errors.md` | How common errors are identified |
| `outputs/tables/` | Summary tables, stored in the repository |
| `outputs/figures/` | Figures, written by `run_all.py` and not stored |
| `data_derived/` | Intermediate files, written by `run_all.py` and not stored |

## Modules

| Module | Purpose |
|---|---|
| `paths.py` | File locations and analysis constants |
| `sample.py` | Applies the inclusion rules and writes `data_derived/analysis_sample.csv`, which every other module reads |
| `duplicates.py` | Participants with more than one subject ID |
| `identity.py` | Links subject IDs to worker IDs (requires the private survey) |
| `demographics.py` | Demographics table and its relation to accuracy (requires the private survey) |
| `descriptives.py` | Participant and problem summaries, task properties |
| `common_errors.py` | Identifies common errors |
| `edit_sequences.py` | Edit similarity and normalized extra steps |
| `correlates.py` | Correlates of problem difficulty |
| `trends.py` | Change over the course of a session |
| `trajectories.py` | Grid state at every step of an edit sequence |
| `experiment1.py` | Experiment 1 analyses |
| `figures.py` | Manuscript figures |
| `visualize_grids.py` | Images of the common solutions |

## Analysis sample

The repository contains the analyzed trials, and the exclusions are described in the main README. `sample.py` assigns each trial to a participant and defines the two Experiment 2 analysis sets.

| Set | Participants | Trials | Used for |
|---|---|---|---|
| Experiment 2, problem level | 192 | 11,600 | Analyses grouped by problem |
| Experiment 2, participant level | 185 | 11,563 | Analyses grouped by participant (at least 12 valid trials) |
| Experiment 1 | 39 | 2,787 | All Experiment 1 analyses |

## Notes on the data

- `last_time` is not a session clock. Use `order` in `trial_order_exp2.csv` for the position of a trial within a session.
- In the edit sequences, `x` is the row and `y` is the column.
- One trial records 44 hours of deliberation time, from a browser that was left open. Timing analyses exclude trials over two hours.
- The common-error threshold counts participants, not sessions or submissions.

## Scripts

| Script | Output |
|---|---|
| `build_trial_validity.py` | `Behavioral data/trial_validity.csv` |
| `build_trial_inclusion.py` | `Behavioral data/trial_inclusion.csv` |
| `rebuild_common_solutions.py` | `Common solutions/` |
| `rebuild_common_solutions_visualized.py` | `Common solutions visualized/` |

## Summary tables

| File in `outputs/tables/` | Contents |
|---|---|
| `participant_summary.csv` | One row per participant: problems attempted, accuracy by attempt |
| `problem_summary.csv` | One row per problem: accuracy, first-attempt success, difficulty, deliberation time |
| `problem_correlates.csv` | Problem-level measures joined to task properties |
| `difficulty_correlations.csv` | Correlations with problem difficulty (Spearman and Pearson) |
| `complexity_pairwise.csv` | Difficulty by rated complexity, FDR corrected |
| `common_errors.csv` | Every common error with its participant count |
| `edit_sequence_measures.csv` | Edit similarity and normalized extra steps per problem |
| `trend_slopes.csv`, `participant_trend_slopes.csv` | Change over the session |
| `measures_by_trial_order.csv` | Each measure at each trial position |
| `exp1_participant_summary.csv`, `exp1_problem_summary.csv` | The same summaries for Experiment 1 |
| `demographics.csv`, `demographics_vs_accuracy.csv`, `demographics_group_means.csv` | Demographics in aggregate and their relation to accuracy |
| `RUN_INFO.txt` | Settings and sample sizes of the run that wrote the tables |

## Private input

The participant screening survey contains Mechanical Turk worker IDs and is not distributed. The demographics tables derived from it are stored in `outputs/tables/`, and `run_all.py` skips the demographics step when the survey is absent. To regenerate the tables, set `COGARC_PRIVATE` to the directory that holds the survey export.

## Settings

The defaults reproduce the manuscript. These environment variables change what a run analyzes and where it writes.

| Variable | Effect |
|---|---|
| `COGARC_ROSTER` | Path to a different roster |
| `COGARC_MIN_TRIALS` | Valid trials required for the participant-level set (default 12) |
| `COGARC_MIN_SOLVED` | Minimum number of problems solved (default: no minimum) |
| `COGARC_PRIVATE` | Directory that holds the screening survey export |
| `COGARC_OUTPUT_SUFFIX` | Suffix added to the output folders and files, so a run does not overwrite the stored ones |
