"""Write `Common solutions/` from the common-error definition.

For each problem, writes the correct output and every distinct incorrect grid
that at least five participants submitted on a first attempt, plus an index
giving the participant count for each. Regenerating this is how anyone can
confirm that the shipped folder matches what the code produces.

See `analysis/docs/common_errors.md` for the definition.
"""

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cogarc import paths
from cogarc.common_errors import find_common_errors, load_success_grids


def _reshape(flat, rows, cols):
    return [list(flat[i * cols:(i + 1) * cols]) for i in range(rows)]


errors = find_common_errors()
errors = errors[errors["qualifies"]]
success = load_success_grids()

shapes = {}
for f in sorted(paths.ARC_TASKS.glob("*.json")):
    grid = json.load(open(f))["test"][0]["output"]
    shapes[f.stem] = (len(grid), len(grid[0]))

root = paths.COMMON_SOLUTIONS_OUT
if root.exists():
    shutil.rmtree(root)
root.mkdir(parents=True)

index = []
for task, correct in sorted(success.items()):
    rows, cols = shapes[task]
    d = root / f"{task}.json"
    d.mkdir()
    with open(d / f"{task}_Success.json", "w") as fh:
        json.dump({"grid_data": _reshape(correct, rows, cols)}, fh, indent=2)
    index.append({"task": task, "solution": "Success", "n_participants": None})

    block = errors[errors["task"] == task].sort_values("error")
    for i, r in enumerate(block.itertuples(), start=1):
        name = f"{task}_Top Error {i}.json"
        with open(d / name, "w") as fh:
            json.dump({"grid_data": _reshape(r.grid, rows, cols)}, fh, indent=2)
        index.append({"task": task, "solution": f"Top Error {i}",
                      "n_participants": int(r.n_participants)})

idx = pd.DataFrame(index)
idx.to_csv(root / "common_solutions_index.csv", index=False)

n_err = int(idx["solution"].str.startswith("Top Error").sum())
per = idx[idx["solution"].str.startswith("Top Error")].groupby("task").size()
print(f"wrote {root}")
print(f"  75 problems, {n_err} common errors across {len(per)} problems")
print(f"  {75 - len(per)} problems have none")
print(f"  errors per problem: {per.value_counts().sort_index().to_dict()}")
print(f"  participants per error: median {idx.n_participants.median():.0f}, "
      f"range {idx.n_participants.min():.0f}-{idx.n_participants.max():.0f}")
