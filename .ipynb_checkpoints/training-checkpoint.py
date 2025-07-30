import os
import sys
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import lightgbm as lgb

def main():
    CSV_PATH = "data.csv"
    MODEL_PATH = "model_lightgbm.txt"
    LABEL_MAP_PATH = "class_labels.json"

    # Check if dataset exists
    if not os.path.isfile(CSV_PATH):
        print(f"Error: CSV file '{CSV_PATH}' not found.")
        sys.exit(1)

    print("Loading dataset...")
    try:
        data = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)

    # Drop any timestamp columns
    data = data.loc[:, ~data.columns.str.contains("timestamp", case=False)]

    # Shuffle dataset
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)

    # Prepare features and labels
    if "label" not in data.columns:
        print("Error: 'label' column not found in dataset.")
        sys.exit(1)

    X = data.drop(columns=["label"])
    y_raw = data["label"]

    # Factorize labels
    print("Encoding labels...")
    y, label_mapping = pd.factorize(y_raw)

    # Save index->label mapping
    label_dict = {int(idx): label for idx, label in enumerate(label_mapping)}
    with open(LABEL_MAP_PATH, 'w') as f:
        json.dump(label_dict, f, indent=4)
        
    print(label_dict)
    print(f"Saved class mapping to '{LABEL_MAP_PATH}'. \n")

    # Split
    print("Splitting data into train/test... \n")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Create LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data  = lgb.Dataset(X_test, label=y_test, reference=train_data)

    # Parameters
    params = {
        "objective": "multiclass",
        "num_class": len(label_mapping),
        "boosting_type": "gbdt",
        "metric": "multi_logloss",
        "learning_rate": 0.05,
        "num_leaves": 15,
        "max_depth": 5,
        "verbosity": -1,
        "min_data_in_leaf": 20,
        "seed": 42
    }

    print("Starting training...")
    # Train with verbose evaluation
    try:
        model = lgb.train(
            params,
            train_data,
            valid_sets=[train_data, test_data],
            valid_names=["train", "test"],
            num_boost_round=1200,
            early_stopping_rounds=50,
            verbose_eval=100
        )
    except Exception as e:
        print(f"Error during training: {e}")
        sys.exit(1)

    print("Training complete.\n")

    # Save model
    model.save_model(MODEL_PATH)
    print(f"Model saved to '{MODEL_PATH}'. \n")

    # Predictions and evaluation
    print("Evaluating on test set...")
    y_pred_probs = model.predict(X_test)
    y_pred = [int(pred.argmax()) for pred in y_pred_probs]
    acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {acc:.4f}")

if __name__ == "__main__":
    main()
