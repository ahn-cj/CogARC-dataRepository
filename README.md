Boston University CogARC Data Repository

This repository contains behavioral and task data associated with the Cognitive Abstraction and Reasoning Corpus (CogARC), a human behavioral dataset based on the Abstraction and Reasoning Corpus (ARC). The data accompany two online experiments reported in the associated manuscript.

The repository includes participant edit sequences, submission grids, task metadata, common solution patterns, and problem annotations intended to support reproducibility, secondary analyses, and comparative modeling of human abstract reasoning behavior.


------------------------------------------------------------
OVERVIEW OF CONTENTS
------------------------------------------------------------

CogARC-dataRepository/
├── Behavioral data/
│   ├── Experiment 1/
│   ├── Experiment 2/
│   ├── subject_task_sequence_measures_mturk.csv
│   ├── subject_task_sequence_measures_zoom.csv
│   ├── behavioral_measures.csv
│   ├── trial_scores.csv
│   ├── trial_validity.csv
│   ├── trial_inclusion.csv
│   ├── participant_roster.csv
│   └── duplicate_participants.csv
├── Task JSONs/
├── Task example PNGs/
├── Common solutions/
├── Common solutions visualized/
├── Task tags.csv
├── analysis/
├── edit_sequence_data_dictionary.md
└── README.md


------------------------------------------------------------
WHICH TRIALS ENTER THE ANALYSES
------------------------------------------------------------

The raw files hold every trial collected. Nothing has been removed. Which
trials enter the analyses reported in the manuscript is recorded separately, in

    Behavioral data/trial_inclusion.csv

one row per trial, with columns:

    experiment          1 or 2
    subject             session identifier, as in the raw files
    trial               ARC problem id
    person_id           the person, which may span two sessions
    record              session_1 / novel_in_later / sole_session /
                        repeat_session / unattributed_session / pilot
    in_trial_level      whether the trial enters analyses grouped by problem
    in_group_level      whether it also enters analyses grouped by participant
    exclusion_reason    why not, where it does not

The manuscript uses two sets. Analyses grouped by problem, such as problem
difficulty and the common errors, use every valid trial (the problem-level
set, column in_trial_level). Analyses grouped by participant drop the
participants with fewer than 12 valid trials (the participant-level set,
column in_group_level).
To reproduce either, join on (experiment, subject, trial) and keep the
matching column.

    Experiment 1: 3,421 trials, 2,787 in analysis, 39 people
        634  lab pilot, run before the main collection

    Experiment 2: 14,107 trials, 11,600 problem-level,     192 people
                              11,563 participant-level, 185 people
      1,335  repeat session: this problem was already attempted earlier
        664  session could not be attributed to a person
        476  examples never opened at any point in the trial
         32  never edited the grid: every submission was the input copied
             over or left blank

Twenty-six participants in Experiment 2 completed the study more than once
under separate subject identifiers. Their sessions are all present in the raw
files; Behavioral data/participant_roster.csv names every session in the
sample and the person it belongs to. Analyses keep the first session per
person, plus any problem a person met only in a later session. The repeat
sessions are retained here because 1,335 problems were attempted twice by the
same person, which is a rare source of test-retest data on ARC.

Fifteen further sessions could not be attributed to a person at all, because
the completion code the participant typed did not resolve to a Mechanical Turk
worker. They are kept in the raw files and excluded from the analyses, since
each could be an unrecognised return visit.

------------------------------------------------------------
ANALYSIS CODE
------------------------------------------------------------

analysis/
├── src/cogarc/        analysis modules
├── scripts/           regenerate the files shipped here
├── docs/              how common errors are identified
├── outputs/tables/    summary results
└── run_all.py         runs everything, about two minutes

Figures are not stored; run_all.py regenerates them into
analysis/outputs/figures/.

Every path resolves inside this repository, so a clone runs without
configuration:

    cd analysis
    python3 run_all.py

Requires Python 3.9+, pandas, numpy, scipy, matplotlib, seaborn, openpyxl.

One input is NOT distributed: the participant screening survey, which carries
Mechanical Turk worker IDs and participant initials. The tables derived from it
are shipped de-identified in analysis/outputs/tables/, and the modules that
read it fail with an explanatory message rather than silently producing
different numbers. Set COGARC_PRIVATE to that directory to regenerate them.


------------------------------------------------------------
BEHAVIORAL DATA
------------------------------------------------------------

Behavioral data are organized by experiment and problem, with separate folders for different data modalities.


Experiments
-----------
Experiment 1:
    First online behavioral experiment (Boston University sample)

Experiment 2:
    Second online behavioral experiment (MTurk sample)

The internal folder structure is identical across experiments.


------------------------------------------------------------
SUBMISSIONS
------------------------------------------------------------

Behavioral Data/
└── Experiment X/
    └── Submissions/
        └── <task_id>.json/
            ├── <task_id>_<subject_id>_submission1.json
            ├── <task_id>_<subject_id>_submission2.json
            └── ...

Each file contains the submitted output grid for a single participant attempt on a given task.

Notes:
- Multiple submission files may exist per participant if they made multiple attempts.
- Files are JSON-formatted and store the grid as a 2D integer array.
- Subject IDs are anonymized and contain no identifying information.


------------------------------------------------------------
EDIT SEQUENCES
------------------------------------------------------------

Behavioral Data/
└── Experiment X/
    └── Edit sequences/
        └── <task_id>.json/
            ├── subj_<subject_id>_trial_<task_id>.json.csv
            └── ...

Each CSV file contains a time-ordered sequence of participant actions during problem solving for a single problem.

Typical actions include:
- cell edits
- resets
- example viewing events (experiment 2 only)
- submission events

Cell edit events specify grid locations using (x, y) coordinates and a color value. These coordinates correspond directly to the indexing used in the JSON grid representations described below.

These files enable reconstruction of participant trajectories and fine-grained analyses of problem-solving behavior. For a full index of possible actions, refer to the edit_sequence_data_dictionary.md file.


------------------------------------------------------------
GRID ENCODING AND COORDINATE SYSTEM
------------------------------------------------------------

All grids in this repository (task JSONs, submission JSONs, and common solution JSONs) are stored as a 2D matrix (array of arrays) of integers.

- Grid format: grid[row][column]
- Values range from 0 to 9
- Each integer encodes a specific color on the grid
- 0 represents the background / empty cell


Edit-sequence coordinates
-------------------------
IMPORTANT: the `x` and `y` columns in the edit-sequence CSV files do NOT follow
the Cartesian convention. In those files:

    x = ROW index
    y = COLUMN index

so an edit event with x = 2, y = 5 sets grid[2][5].

Reconstructing a grid with the intuitive reading (x as the column) reproduces
the logged submission for about 5% of trials. Reading x as the row reproduces
it for 100%: verified on 1,875 trials across all 75 problems, and on 324 trials
drawn only from the 27 non-square problems, where the two readings cannot be
confused.

In Python:

    flat_index = x * n_columns + y

An earlier version of this README documented the opposite convention. Analyses
that reconstructed grid states from the edit sequences using that description
will not have reproduced the submitted grids.


COLOR ENCODING LEGEND
------------------------------------------------------------

The following integer-to-color mapping is used consistently across all JSON grids and edit-sequence files:

0  = #2B2B2B  (background / empty)
1  = #248ADA  (blue)
2  = #C71010  (red)
3  = #1FC719  (green)
4  = #F7DE28  (yellow)
5  = #878494  (grey)
6  = #F954F2  (pink)
7  = #EE6000  (orange)
8  = #6B23A9  (purple)
9  = #8B5A28  (brown)


------------------------------------------------------------
TASK FILES
------------------------------------------------------------

Task JSONs
----------
Task JSONs/
├── <task_id>.json
└── ...

These files contain the original ARC-style task files, including training input-output pairs and test input-output. They define the problem structure presented to participants.


Task Example PNGs
-----------------
Task example PNGs/
├── <task_id>.json.png
└── ...

Static visualizations of the problem examples corresponding to each task, included for reference and documentation.


------------------------------------------------------------
COMMON SOLUTIONS
------------------------------------------------------------

Common solutions/
└── <task_id>.json/
   ├── <task_id>_Success.json
   ├── <task_id>_Top Error 1.json
   └── ...

This folder contains, for each problem, the correct solution and every common error identified from first-attempt submissions in Experiment 2.

A common error is a distinct incorrect output grid submitted by at least five distinct participants. The set contains 94 common errors across 50 problems, between one and five per problem. The remaining 25 problems produced no incorrect solution that five or more participants arrived at independently, and so have only a Success file.

common_solutions_index.csv lists every file with the number of participants who submitted it.

The threshold counts distinct people rather than sessions: 26 participants completed Experiment 2 more than once, and their repeat submissions are not double-counted. Submissions consisting of an unedited grid, either all background or an unmodified copy of the test input, are excluded, as neither reflects an inferred transformation.




------------------------------------------------------------
COMMON SOLUTIONS (VISUALIZED)
------------------------------------------------------------

Common solutions visualized/
└── <task_id>.json/
   ├── <task_id>_Success.json.png
   ├── <task_id>_Top Error 1.json.png
   └── ...

PNG visualizations of the common solutions are provided for quick inspection and qualitative comparison.


------------------------------------------------------------
TASK ANNOTATIONS
------------------------------------------------------------

Task tags.csv

This file contains experimenter-provided annotations for each problem, including:
- task ID
- experimenter-rated problem complexity
- core knowledge category labels
  (objectness [Obj], geometry & patterns [Geo],
   goal-directedness [GoD], and numbers & counting [Num])

These annotations were used in analyses reported in the associated manuscript.


------------------------------------------------------------
NOTES ON DATA USE
------------------------------------------------------------

- All subject identifiers are anonymized.
- No individual-level demographic or personally identifying information is included. Demographics are reported in aggregate in analysis/outputs/tables/.
- Data are released for research and educational use.
- When using this dataset, please cite the associated CogARC manuscript.


------------------------------------------------------------
CITATION
------------------------------------------------------------

If you use this dataset, please cite:

[Manuscript citation to be added]


------------------------------------------------------------
CONTACT
------------------------------------------------------------

For questions or issues related to this dataset, please contact the authors of the associated manuscript.
