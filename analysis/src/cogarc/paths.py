"""Canonical file locations for the CogARC analyses.

Every path resolves inside this repository, so a clone runs without
configuration. The one exception is the participant demographics survey, which
carries Mechanical Turk worker IDs and participant initials and is therefore
NOT distributed. The derived, de-identified demographics table is shipped in
`analysis/outputs/tables/` instead; `demographics.py` regenerates it only when
the private source is present.
"""

import os as _os
from pathlib import Path

# analysis/src/cogarc/paths.py -> the repository root
REPO = Path(__file__).resolve().parents[3]

# COGARC_OUTPUT_SUFFIX sends everything a run generates -- derived data,
# tables, figures, the inclusion table and the rebuilt common solutions -- to
# parallel names, so an alternative sample can be analysed end to end without
# touching the shipped files.
_suffix = _os.environ.get("COGARC_OUTPUT_SUFFIX", "")
ANALYSIS = REPO / "analysis"

# --- data shipped with this repository --------------------------------------
DATA_REPO = REPO / "Behavioral data"
EXP1 = DATA_REPO / "Experiment 1"
EXP2 = DATA_REPO / "Experiment 2"

# Per-trial behavioral measures.
# Experiment 2 (Mechanical Turk): 14,107 rows, 233 sessions.
SEQ_MEASURES_MTURK = DATA_REPO / "subject_task_sequence_measures_mturk.csv"
# Experiment 1 (remote-supervised): 3,421 rows, 49 sessions.
SEQ_MEASURES_ZOOM = DATA_REPO / "subject_task_sequence_measures_zoom.csv"
# Carries the true trial `order` column -- see ORDER_WARNING below.
# Trial-level measures with the within-session trial `order`, which exists
# nowhere else. behavioral_measures_filtered.csv, which this replaces, had the
# old "at least ten successful trials" subject filter baked in, so the fifteen
# subjects below that line carried no order and silently dropped out of every
# within-session analysis regardless of the sample definition. This file is the
# same merge with that filter removed: 14,107 rows, all 233 sessions.
BEHAVIORAL_MEASURES = DATA_REPO / "behavioral_measures.csv"
BEHAVIORAL_FILTERED = BEHAVIORAL_MEASURES  # old name, kept for callers
TRIAL_SCORES = DATA_REPO / "trial_scores.csv"

# Submitted grids, one file per participant attempt.
SUBMISSIONS = EXP2 / "Submissions"
SUBMISSIONS_EXP1 = EXP1 / "Submissions"

# Logged edit sequences, one file per trial.
EDIT_SEQUENCES = EXP2 / "Edit sequences"
EDIT_SEQUENCES_EXP1 = EXP1 / "Edit sequences"

# The 75 ARC problems, and the correct output plus common errors for each.
ARC_TASKS = REPO / "Task JSONs"
# The canonical set of solution grids, read by every run. The Success grid for
# each problem is reference data, not something a sample determines.
COMMON_SOLUTIONS = REPO / "Common solutions"

# Where a run WRITES its rebuilt solutions. Identical to the above for a normal
# run; a suffixed run writes alongside instead of over it.
COMMON_SOLUTIONS_OUT = REPO / f"Common solutions{_suffix}"
TASK_TAGS = REPO / "Task tags.csv"

# --- private input, not distributed -----------------------------------------
# The screening survey links subject IDs to Mechanical Turk worker IDs and
# holds initials, age and other responses. It stays out of the repository.
# Set COGARC_PRIVATE to its parent directory to regenerate the demographics
# table; otherwise the shipped table is used as-is.

_private = _os.environ.get("COGARC_PRIVATE")
PRIVATE = Path(_private).expanduser() if _private else None
DEMOGRAPHICS = (
    PRIVATE / "ARC Screening & Demographics Survey_July 27, 2023_09.33.csv"
    if PRIVATE else None
)
DEMOGRAPHICS_LINKED = (
    PRIVATE / "ARC Screening & Demographics Survey_with_subjectIDs.csv"
    if PRIVATE else None
)
# The complete Qualtrics exports, pulled 2026-08-29. These supersede the
# July 2023 files above, which are a working subset: 84 eligible responses
# carrying a worker ID are absent from them, spread across every collection
# date. The full exports also carry the response timestamps and ResponseId
# needed to recover the June 13-14 responses (see demographics.RECOVERED).
QUALTRICS_FULL = PRIVATE / "qualtrics full exports" if PRIVATE else None
SCREENING_FULL = (
    QUALTRICS_FULL / "ARC Screening & Demographics Survey_August 29, 2026_09.51.csv"
    if PRIVATE else None
)
CONSENT_FULL = (
    QUALTRICS_FULL / "ARC Behavioral Informed Consent Form_August 29, 2026_09.50.csv"
    if PRIVATE else None
)
ENVIRONMENT_FULL = (
    QUALTRICS_FULL / "ARC Testing Environment Survey_August 29, 2026_10.14.csv"
    if PRIVATE else None
)

COMPLETION_CODES = PRIVATE / "completion codes" if PRIVATE else None
SUBJECT_LOG = PRIVATE / "ARC online subject log.xlsx" if PRIVATE else None

# --- outputs written by the analysis ----------------------------------------
# The roster names every session in the sample and the person it belongs to,
# so it both restricts the data and defines the grouping. The shipped file is
# the hand-adjudicated sample reported in the manuscript, with the Mechanical
# Turk worker IDs and session timestamps that identified people removed; it is
# the default so that a fresh clone reproduces the published numbers (192
# people and 11,600 valid trials; 185 and 11,563 for analyses of means).
#
# COGARC_ROSTER overrides it with another CSV of the same shape, for analysing
# an alternative sample definition without editing the shipped one. Pointing it
# at a roster that still carries a `worker` column also lets the demographics
# table be rebuilt from the private survey export.
ROSTER_SHIPPED = REPO / "Behavioral data" / "participant_roster.csv"
_roster = _os.environ.get("COGARC_ROSTER")
ROSTER = Path(_roster).expanduser() if _roster else ROSTER_SHIPPED

# COGARC_OUTPUT_SUFFIX writes a run's derived data, tables and figures to
# parallel directories, so an alternative sample definition can be built
# without overwriting the main one.
DERIVED = ANALYSIS / f"data_derived{_suffix}"
TABLES = ANALYSIS / f"outputs/tables{_suffix}"
FIGURES = ANALYSIS / f"outputs/figures{_suffix}"

DUPLICATE_LIST = DERIVED / "duplicate_participants.csv"
ANALYSIS_SAMPLE = DERIVED / "analysis_sample.csv"
# The inclusion flags shipped alongside the data.
TRIAL_INCLUSION = DATA_REPO / f"trial_inclusion{_suffix}.csv"

# The two trial-level validity checks, written by scripts/build_trial_validity.py.
TRIAL_VALIDITY = DATA_REPO / "trial_validity.csv"
# De-identified list of people holding more than one subject ID.
DUPLICATES_PUBLIC = DATA_REPO / "duplicate_participants.csv"

for _d in (DERIVED, TABLES, FIGURES):
    _d.mkdir(parents=True, exist_ok=True)

# --- analysis constants -----------------------------------------------------
# `last_time` in SEQ_MEASURES_MTURK is NOT a session clock; ranking trials by
# it correlates about -0.2 with true order. Use `order` in BEHAVIORAL_MEASURES.
ORDER_WARNING = "Use behavioral_measures.order, never last_time."

# Subject fl73adm5 / problem 82819916 records a 44-hour deliberation time (an
# unattended browser session), 35x the next largest trial. Timing analyses drop
# trials above this bound and aggregate by median or on the log scale.
DELIBERATION_MAX_MS = 2 * 60 * 60 * 1000  # 2 hours

# Quality control: participants must have solved more than this many problems.
# Set COGARC_MIN_SOLVED to override, and to -1 to drop the rule entirely.
#
# The rule predates the trial-level validity checks in TRIAL_VALIDITY, which
# now remove the trials a disengaged participant produces. What it removes on
# top of those is people whose remaining trials are valid but few or mostly
# wrong -- that is, it selects on the outcome rather than on the behaviour.
#
# Checked directly on the seven participants it excludes from the adjudicated
# sample. For each, the rank correlation between their own per-trial difficulty
# outcome and how hard those problems were for everyone else, leave-one-out so
# nobody contributes to their own benchmark; a random responder scores zero:
#
#     y8mzyzjc  73 trials  rho +0.69     0fy66fv2  17 trials  rho +0.56
#     nsu6cwh4   6 trials  rho +0.51     4kl3i3tv  17 trials  rho +0.50
#     ihnjt6k4  19 trials  rho +0.48     wz0zoo1d   4 trials  too few to score
#                                        1xogp17t   3 trials  too few to score
#
# against a median of +0.51 across the other 185 participants, 72 of whom
# score below the weakest of the seven. Their median deliberation runs longer
# than the sample median, not shorter, and the split-half reproducibility of
# the problem ordering is slightly HIGHER with them included (Spearman-Brown
# 0.9494 against 0.9475). So the rule is not separating signal from noise; it
# is trimming the low tail of a continuum. The rule was therefore dropped: the
# default is -1, which keeps everyone, and the manuscript applies no threshold
# on problems solved. Set COGARC_MIN_SOLVED to reinstate one.
MIN_PROBLEMS_SOLVED = int(_os.environ.get("COGARC_MIN_SOLVED", -1))

# A participant must have at least this many valid trials for their own mean
# to be worth comparing with anyone else's. Set COGARC_MIN_TRIALS to override,
# and to -1 to drop the rule. Unlike MIN_PROBLEMS_SOLVED this selects on how
# much evidence there is, not on how well the person did.
#
# Chosen from the data two ways, which agree. Taking the 133 participants with
# 60 or more trials and drawing n of their trials at random, the n-trial
# estimate recovers their own full-session accuracy at r = .78 for n = 10 and
# .82 for n = 12; split-half reliability of accuracy reaches the conventional
# .70 at n = 12. Separately, the sample contains nobody with between 10 and 16
# trials, so any cutoff in that range selects the same people -- the choice
# sits in an empty region of the distribution and cannot be tuned.
#
# It removes seven participants and 37 trials, 0.3% of the sample. A stricter
# n = 25 would reach .80 reliability, the criterion for comparing individuals,
# but costs 2.2% of the trials and falls in a densely populated part of the
# distribution; the per-participant analyses handle precision by weighting
# instead (see trends.py).
MIN_TRIALS_ATTEMPTED = int(_os.environ.get("COGARC_MIN_TRIALS", 12))

# A submitted output counts as a common error when this many distinct
# PARTICIPANTS (not sessions) submit an identical incorrect grid.
COMMON_ERROR_MIN_PARTICIPANTS = 5

# Candidate errors kept per problem. 0 means every distinct grid meeting the
# participant threshold is counted, which is what the analyses use.
COMMON_ERROR_MAX_PER_PROBLEM = 0

# In the logged edit sequences `x` is the ROW index and `y` the COLUMN.
# Replaying with the intuitive `y * cols + x` reproduces the logged submission
# for about 5% of trials; with `x * cols + y` it reproduces 100%.
GRID_INDEX_NOTE = "x is the row, y is the column: idx = x * n_cols + y"

# Three clocks appear in the study records, and none of them agree.
#
#   task logs        `start_time` in the session JSONs is the PARTICIPANT'S
#                    BROWSER clock, written by the client, and carries whatever
#                    zone that machine was set to. Thirteen zones appear across
#                    the 234 sessions -- 115 Eastern, 54 Central, 35 Pacific,
#                    9 East Africa, 7 Mountain, and singletons as far out as
#                    Hawaii, Pakistan and Bangladesh. Each string states its own
#                    offset ("GMT-0400 (Eastern Daylight Time)"), so a session
#                    can be converted, but only one at a time. Applying a single
#                    offset to all of them is wrong for more than half.
#
#   Qualtrics        consent, screening and environment exports are stamped in
#                    Mountain Time. Verified against the sessions once each was
#                    converted to UTC: the median gap between a consent
#                    submission and the start of that participant's session is
#                    13 minutes under UTC-6, against 73 minutes under Central
#                    and 133 under Eastern. The collection window is entirely
#                    within daylight saving, so UTC-6 throughout; a response
#                    outside it would be UTC-7.
#
#   CloudResearch    the completion-code exports are stamped in UTC. Under that
#                    reading 186 of 187 known assignment/session pairs fall in a
#                    plausible window, median 25 minutes from accepting the HIT
#                    to starting the task.
#
# Nothing in the analysis depends on wall-clock time -- trial timing comes from
# millisecond offsets within a session -- and no wall-clock stamp is
# distributed with the repository. The note is here for anyone linking these
# records to each other later.
TIMEZONE_NOTE = (
    "Session start_time is the participant's browser clock (13 zones, each "
    "stating its own offset); Qualtrics exports are Mountain Time; "
    "CloudResearch exports are UTC."
)
