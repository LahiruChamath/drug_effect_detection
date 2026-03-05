import os
import numpy as np
import joblib
from sklearn.model_selection import StratifiedKFold, cross_val_predict, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

from src.preprocessing import preprocess_sequence
from src.feature_extraction import extract_features

# Suppress XGBoost warnings
warnings.filterwarnings('ignore', message='.*use_label_encoder.*')


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
            print(f"⚠️ Warning: {folder} not found, skipping...")
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
                    print(f"❌ Error processing {filename}: {e}")

    return np.array(X), np.array(y)


# ==========================================================
# PLOT CONFUSION MATRIX
# ==========================================================

def plot_confusion_matrix(y_true, y_pred, classes, save_path=None):
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens',
                xticklabels=classes,
                yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix - XGBoost')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"✅ Saved: {save_path}")
    
    plt.close()  # Close to free memory


# ==========================================================
# PLOT FEATURE IMPORTANCE
# ==========================================================

def plot_feature_importance(model, top_n=20, save_path=None):
    """Plot top N most important features"""
    importance = model.feature_importances_
    indices = np.argsort(importance)[::-1][:top_n]
    
    plt.figure(figsize=(10, 6))
    plt.title(f'Top {top_n} Feature Importance')
    plt.bar(range(top_n), importance[indices], color='steelblue')
    plt.xticks(range(top_n), [f'F{i}' for i in indices], rotation=45)
    plt.xlabel('Feature Index')
    plt.ylabel('Importance Score')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"✅ Saved: {save_path}")
    
    plt.close()


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

    # Encode labels (XGBoost requires numeric labels)
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    print(f"Encoded classes: {le.classes_}")

    # ==================== SCALE FEATURES ====================
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ==================== HYPERPARAMETER TUNING ====================
    print("\n" + "=" * 60)
    print("HYPERPARAMETER TUNING (GridSearchCV)")
    print("=" * 60)

    # Parameter grid
    param_grid = {
        'n_estimators': [100, 200, 300],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1, 0.2],
        'subsample': [0.8, 1.0]
    }

    # Base model - REMOVED use_label_encoder parameter
    xgb = XGBClassifier(
        random_state=42,
        eval_metric='mlogloss',
        n_jobs=-1  # Use all CPU cores
    )

    # Grid search
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        xgb, 
        param_grid, 
        cv=skf, 
        scoring='accuracy', 
        n_jobs=-1,
        verbose=1
    )

    print("Searching for best parameters...")
    grid_search.fit(X_scaled, y_encoded)

    print(f"\n✅ Best parameters: {grid_search.best_params_}")
    print(f"✅ Best CV accuracy: {grid_search.best_score_:.4f}")

    # ==================== FINAL MODEL ====================
    print("\n" + "=" * 60)
    print("EVALUATING BEST MODEL")
    print("=" * 60)

    best_model = grid_search.best_estimator_

    # Cross-validation predictions
    y_pred = cross_val_predict(best_model, X_scaled, y_encoded, cv=skf)

    # ==================== EVALUATION ====================
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    
    print(classification_report(y_encoded, y_pred, target_names=le.classes_))

    print("Confusion Matrix:")
    print(confusion_matrix(y_encoded, y_pred))

    # Calculate accuracy
    accuracy = accuracy_score(y_encoded, y_pred)
    print(f"\n✅ Overall Accuracy: {accuracy:.2%}")

    # Plot confusion matrix
    plot_confusion_matrix(
        y_encoded, y_pred, CLASSES,
        save_path=os.path.join(MODEL_PATH, "confusion_matrix_xgboost.png")
    )

    # ==================== FEATURE IMPORTANCE ====================
    print("\n" + "=" * 60)
    print("TOP 10 IMPORTANT FEATURES")
    print("=" * 60)

    # Train on full data
    best_model.fit(X_scaled, y_encoded)

    # Get feature importance
    importance = best_model.feature_importances_
    indices = np.argsort(importance)[::-1][:10]

    print("Feature ranking:")
    for i, idx in enumerate(indices):
        print(f"  {i+1}. Feature {idx}: {importance[idx]:.4f}")

    # Plot feature importance
    plot_feature_importance(
        best_model, 
        top_n=20,
        save_path=os.path.join(MODEL_PATH, "feature_importance_xgboost.png")
    )

    # ==================== SAVE MODEL ====================
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)

    # Save model
    model_file = os.path.join(MODEL_PATH, "drug_classifier_xgboost.pkl")
    joblib.dump(best_model, model_file)
    print(f"✅ Model saved: {model_file}")

    # Save scaler
    scaler_file = os.path.join(MODEL_PATH, "scaler.pkl")
    joblib.dump(scaler, scaler_file)
    print(f"✅ Scaler saved: {scaler_file}")

    # Save label encoder
    le_file = os.path.join(MODEL_PATH, "label_encoder.pkl")
    joblib.dump(le, le_file)
    print(f"✅ Label encoder saved: {le_file}")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)