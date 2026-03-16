from __future__ import annotations

from pathlib import Path

import pandas as pd


COLUMN_MAP = {
    "Schizophrenia disorders (share of population) - Sex: Both - Age: Age-standardized": "schizophrenia",
    "Depressive disorders (share of population) - Sex: Both - Age: Age-standardized": "depressive",
    "Anxiety disorders (share of population) - Sex: Both - Age: Age-standardized": "anxiety",
    "Bipolar disorders (share of population) - Sex: Both - Age: Age-standardized": "bipolar",
    "Eating disorders (share of population) - Sex: Both - Age: Age-standardized": "eating",
}

DISORDER_COLUMNS = ["schizophrenia", "depressive", "anxiety", "bipolar", "eating"]


def load_and_clean_data(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    df = df.rename(columns=COLUMN_MAP)
    df["Entity"] = df["Entity"].astype(str).str.strip()
    df["Code"] = df["Code"].astype(str).str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")

    for col in DISORDER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.drop_duplicates()
    df = df.dropna(subset=["Entity", "Year"] + DISORDER_COLUMNS)
    df = df[df["Year"] >= 1900]
    df = df.sort_values(["Entity", "Year"]).reset_index(drop=True)
    df["total_burden"] = df[DISORDER_COLUMNS].sum(axis=1)

    return df


def save_cleaned_data(input_csv: str | Path, output_csv: str | Path) -> Path:
    cleaned = load_and_clean_data(input_csv)
    output_path = Path(output_csv)
    cleaned.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    source = Path("1- mental-illnesses-prevalence.csv")
    target = Path("cleaned_mental_illnesses_prevalence.csv")
    saved = save_cleaned_data(source, target)
    print(f"Saved cleaned dataset to: {saved.resolve()}")
