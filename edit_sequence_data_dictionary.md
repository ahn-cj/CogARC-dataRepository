# Edit sequence data dictionary

Each edit-sequence CSV file is the log of one trial: one participant working on one problem. Each row is one action, in the order it occurred.

## Columns

| Column | Meaning |
|---|---|
| `action` | The type of action (see below) |
| `x` | Row index of the edited cell, 0-based (edit actions only) |
| `y` | Column index of the edited cell, 0-based (edit actions only) |
| `color` | Integer from 0 to 9, the color written to the cell (edit actions only) |
| `time` | Time of the action in milliseconds from the start of the trial |
| `rt` | Time since the previous action, in milliseconds |
| `outcome` | For an edit, whether the cell now matches the correct solution (1) or not (0). For a submission, `success` or `fail`. |
| `type` | `click` or `drag`, for edit actions. Present only in `Edit sequences typed/` (Experiment 2). |

## Actions

| Action | Meaning |
|---|---|
| `new` | A new problem is loaded |
| `edit` | One grid cell is colored, by clicking or dragging |
| `reset` | The working grid is cleared |
| `copy` | The test input is copied to the working grid |
| `showex` | The examples are opened (Experiment 2 only) |
| `hideex` | The examples are closed (Experiment 2 only) |
| `submit` | A solution attempt is submitted |

## Coordinates

`x` is the row index and `y` is the column index. An edit with `x = 2, y = 5` sets `grid[2][5]`, and the flat index of a cell is `x * n_columns + y`.

Replaying the edit sequences with this convention reproduces the logged submission in all 1,875 trials that we checked across the 75 problems.

## Colors

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
