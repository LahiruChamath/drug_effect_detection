import os
import numpy as np
import joblib
from sklearn.model_selection import StratifiedKFold, cross_val_predict, GridSearchCV
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

from src.preprocessing import preprocess_sequence
from src.feature_extraction import extract_features


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "pose_sequences")
MODEL_PATH = os.path.join(BASE_DIR, "models")
CLASSES = ["none", "stimulant", "depressant", "cannabis"]


# ==========================================================
# LOAD DATASET
# ==========================================================

def load_dataset():
    X = []
    y = []

    for label in CLASSES:
        folder = os.path.join(DATA_PATH, label)

        if not os.path.exists(folder):
            print(f"Warning: {folder} not found, skipping...")
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
# PLOT CONFUSION MATRIX
# ==========================================================

def plot_confusion_matrix(y_true, y_pred, classes, save_path=None):
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes,
                yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix - SVM')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"✅ Saved: {save_path}")
    
    plt.show()


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    # Create models directory if not exists
    os.makedirs(MODEL_PATH, exist_ok=True)

    # ==================== LOAD DATA ====================
    print("=" * 60)
    print("LOADING DATASET")
    print("=" * 60)
    
    X, y = load_dataset()

    print(f"Dataset shape: {X.shape}")
    print(f"Labels: {np.unique(y, return_counts=True)}")
    print(f"Number of features: {X.shape[1]}")

    # ==================== HYPERPARAMETER TUNING ====================
    print("\n" + "=" * 60)
    print("HYPERPARAMETER TUNING (GridSearchCV)")
    print("=" * 60)

    # Define pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC())
    ])

    # Parameter grid
    param_grid = {
        'svm__C': [0.1, 1, 10, 100],
        'svm__gamma': ['scale', 'auto', 0.01, 0.1],
        'svm__kernel': ['rbf', 'poly']
    }

    # Grid search with cross-validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        pipeline, 
        param_grid, 
        cv=skf, 
        scoring='accuracy', 
        n_jobs=-1,
        verbose=1
    )

    print("Searching for best parameters...")
    grid_search.fit(X, y)

    print(f"\n✅ Best parameters: {grid_search.best_params_}")
    print(f"✅ Best CV accuracy: {grid_search.best_score_:.4f}")

    # ==================== FINAL MODEL ====================
    print("\n" + "=" * 60)
    print("TRAINING FINAL MODEL")
    print("=" * 60)

    # Use best parameters
    best_model = grid_search.best_estimator_

    # Cross-validation predictions
    y_pred = cross_val_predict(best_model, X, y, cv=skf)

    # ==================== EVALUATION ====================
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    
    print(classification_report(y, y_pred))

    print("Confusion Matrix:")
    print(confusion_matrix(y, y_pred))

    # Calculate accuracy
    accuracy = accuracy_score(y, y_pred)
    print(f"\n✅ Overall Accuracy: {accuracy:.2%}")

    # Plot confusion matrix
    plot_confusion_matrix(
        y, y_pred, CLASSES,
        save_path=os.path.join(MODEL_PATH, "confusion_matrix_svm.png")
    )

    # ==================== SAVE MODEL ====================
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)

    # Train on full dataset
    best_model.fit(X, y)

    # Save model
    model_file = os.path.join(MODEL_PATH, "drug_classifier_svm.pkl")
    joblib.dump(best_model, model_file)
    print(f"✅ Model saved: {model_file}")

    # Save label encoder
    le = LabelEncoder()
    le.fit(y)
    le_file = os.path.join(MODEL_PATH, "label_encoder.pkl")
    joblib.dump(le, le_file)
    print(f"✅ Label encoder saved: {le_file}")

    # Save classes
    classes_file = os.path.join(MODEL_PATH, "classes.npy")
    np.save(classes_file, CLASSES)
    print(f"✅ Classes saved: {classes_file}")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)