import sqlite3
import pandas as pd
import json

SET_NUMBER = 17

def clean_name(name):
    return (
        str(name)
        .replace(f"TFT{SET_NUMBER}_", "")
        .replace(f"Set{SET_NUMBER}_", "")
        .replace(f"TFT_Set{SET_NUMBER}_", "")
    )
    
# Load data from DB

def load_data(db_path = "data/database.db"):
    connection = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM matches", connection)
    connection.close()
    return df


# Parse JSON columns

def parse_json_columns(df):
    df["traits"] = df["traits"].apply(json.loads)
    df["units"] = df["units"].apply(json.loads)
    df["augments"] = df["augments"].apply(json.loads)
    return df


# Extract features

def extract_traits(df):
# Record how many units were active for each trait
    trait_records = []
    for _, row in df.iterrows():
        record = {
            "match_id": row["match_id"],
            "puuid": row["puuid"]
        }

        for t in row["traits"]:
            name = clean_name(t.get("name", ""))

            if not name:
                continue

            record[f"trait_{name}"] = t.get("num_units", 0)

        trait_records.append(record)

    return pd.DataFrame(trait_records).fillna(0)


def extract_units(df):
# Mark 1 for each champion on player board
    unit_records = []
    for _, row in df.iterrows():
        record = {
            "match_id": row["match_id"],
            "puuid": row["puuid"]
        }

        for u in row["units"]:
            name = clean_name(u.get("character_id", ""))

            if not name:
                continue

            record[f"unit_{name}"] = 1

        unit_records.append(record)

    return pd.DataFrame(unit_records).fillna(0)


def extract_augments(df):
# Mark 1 for each augment the player picked
    augment_records = []
    for _, row in df.iterrows():
        record = {"match_id": row["match_id"], "puuid": row["puuid"]}
        for aug in row["augments"]:
            record[f"aug_{aug}"] = 1
        augment_records.append(record)
    return pd.DataFrame(augment_records).fillna(0)


# Main

def main():
    print("Loading data...")
    df = load_data()
    print(f"Raw rows: {len(df)}")

    # Filter to latest patch
    latest_patch = df["patch"].value_counts().index[0]
    print(f"Latest patch: {latest_patch} | rows: {len(df[df['patch'] == latest_patch])}")
    df = df[df["patch"] == latest_patch]
    print(f"Filtered rows: {len(df)}")

    df = parse_json_columns(df)

    print("Extracting features...")
    traits_df   = extract_traits(df)
    units_df    = extract_units(df)
    augments_df = extract_augments(df)

    # Merge all features
    features = traits_df.merge(units_df,    on=["match_id", "puuid"]) \
                        .merge(augments_df, on=["match_id", "puuid"])

    # Add target column
    features = features.merge(
        df[["match_id", "puuid", "placement", "level"]],
        on=["match_id", "puuid"]
    )

    print(f"Feature columns: {len(features.columns)}")
    print(f"Total rows: {len(features)}")
    print(f"\nPlacement distribution:\n{features['placement'].value_counts().sort_index()}")

    # Save
    features.to_csv("data/features.csv", index=False)
    print("\nSaved to data/features.csv")

if __name__ == "__main__":
    main()