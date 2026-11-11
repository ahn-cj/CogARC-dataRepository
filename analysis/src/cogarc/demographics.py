"""Demographics table for the Experiment 2 analysis sample.

One row per person, not per session: a participant who completed the study
twice contributes their demographics once.

Coverage is incomplete and is reported alongside the table rather than hidden.
Of the 199 people in the analysis sample, 162 can be linked to a Mechanical
Turk worker ID; the remaining 37 never appear in a completion-code export,
because the code a participant typed to claim payment is their subject ID and
some entered it incorrectly.

Among the 162, 159 have a demographics record: 151 matched directly on worker
ID, and eight recovered by hand. The screening survey did not record the worker
ID for responses submitted on 13-14 June 2023 -- every response those two days
has a blank workerId, and the problem was fixed on 15 June -- so those
responses are orphaned. See RECOVERED for how they are matched back.

Percentages are reported over the number of people answering each item, and
that denominator is printed with the table.
"""

from __future__ import annotations

import json
import sys

import pandas as pd

from . import paths
from .identity import subject_to_worker
from .sample import load_sample, trial_level_sample


# Raw survey values -> the categories reported in the table.
WORK_STATUS = {
    "Working full-time": "Working full-time",
    "Working part-time": "Working part-time",
    "Keeping house or raising children full-time": "Keeping house full-time",
    "Looking for work": "Looking for work",
    "Full-time student": "Full-time student",
    "Unemployed or laid off": "Unemployed",
    "Retired": "Retired",
}
DEGREE = {
    "Bachelor's degree": "Bachelor's degree",
    "High school diploma or equivalency (GED)": "High school diploma or equivalency",
    "Master's degree": "Master's degree",
    "Associate degree (junior college)": "Associate degree",
    "Doctorate": "Doctorate",
    "Professional (MD, JD, DDS, etc.)": "Professional",
    "None of the above (less than high school)": "None of the above",
}
RACE = {
    "White": "White",
    "Black or African American": "Black or African American",
    "Asian": "Asian",
    "American Indian or Alaska Native": "American Indian or Alaska Native",
    "Native Hawaiian or Pacific Islander": "Native Hawaiian or Pacific Islander",
}


def _collapse_race(value) -> str:
    """A comma-joined response means more than one race was selected."""
    if pd.isna(value) or not str(value).strip():
        return "Not reported"
    parts = [p.strip() for p in str(value).split(",") if p.strip()]
    named = [RACE[p] for p in parts if p in RACE]
    if len(parts) > 1 or "More than one race, specify:" in parts:
        return "More than one race"
    if named:
        return named[0]
    return "Other"


def _collapse(value, mapping, other="Other") -> str:
    if pd.isna(value) or not str(value).strip():
        return "Not reported"
    return mapping.get(str(value).strip(), other)


# Question codes in the full Qualtrics export, mapped to the names used below.
SURVEY_COLUMNS = {
    "Q1": "intitals", "Q2": "age", "Q3": "handedness", "Q4": "sex",
    "Q5": "ethnicity", "Q6": "race", "Q7": "native language",
    "Q8": "years of education", "Q10": "highest degree", "Q11": "work status",
    "Q12": "work category", "Q13": "job title",
}

# Responses submitted on 13-14 June 2023 carry no worker ID: the survey was not
# recording it for the first two days of collection. Each of these six was
# matched to a participant by initials and age, against the name and date of
# birth on their consent form, giving a unique pairing in both directions, and
# corroborated by the gap between the two submissions -- 0.6 to 2.4 minutes,
# against a median of 1.3 minutes for the 344 participants whose worker ID was
# recorded. Kept as an explicit table so the evidence travels with the claim.
def _recovered(name: str) -> dict[str, str]:
    """Worker ID -> Qualtrics ResponseId for the orphaned June 13-14 responses.

    The pairs are worker IDs, which identify a person, so they live beside the
    survey export rather than in this repository. They are needed only when the
    demographics table is rebuilt from that export, which already requires
    COGARC_PRIVATE.
    """
    if paths.PRIVATE is None:
        return {}
    f = paths.PRIVATE / "recovered_response_ids.json"
    if not f.exists():
        raise FileNotFoundError(
            f"{f} holds the worker ID to ResponseId pairs for the responses "
            "the survey did not stamp on 13-14 June 2023. Without it those "
            "participants lose their demographics."
        )
    return json.loads(f.read_text())[name]


RECOVERED = _recovered("RECOVERED")
ENVIRONMENT_RECOVERED = _recovered("ENVIRONMENT_RECOVERED")


def load_survey() -> pd.DataFrame:
    """The screening survey, from the complete Qualtrics export.

    The July 2023 file used previously is a working subset: 84 eligible
    responses carrying a worker ID are absent from it, spread across every
    collection date. The first two rows of a Qualtrics export are the question
    text and the import IDs, not responses.
    """
    if paths.SCREENING_FULL is None or not paths.SCREENING_FULL.exists():
        raise FileNotFoundError(
            "The demographics survey carries Mechanical Turk worker IDs and "
            "participant initials and is not distributed with this repository. "
            f"The derived table is shipped at {paths.TABLES / 'demographics.csv'}. "
            "To regenerate it, set COGARC_PRIVATE to the directory holding the "
            "Qualtrics exports."
        )
    df = pd.read_csv(paths.SCREENING_FULL, dtype=str, low_memory=False)
    df = df.iloc[2:].reset_index(drop=True).rename(columns=SURVEY_COLUMNS)
    df["workerId"] = df["workerId"].astype(str).str.strip()
    return df


def load_person_demographics() -> pd.DataFrame:
    """One row per person in the analysis sample, with demographics attached.

    People without a linked survey response are retained with missing values so
    that coverage is visible in the output.
    """
    # Every participant with valid trials, so that the table describes
    # everyone who contributed data rather than the narrower set used for
    # averages. An age is one recorded value, equally precise however many
    # trials the participant completed.
    sample = trial_level_sample()

    if paths.ROSTER is not None:
        # The roster carries the adjudicated worker link for each person,
        # including the ones established by hand rather than by a typed
        # completion code, and a flag saying whether that link is firm enough
        # to inherit the person's survey record. A link resting on timing and
        # timezone alone identifies the session well enough to keep its task
        # data, but not well enough to attach someone's demographics to it.
        roster = pd.read_csv(paths.ROSTER, dtype=str)
        roster = roster[roster["demographics"].str.strip().str.lower() == "yes"]
        if "worker" not in roster.columns:
            # The shipped roster carries the flag but not the worker ID, which
            # identifies a person and stays out of the repository. Rebuilding
            # the table needs the private survey export and a roster that
            # still has the column; without it the shipped table stands.
            raise FileNotFoundError(
                f"{paths.ROSTER} carries no worker column, so survey records "
                "cannot be attached. The derived table is shipped at "
                f"{paths.TABLES / 'demographics.csv'}; to regenerate it, point "
                "COGARC_ROSTER at a roster holding the worker IDs and set "
                "COGARC_PRIVATE."
            )
        per_person = (
            roster[roster["worker"].notna() & (roster["worker"].str.strip() != "")]
            .drop_duplicates("person_id")[["person_id", "worker"]]
            .reset_index(drop=True)
        )
        # Keep every person in the analysis sample, so coverage stays visible.
        everyone = pd.DataFrame({"person_id": sorted(sample["person_id"].unique())})
        per_person = everyone.merge(per_person, on="person_id", how="left")
    else:
        link = subject_to_worker()
        people = (
            sample[["person_id", "subject"]]
            .drop_duplicates()
            .assign(worker=lambda d: d["subject"].map(link))
        )
        per_person = (
            people.groupby("person_id")["worker"]
            .apply(lambda s: next((w for w in s if pd.notna(w)), None))
            .rename("worker")
            .reset_index()
        )

    survey = load_survey()

    direct = survey[~survey["workerId"].isin(["nan", ""])].drop_duplicates(
        "workerId", keep="first")

    recovered = survey[survey["ResponseId"].isin(RECOVERED.values())].copy()
    recovered["workerId"] = recovered["ResponseId"].map(
        {v: k for k, v in RECOVERED.items()})

    survey = pd.concat([direct, recovered], ignore_index=True)
    survey = survey.drop_duplicates("workerId", keep="first")

    df = per_person.merge(survey, left_on="worker", right_on="workerId", how="left")

    df["age_num"] = pd.to_numeric(df["age"], errors="coerce")
    df["education_years"] = pd.to_numeric(df["years of education"], errors="coerce")
    df["gender"] = df["sex"].apply(lambda v: _collapse(v, {
        "Male": "Male", "Female": "Female", "Other": "Other"}))
    df["language"] = df["native language"].apply(lambda v: _collapse(v, {
        "English": "English"}, other="Other"))
    df["race_group"] = df["race"].apply(_collapse_race)
    df["degree"] = df["highest degree"].apply(lambda v: _collapse(v, DEGREE))
    df["employment"] = df["work status"].apply(lambda v: _collapse(v, WORK_STATUS))
    df["handedness_group"] = df["handedness"].apply(lambda v: _collapse(v, {
        "Right-handed": "Right-handed",
        "Left-handed": "Left-handed",
        "Ambidextrous": "Ambidextrous"}))
    df["has_survey"] = df["workerId"].notna()
    return df


def _categorical_block(df: pd.DataFrame, column: str, label: str) -> list[dict]:
    """Counts and percentages over the people who answered the item."""
    answered = df[df[column] != "Not reported"]
    n = len(answered)
    rows = []
    counts = answered[column].value_counts()
    for category, count in counts.items():
        rows.append(
            {
                "Measure": label,
                "Category": category,
                "n": int(count),
                "Percent": round(100 * count / n, 1) if n else None,
            }
        )
    missing = int((df[column] == "Not reported").sum())
    if missing:
        rows.append(
            {"Measure": label, "Category": "Not reported", "n": missing, "Percent": None}
        )
    return rows


def _continuous_block(df: pd.DataFrame, column: str, label: str) -> list[dict]:
    s = df[column].dropna()
    return [
        {
            "Measure": label,
            "Category": "",
            "n": int(len(s)),
            "Percent": None,
            "Mean": round(s.mean(), 2),
            "Median": round(s.median(), 1),
            "SD": round(s.std(), 2),
        }
    ]


# The per-person file lands in the repository, so it carries the analysis
# variables and nothing else. Named explicitly rather than by exclusion: the
# survey export also holds worker IDs, response metadata, IP addresses and
# coordinates, free-text initials, job titles, the uploaded consent file name,
# and written answers about head injury and attention disorders. An earlier
# version wrote the export through unchanged.
PUBLISHABLE = [
    "person_id", "has_survey", "age_num", "gender", "language", "race_group",
    "education_years", "degree", "employment", "handedness_group",
]


def _write_person_demographics(df: pd.DataFrame) -> None:
    """Write one row per person, holding only the publishable columns."""
    kept = df[[c for c in PUBLISHABLE if c in df.columns]]
    paths.DERIVED.mkdir(parents=True, exist_ok=True)
    kept.to_csv(paths.DERIVED / "person_demographics.csv", index=False)


def build_table() -> pd.DataFrame:
    df = load_person_demographics()
    answered = df[df["has_survey"]]

    rows: list[dict] = []
    rows += _continuous_block(answered, "age_num", "Age")
    rows += _categorical_block(answered, "gender", "Gender")
    rows += _categorical_block(answered, "language", "Native language")
    rows += _categorical_block(answered, "race_group", "Race")
    rows += _continuous_block(answered, "education_years", "Years of education")
    rows += _categorical_block(answered, "degree", "Highest degree")
    rows += _categorical_block(answered, "employment", "Job status")
    rows += _categorical_block(answered, "handedness_group", "Handedness")

    return pd.DataFrame(rows)[
        ["Measure", "Category", "n", "Percent", "Mean", "Median", "SD"]
    ]


# --- does any demographic variable predict performance? --------------------

CONTINUOUS = [("age_num", "Age"), ("education_years", "Years of education")]
CATEGORICAL = [
    ("gender", "Gender"),
    ("handedness_group", "Handedness"),
    ("race_group", "Race"),
    ("degree", "Highest degree"),
    ("employment", "Job status"),
]
MIN_CELL = 5      # categories smaller than this are not tested


def performance_by_demographics() -> pd.DataFrame:
    """Test each demographic variable against participant accuracy.

    Seven tests are run, so p-values are corrected with Benjamini-Hochberg.
    Two variables reach p < .05 uncorrected and neither survives:

    * highest degree, where the pattern is non-monotonic (high school above
      bachelor's above master's above associate) and the continuous
      years-of-education measure shows nothing, which is what an education
      effect would show first;
    * employment status, which rests on cells of five to seven people.

    Both read as small-cell noise rather than findings.
    """
    from scipy import stats

    from .correlates import _benjamini_hochberg
    from .descriptives import participant_summary

    people = participant_summary()
    df = load_person_demographics().set_index("person_id")
    df = df.join(people[["accuracy"]], how="inner")
    df = df[df["has_survey"]]

    rows = []
    for col, label in CONTINUOUS:
        sub = df[[col, "accuracy"]].dropna()
        r, p = stats.pearsonr(sub[col], sub["accuracy"])
        rho, _ = stats.spearmanr(sub[col], sub["accuracy"])
        rows.append({"measure": label, "test": "Pearson r", "n": len(sub),
                     "statistic": round(r, 3), "spearman": round(rho, 3),
                     "p_raw": p})

    for col, label in CATEGORICAL:
        groups, names = [], []
        for name, block in df.groupby(col):
            vals = block["accuracy"].dropna()
            if name != "Not reported" and len(vals) >= MIN_CELL:
                groups.append(vals.values)
                names.append(name)
        if len(groups) < 2:
            continue
        f, p = stats.f_oneway(*groups)
        rows.append({"measure": label, "test": f"ANOVA ({len(groups)} groups)",
                     "n": int(sum(len(g) for g in groups)),
                     "statistic": round(f, 3), "spearman": None, "p_raw": p})

    out = pd.DataFrame(rows)
    out["p_fdr"] = _benjamini_hochberg(out["p_raw"].values)
    out["significant"] = out["p_fdr"] < .05
    return out


def demographic_group_means() -> pd.DataFrame:
    """Mean accuracy within each demographic category, for reference."""
    from .descriptives import participant_summary

    df = load_person_demographics().set_index("person_id")
    df = df.join(participant_summary()[["accuracy"]], how="inner")
    df = df[df["has_survey"]]

    rows = []
    for col, label in CATEGORICAL:
        for name, block in df.groupby(col):
            vals = block["accuracy"].dropna()
            if not len(vals):
                continue
            # A mean over a handful of people can be matched against the
            # participant summary, which would attach the category to a
            # subject ID. Cells below MIN_CELL report their count only.
            shown = round(vals.mean(), 4) if len(vals) >= MIN_CELL else None
            rows.append({"measure": label, "category": name, "n": len(vals),
                         "mean_accuracy": shown,
                         "tested": name != "Not reported" and len(vals) >= MIN_CELL})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    try:
        df = load_person_demographics()
    except FileNotFoundError as exc:
        # The survey export and the worker IDs that join it to a session are
        # not distributed, so a clone cannot rebuild this table. The shipped
        # one stands; say so and stop rather than failing the run.
        print(f"skipped: {exc}")
        sys.exit(0)
    n_people = len(df)
    n_linked = int(df["worker"].notna().sum())
    n_survey = int(df["has_survey"].sum())

    print(f"people in the analysis sample:        {n_people}")
    print(f"  linked to a worker ID:              {n_linked}")
    print(f"  with a completed demographics form: {n_survey} "
          f"({n_survey / n_people:.1%})")
    print(f"  no demographics available:          {n_people - n_survey}\n")

    table = build_table()
    print(table.fillna("").to_string(index=False))

    print("\n=== does any demographic variable predict accuracy? ===")
    tests = performance_by_demographics()
    show = tests.copy()
    for c in ("p_raw", "p_fdr"):
        show[c] = show[c].map(lambda v: f"{v:.3f}")
    print(show[["measure", "test", "n", "statistic", "p_raw", "p_fdr",
                "significant"]].to_string(index=False))
    if not tests["significant"].any():
        print("\nnothing survives correction for the seven tests.")

    out = paths.TABLES / "demographics.csv"
    table.to_csv(out, index=False)
    tests.to_csv(paths.TABLES / "demographics_vs_accuracy.csv", index=False)
    demographic_group_means().to_csv(
        paths.TABLES / "demographics_group_means.csv", index=False)
    _write_person_demographics(df)
    print(f"\nwrote {out}")
    print(f"wrote {paths.DERIVED / 'person_demographics.csv'}")
