import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
import pickle
import sqlite3
from datetime import datetime

# Load features

def load_features(path="data/features.csv"):
    df = pd.read_csv(path)
    return df


# Train Model

def train(df):
    x = df.drop(columns=["match_id", "puuid", "placement"])
    y = df["placement"].apply(lambda x: 1 if x <= 4 else 0)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size = 0.2, random_state = 42
    )

    model = RandomForestClassifier(
        n_estimators = 200,
        max_depth = 10,
        min_samples_leaf = 3,
        random_state = 42
    )
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.2%}")
    print(f"\nConfusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
    
    importances = pd.Series(model.feature_importances_, index=x.columns)
    print(f"\nTop 10 features:\n{importances.nlargest(10)}")

    return model, x_test.columns.tolist(), acc


# Save model

def save_model(model, feature_cols, path="ml/model.pkl"):
    with open(path, "wb") as f:
        pickle.dump({"model": model, "feature_cols": feature_cols}, f)
    print(f"\nModel saved to {path}")

    
# Log experiment to SQLite

def log_experiment(acc, n_rows, n_features, db_path="data/database.db"):
    connection = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            run_at      TEXT,
            accuracy    REAL,
            n_rows      INTEGER,
            n_features  INTEGER
        )
    """)
    connection.execute("""
        INSERT INTO experiments (run_at, accuracy, n_rows, n_features)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().isoformat(), acc, n_rows, n_features))
    connection.commit()
    connection.close()
    print("Experiment logged to DB")


# Main
def main():
    print("Loading features...")
    df = load_features()
    print(f"Rows: {len(df)} | Features: {len(df.columns)}")

    print("\nTraining model...")
    model, feature_cols, acc = train(df)

    save_model(model, feature_cols)
    log_experiment(acc, len(df), len(feature_cols))


if __name__ == "__main__":
    main()