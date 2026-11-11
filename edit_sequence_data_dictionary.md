------------------------------------------------------------
EDIT SEQUENCE CSV: DATA DICTIONARY
------------------------------------------------------------

Each edit-sequence CSV file records a time-ordered log of participant actions while solving a single CogARC problem.

Each row corresponds to one action event. Column definitions are listed below. Some columns may be unused or absent depending on experiment version or action type.


Common columns
----------------

time
    Time at which the action occurred, recorded relative to the start of the trial (in milliseconds).

rt
    Reaction time between actions (in milliseconds).

action
    Type of action performed. Common values include:
    - new        (load a new problem)
    - edit         (modify a single grid cell by clicking or dragging)
    - reset       (clear the current working grid)
    - copy       (copy over the test input grid)
    - showex   (open example view; Experiment 2 only)
    - hideex    (close example view; Experiment 2 only)
    - submit    (submit a solution attempt)


Grid-related columns (used for edit actions)
--------------------------------------------

x
    Column index of the edited cell (0-based).

y
    Row index of the edited cell (0-based).

color
    Integer value (0–9) specifying the color written to the cell.
    Color encodings are defined in the COLOR ENCODING LEGEND section.


Submission-related columns
--------------------------

outcome
    For edit actions: Boolean or binary indicator of whether the grid edit was correct (1 = correct, 0 = incorrect).
    For submission actions: Submission attempt result logged as either ‘success’ or ‘fail’.


Color encoding legend
--------------------------

0  = #2B2B2B  (black / background)
1  = #248ADA  (blue)
2  = #C71010  (red)
3  = #1FC719  (green)
4  = #F7DE28  (yellow)
5  = #878494  (grey)
6  = #F954F2  (pink)
7  = #EE6000  (orange)
8  = #6B23A9  (purple)
9  = #8B5A28  (brown)


Notes
-----

- Not all columns are populated for every action type.
  For example, x, y, and color are only meaningful for edit actions.
- The order of rows reflects the exact temporal sequence of actions.
- Grid coordinates (x, y) correspond directly to JSON grid indexing:
  grid[y][x].


------------------------------------------------------------
COORDINATE CONVENTION
------------------------------------------------------------

In the `x` and `y` columns of these files:

    x = ROW index
    y = COLUMN index

An edit with x = 2, y = 5 sets grid[2][5]. This is the opposite of the
Cartesian reading. Verified on 1,875 trials across all 75 problems, and on 324
trials from the 27 non-square problems where the two readings cannot be
confused: reading x as the row reproduces the logged submission for 100% of
trials, reading it as the column for about 5%.
