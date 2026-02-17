import os
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix

from src.preprocessing import preprocess_sequence
from src.feature_extraction import extract_features


# ==========================================================
# LOAD DATASET
# ==========================================================

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "pose_sequences")
CLASSES = ["none", "stimulant", "depressant", "cannabis"]


def load_dataset():
    X = []
    y = []

    for label in CLASSES:
        folder = os.path.join(DATA_PATH, label)

        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                filepath = os.path.join(folder, filename)

                try:
                    sequence = preprocess_sequence(filepath)
                    features = extract_features(sequence)

                    X.append(features)
                    y.append(label)

                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    return np.array(X), np.array(y)


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("Loading dataset...")
    X, y = load_dataset()

    print("Dataset shape:", X.shape)
    print("Labels:", np.unique(y, return_counts=True))

    # Build pipeline (Scaler + SVM)
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(kernel="rbf", C=1, gamma="scale"))
    ])

    # 5-fold cross-validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    print("\nRunning cross-validation...")
    y_pred = cross_val_predict(model, X, y, cv=skf)

    print("\nClassification Report:")
    print(classification_report(y, y_pred))

    print("Confusion Matrix:")
    print(confusion_matrix(y, y_pred))