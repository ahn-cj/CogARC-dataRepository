# Common errors

A **common error** is a distinct incorrect output grid submitted by at least
five distinct participants on their first attempt at a problem. The set
contains **94 common errors across 50 of the 75 problems**, between one and
five per problem; the remaining 25 problems produced no incorrect solution that
five or more participants arrived at independently.

The grids are shipped in `Common solutions/`, one folder per problem, with
`common_solutions_index.csv` giving the participant count for each. Images of
the same grids are in `Common solutions visualized/`.

## How they are identified

For each problem, every first-attempt submission is compared cell by cell
against the correct output. Among the incorrect submissions, each distinct grid
is counted by the number of **distinct participants** who produced it, and any
grid reaching the threshold is a common error.

Four properties of that definition are worth stating, because each rules out a
way of over-counting:

**Grids are compared exactly.** Two submissions are counted together only when
every cell matches in both colour and position. No clustering, no distance
threshold, nothing that could merge distinct solutions. `top_cluster` naming in
earlier versions of these files was inherited from unrelated analyses and did
not reflect any clustering.

**The threshold counts people, not sessions.** Seventeen participants completed
Experiment 2 more than once under separate subject identifiers. A person who
submitted the same wrong grid in two sessions counts once.

**Candidates are ranked and counted on first attempts.** A grid that is common
only as a second- or third-attempt correction is a different thing from a
common first response: it is what someone produced after being told they were
wrong. Second and third attempts contribute to neither the ranking nor the
count.

**Every qualifying grid is counted.** A problem that elicited four or five
distinct shared errors contributes all of them; six problems have more than
three.

Two kinds of submission are never counted, however many people produced them:
an all-background grid, which is both the editor's starting state and what the
reset button produces, and a grid identical to the test input, which is what
the copy-input button produces. Neither reflects an inferred transformation.

## Reproducing them

```bash
cd analysis
PYTHONPATH=src python3 -m cogarc.common_errors     # identify the errors
python3 scripts/rebuild_common_solutions.py        # rewrite Common solutions/
```

## Recurrence in Experiment 1

The same incorrect solutions recur in the separate, in-person Experiment 1
sample: 68 of the 94 (72%) were also submitted by at least one Experiment 1
participant, and the frequency with which an error was made correlates across
the two experiments (Spearman rho = .47, *p* < .001).

`cogarc.experiment1.replication_of_exp2_errors()` computes this.
