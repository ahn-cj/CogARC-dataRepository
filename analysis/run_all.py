"""Run every analysis in order and report what each produced.

Usable from a fresh clone: no configuration, no required ordering.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ("cogarc.duplicates", "people holding more than one subject ID"),
    ("cogarc.sample", "build the analysis sample"),
    ("cogarc.descriptives", "participant and problem summaries"),
    ("cogarc.edit_sequences", "edit similarity and extra steps"),
    ("cogarc.common_errors", "common errors"),
    ("cogarc.correlates", "what predicts difficulty"),
    ("cogarc.trends", "change over the session"),
    ("cogarc.experiment1", "Experiment 1"),
    ("cogarc.demographics", "participant demographics"),
    ("cogarc.visualize_grids", "grid images"),
    ("cogarc.figures", "every manuscript figure"),
]
SCRIPTS = [
    ("scripts/build_trial_validity.py", "trial validity checks"),
    ("scripts/build_trial_inclusion.py", "trial inclusion flags"),
    ("scripts/rebuild_common_solutions.py", "Common solutions/"),
    ("scripts/rebuild_common_solutions_visualized.py", "Common solutions visualized/"),
]


def run(cmd, label, what):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": "src"})
    ok = r.returncode == 0
    print(f"  {'ok  ' if ok else 'FAIL'} {label:38s} {what}  ({time.time()-t0:.0f}s)")
    if not ok:
        print("\n".join("        " + l for l in r.stderr.strip().splitlines()[-6:]))
    return ok



def stamp_run():
    """Record what produced these outputs, next to the outputs themselves.

    Two runs of this pipeline give different samples depending on whether
    COGARC_ROSTER is set, and the files they write are otherwise
    indistinguishable. Writing the settings and the resulting counts into each
    output directory means a file's provenance can be checked without
    rerunning anything.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from datetime import datetime, timezone

    import pandas as pd

    from cogarc import paths

    env = {k: os.environ.get(k) for k in
           ("COGARC_ROSTER", "COGARC_MIN_SOLVED", "COGARC_MIN_TRIALS",
            "COGARC_OUTPUT_SUFFIX", "COGARC_PRIVATE")}
    lines = [f"written {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}", ""]
    lines += [f"{k} = {v if v else '(unset)'}" for k, v in env.items()]

    try:
        s = pd.read_csv(paths.ANALYSIS_SAMPLE)
        valid = s[s["valid_trial"]]
        group = valid[valid["enough_trials"] & valid["passes_qc"]]
        lines += ["",
                  f"problem-level set:      {valid['person_id'].nunique()} people, "
                  f"{len(valid):,} trials",
                  f"participant-level set:  {group['person_id'].nunique()} people, "
                  f"{len(group):,} trials"]
    except Exception as exc:                      # the sample may not exist yet
        lines += ["", f"sample not readable: {exc}"]

    if paths.ROSTER == paths.ROSTER_SHIPPED:
        lines += ["", "roster: the shipped one, so this is the sample the "
                  "manuscript reports."]
    else:
        lines += ["", f"ROSTER OVERRIDDEN with {paths.ROSTER}, so this sample "
                  "may differ from the one the manuscript reports."]

    for folder in (paths.TABLES, paths.FIGURES):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "RUN_INFO.txt").write_text("\n".join(lines) + "\n")


print("modules")
failed = [l for m, w in STEPS
          if not run([sys.executable, "-m", m], m.split(".")[-1], w) for l in [m]]
print("\nscripts")
failed += [s for s, w in SCRIPTS
           if not run([sys.executable, s], Path(s).stem, w)]

print(f"\n{len(STEPS) + len(SCRIPTS) - len(failed)} of "
      f"{len(STEPS) + len(SCRIPTS)} succeeded")

stamp_run()
sys.exit(1 if failed else 0)
