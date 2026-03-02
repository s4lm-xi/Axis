import glob
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

FEATURE_COLS = ["f1","f2","f3","f4","f5","ax","ay","az","gx","gy","gz"]

SAMPLE_HZ = 50
WIN_S = 1.0
STEP_S = 0.2
WIN = int(WIN_S * SAMPLE_HZ)
STEP = int(STEP_S * SAMPLE_HZ)

def feats_from_window(Xw):
  # mean/std/min/max per channel => 11 * 4 = 44 features
  mean = Xw.mean(axis=0)
  std  = Xw.std(axis=0)
  mn   = Xw.min(axis=0)
  mx   = Xw.max(axis=0)
  return np.concatenate([mean, std, mn, mx], axis=0)

def build_dataset(paths):
  X_list, y_list = [], []
  for p in paths:
    df = pd.read_csv(p).dropna()
    if len(df) < WIN:
      continue
    X = df[FEATURE_COLS].to_numpy(np.float32)
    y = int(df["label"].iloc[0])

    for start in range(0, len(df) - WIN + 1, STEP):
      Xw = X[start:start+WIN]
      X_list.append(feats_from_window(Xw))
      y_list.append(y)

  return np.vstack(X_list), np.array(y_list)

if __name__ == "__main__":
  paths = glob.glob("dataset_runs/*.csv")
  X, y = build_dataset(paths)
  print("Dataset:", X.shape, "classes:", sorted(set(y)))

  Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

  model = XGBClassifier(
    n_estimators=80,
    max_depth=4,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.9,
    objective="multi:softmax",
    eval_metric="mlogloss"
  )
  model.fit(Xtr, ytr)

  pred = model.predict(Xte)
  print("Accuracy:", accuracy_score(yte, pred))

  model.save_model("xgb_model.json")
  print("Saved: xgb_model.json")