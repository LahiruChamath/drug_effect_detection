"""
Master Retraining Script — v3 (Accuracy Boost Edition)
Improvements vs v2:
  SVM  : +101 new features (per-joint velocity, acceleration, head sway)
  BiLSTM: window slicing (3× data), class weights, 60 frames, z-coord included

Run from the project root:
    python retrain_all.py
"""

import os, sys, json, shutil, time, warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import StratifiedKFold, cross_val_predict, GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder, label_binarize
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score,
    roc_curve, auc, roc_auc_score, log_loss
)
from xgboost import XGBClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.preprocessing import preprocess_sequence
from src.feature_extraction import extract_features

# ============================================================
# CONFIG
# ============================================================
DATA_PATH    = os.path.join(BASE_DIR, "data", "pose_sequences")
MODEL_PATH   = os.path.join(BASE_DIR, "models")
RESULTS_PATH = os.path.join(BASE_DIR, "results")
CLASSES      = ["none", "stimulant", "depressant", "cannabis"]
N_CLASSES    = len(CLASSES)
LSTM_FRAMES  = 60   # ← increased from 30 to capture more temporal context

os.makedirs(MODEL_PATH,   exist_ok=True)
os.makedirs(RESULTS_PATH, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================
def header(title):
    print(f"\n{'='*70}\n  {title}\n{'='*70}")


def load_feature_dataset():
    """Load preprocessed feature vectors for SVM / XGBoost."""
    X, y = [], []
    for label in CLASSES:
        folder = os.path.join(DATA_PATH, label)
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            if not fname.endswith(".json"):
                continue
            try:
                seq = preprocess_sequence(os.path.join(folder, fname))
                X.append(extract_features(seq))
                y.append(label)
            except Exception as e:
                print(f"  ⚠ Skipped {fname}: {e}")
    return np.array(X), np.array(y)


def load_sequence_dataset_windowed(target_frames=LSTM_FRAMES, stride=None):
    """
    Load pose sequences for BiLSTM with window slicing.

    Instead of one (target_frames,) window per file, we extract multiple
    overlapping windows across the full ~200-frame preprocessed sequence.
    This multiplies training data 3-4× without new recordings.

    stride: frames to advance per window (default = target_frames // 2 → 50% overlap)
    """
    if stride is None:
        stride = target_frames // 2   # 50% overlap → ~3× more samples

    X, y = [], []
    for label in CLASSES:
        folder = os.path.join(DATA_PATH, label)
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            if not fname.endswith(".json"):
                continue
            try:
                # preprocess returns (200, 33, 3) — use all 200 frames
                seq = preprocess_sequence(os.path.join(folder, fname),
                                          target_frames=200)
                # seq shape: (200, 33, 3)  →  flatten to (200, 99) — includes z
                seq_flat = seq.reshape(200, -1)

                # Slide a window across the sequence
                n_frames = seq_flat.shape[0]
                starts = range(0, n_frames - target_frames + 1, stride)
                for start in starts:
                    window = seq_flat[start : start + target_frames]
                    X.append(window)
                    y.append(label)

            except Exception as e:
                print(f"  ⚠ Skipped {fname}: {e}")

    return np.array(X, dtype=np.float32), np.array(y)


def save_confusion_matrix(y_true, y_pred, model_name, cmap, path):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap=cmap,
                xticklabels=CLASSES, yticklabels=CLASSES)
    plt.xlabel('Predicted'); plt.ylabel('Actual')
    plt.title(f'Confusion Matrix — {model_name}')
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()
    print(f"  ✅ Saved: {os.path.basename(path)}")


def save_roc_curves(y_true_enc, y_prob, model_name, path):
    y_bin = label_binarize(y_true_enc, classes=range(N_CLASSES))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    plt.figure(figsize=(10, 8))
    for i, (cls, col) in enumerate(zip(CLASSES, colors)):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_prob[:, i])
        plt.plot(fpr, tpr, color=col, lw=2, label=f'{cls} (AUC={auc(fpr, tpr):.3f})')
    plt.plot([0, 1], [0, 1], 'k--', lw=1)
    plt.xlabel('FPR'); plt.ylabel('TPR')
    plt.title(f'ROC Curves — {model_name}')
    plt.legend(loc='lower right'); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(path, dpi=150); plt.close()
    print(f"  ✅ Saved: {os.path.basename(path)}")


def compute_and_print_metrics(name, y_true, y_pred, y_prob):
    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average='macro', zero_division=0)
    rec  = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1   = f1_score(y_true, y_pred, average='macro', zero_division=0)
    ll   = log_loss(y_true, y_prob)
    y_bin = label_binarize(y_true, classes=range(N_CLASSES))
    rauc = roc_auc_score(y_bin, y_prob, average='macro')
    print(f"\n  {name} Results:")
    print(f"    Accuracy : {acc:.4f} ({acc*100:.2f}%)")
    print(f"    Precision: {prec:.4f}   Recall: {rec:.4f}   F1: {f1:.4f}")
    print(f"    Log Loss : {ll:.4f}    ROC AUC: {rauc:.4f}")
    print(f"\n{classification_report(y_true, y_pred, target_names=CLASSES, zero_division=0)}")
    return dict(accuracy=acc, precision_macro=prec, recall_macro=rec,
                f1_macro=f1, log_loss=ll, roc_auc_macro=rauc)


def save_report(name, m, path):
    with open(path, 'w') as f:
        f.write(f"{'='*70}\n  {name} — CLASSIFICATION REPORT\n{'='*70}\n\n")
        for k, v in m.items():
            if isinstance(v, float):
                f.write(f"  {k:<25}: {v:.4f}\n")
    print(f"  ✅ Saved: {os.path.basename(path)}")


# ============================================================
# STEP 1 — SVM  (richer features from updated feature_extraction.py)
# ============================================================
def train_svm(X, y, le):
    header("STEP 1 / 4 — Training SVM  (230 features)")
    y_enc = le.transform(y)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    param_grid = {
        'svm__C':     [1, 10, 100],
        'svm__gamma': ['scale', 0.001, 0.01],
        'svm__kernel': ['rbf']
    }
    pipe = Pipeline([("scaler", StandardScaler()), ("svm", SVC(probability=True))])
    gs = GridSearchCV(pipe, param_grid, cv=skf, scoring='accuracy', n_jobs=-1, verbose=1)
    gs.fit(X, y_enc)
    print(f"\n  Best params: {gs.best_params_}")
    print(f"  Best CV acc: {gs.best_score_:.4f}")

    best = gs.best_estimator_
    y_pred = cross_val_predict(best, X, y_enc, cv=skf)
    y_prob = cross_val_predict(best, X, y_enc, cv=skf, method='predict_proba')

    metrics = compute_and_print_metrics("SVM", y_enc, y_pred, y_prob)

    save_confusion_matrix(y_enc, y_pred, "SVM", "Blues",
                          os.path.join(RESULTS_PATH, "confusion_matrix_svm.png"))
    save_confusion_matrix(y_enc, y_pred, "SVM", "Blues",
                          os.path.join(MODEL_PATH, "confusion_matrix_svm.png"))
    save_roc_curves(y_enc, y_prob, "SVM",
                    os.path.join(RESULTS_PATH, "roc_curves_svm.png"))
    save_report("SVM", metrics,
                os.path.join(RESULTS_PATH, "classification_report_svm.txt"))

    best.fit(X, y_enc)
    joblib.dump(best, os.path.join(MODEL_PATH, "drug_classifier_svm.pkl"))
    print(f"  ✅ Model saved: drug_classifier_svm.pkl")
    return metrics


# ============================================================
# STEP 2 — XGBoost
# ============================================================
def train_xgboost(X, y, le):
    header("STEP 2 / 4 — Training XGBoost  (230 features)")
    y_enc = le.transform(y)
    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    model = XGBClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.1,
        subsample=0.8, random_state=42, eval_metric='mlogloss', n_jobs=-1
    )
    y_pred = cross_val_predict(model, X_sc, y_enc, cv=skf)
    y_prob = cross_val_predict(model, X_sc, y_enc, cv=skf, method='predict_proba')

    metrics = compute_and_print_metrics("XGBoost", y_enc, y_pred, y_prob)

    save_confusion_matrix(y_enc, y_pred, "XGBoost", "Greens",
                          os.path.join(RESULTS_PATH, "confusion_matrix_xgboost.png"))
    save_confusion_matrix(y_enc, y_pred, "XGBoost", "Greens",
                          os.path.join(MODEL_PATH, "confusion_matrix_xgboost.png"))
    save_roc_curves(y_enc, y_prob, "XGBoost",
                    os.path.join(RESULTS_PATH, "roc_curves_xgboost.png"))
    save_report("XGBoost", metrics,
                os.path.join(RESULTS_PATH, "classification_report_xgboost.txt"))

    model.fit(X_sc, y_enc)
    imp = model.feature_importances_
    idx = np.argsort(imp)[::-1][:20]
    plt.figure(figsize=(10, 5))
    plt.bar(range(20), imp[idx], color='steelblue')
    plt.xticks(range(20), [f'F{i}' for i in idx], rotation=45)
    plt.title('Top 20 Feature Importance — XGBoost')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_PATH, "feature_importance_xgboost.png"), dpi=150)
    plt.savefig(os.path.join(MODEL_PATH, "feature_importance_xgboost.png"), dpi=150)
    plt.close()

    joblib.dump(model,  os.path.join(MODEL_PATH, "drug_classifier_xgboost.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_PATH, "scaler.pkl"))
    print(f"  ✅ Model saved: drug_classifier_xgboost.pkl")
    return metrics


# ============================================================
# STEP 3 — BiLSTM  (window slicing + class weights + 60 frames)
# ============================================================
def train_bilstm(X_seq, y, le):
    header(f"STEP 3 / 4 — Training BiLSTM  ({LSTM_FRAMES} frames, windowed)")
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization
        from tensorflow.keras.utils import to_categorical
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    except ImportError:
        print("  ❌ TensorFlow not installed. Skipping BiLSTM.")
        return None

    # ── Fix random seed for reproducibility ────────────────────────────
    tf.random.set_seed(42)
    np.random.seed(42)

    y_enc = le.transform(y)

    # ── class weights to fix the cannabis 0/5 problem ──────────────────
    from sklearn.utils.class_weight import compute_class_weight
    cw = compute_class_weight('balanced', classes=np.unique(y_enc), y=y_enc)
    class_weight_dict = {i: w for i, w in enumerate(cw)}
    print(f"\n  Class weights: {class_weight_dict}")

    y_cat = to_categorical(y_enc, num_classes=N_CLASSES)

    # ── Clip-level train/test split (prevent data leakage) ─────────────
    # y has one label PER WINDOW (500 total from 100 clips × 5 windows).
    # We must split on the 100 ORIGINAL CLIPS so that windows from the
    # same clip never appear in both train and test.
    #
    # Since load_sequence_dataset_windowed iterates clips in order and
    # appends ~5 windows per clip, we can recover clip indices:
    windows_per_clip = len(y) // 100   # e.g. 5 for 60-frame, 50%-overlap
    clip_labels = y[::windows_per_clip]  # one label per clip (100 values)
    clip_indices = np.arange(100)

    train_clips, test_clips = train_test_split(
        clip_indices, test_size=0.2,
        stratify=clip_labels, random_state=42
    )

    # Expand clip indices back to window indices
    def clip_to_window_idx(clips, wpc):
        return np.concatenate([np.arange(c * wpc, (c + 1) * wpc) for c in clips])

    train_idx = clip_to_window_idx(train_clips, windows_per_clip)
    test_idx  = clip_to_window_idx(test_clips,  windows_per_clip)

    X_train, X_test = X_seq[train_idx], X_seq[test_idx]
    y_train, y_test = y_cat[train_idx], y_cat[test_idx]
    y_ts_enc        = y_enc[test_idx]

    print(f"  Clips  : {len(train_clips)} train / {len(test_clips)} test")
    print(f"  Windows: {len(X_train)} train / {len(X_test)} test (no leakage)")
    print(f"  Input shape  : {X_seq.shape[1:]}  (frames × features)")

    model = Sequential([
        Bidirectional(LSTM(128, return_sequences=True),
                      input_shape=(X_seq.shape[1], X_seq.shape[2])),
        Dropout(0.3),
        Bidirectional(LSTM(64, return_sequences=True)),
        Dropout(0.3),
        Bidirectional(LSTM(32, return_sequences=False)),
        Dropout(0.3),
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.4),
        Dense(N_CLASSES, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.summary()

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=25,
                      restore_best_weights=True, verbose=1),
        ModelCheckpoint(os.path.join(MODEL_PATH, 'best_lstm_model.keras'),
                        monitor='val_accuracy', save_best_only=True, verbose=0),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                          patience=10, min_lr=1e-7, verbose=1)
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=150,
        batch_size=8,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )

    y_prob = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_prob, axis=1)
    y_true = np.argmax(y_test, axis=1)

    metrics = compute_and_print_metrics("BiLSTM", y_true, y_pred, y_prob)

    save_confusion_matrix(y_true, y_pred, "BiLSTM", "Purples",
                          os.path.join(RESULTS_PATH, "confusion_matrix_lstm.png"))
    save_confusion_matrix(y_true, y_pred, "BiLSTM", "Purples",
                          os.path.join(MODEL_PATH, "confusion_matrix_lstm.png"))
    save_roc_curves(y_true, y_prob, "BiLSTM",
                    os.path.join(RESULTS_PATH, "roc_curves_lstm.png"))
    save_report("BiLSTM", metrics,
                os.path.join(RESULTS_PATH, "classification_report_lstm.txt"))

    # Training history
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    ax1.plot(history.history['loss'],     label='Train', lw=2)
    ax1.plot(history.history['val_loss'], label='Val',   lw=2)
    ax1.set_title('BiLSTM Loss'); ax1.set_xlabel('Epoch')
    ax1.legend(); ax1.grid(alpha=0.3)
    ax2.plot(history.history['accuracy'],     label='Train', lw=2)
    ax2.plot(history.history['val_accuracy'], label='Val',   lw=2)
    ax2.set_title('BiLSTM Accuracy'); ax2.set_xlabel('Epoch')
    ax2.legend(); ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_PATH, "lstm_training_history.png"), dpi=150)
    plt.savefig(os.path.join(MODEL_PATH, "lstm_training_history.png"), dpi=150)
    plt.close()
    print(f"  ✅ Saved: lstm_training_history.png")

    model.save(os.path.join(MODEL_PATH, "drug_classifier_lstm.h5"))
    print(f"  ✅ Model saved: drug_classifier_lstm.h5")
    return metrics


# ============================================================
# STEP 4 — COMPARISON SUMMARY
# ============================================================
def save_comparison(svm_m, xgb_m, lstm_m):
    header("STEP 4 / 4 — Model Comparison Summary")
    rows = [
        ("Accuracy",        'accuracy'),
        ("Precision macro", 'precision_macro'),
        ("Recall macro",    'recall_macro'),
        ("F1 macro",        'f1_macro'),
        ("Log Loss",        'log_loss'),
        ("ROC AUC macro",   'roc_auc_macro'),
    ]
    lstm_d = lstm_m if lstm_m else {}
    print(f"\n  {'Metric':<22} {'SVM':>10} {'XGBoost':>10} {'BiLSTM':>10}")
    print(f"  {'-'*55}")
    lines = []
    for label, key in rows:
        sv = svm_m.get(key, float('nan'))
        xb = xgb_m.get(key, float('nan'))
        lm = lstm_d.get(key, float('nan'))
        row = f"  {label:<22} {sv:>10.4f} {xb:>10.4f} {lm:>10.4f}"
        print(row); lines.append(row)

    path = os.path.join(RESULTS_PATH, "model_comparison_summary.txt")
    with open(path, 'w') as f:
        f.write("MODEL COMPARISON SUMMARY\n" + "="*55 + "\n")
        f.write(f"  {'Metric':<22} {'SVM':>10} {'XGBoost':>10} {'BiLSTM':>10}\n")
        f.write("  " + "-"*53 + "\n")
        for l in lines:
            f.write(l + "\n")
    print(f"\n  ✅ Saved: model_comparison_summary.txt")


# ============================================================
# SYNC PNGs FROM results/ → models/
# ============================================================
def sync_pngs():
    header("SYNCING PNGs  results/ → models/")
    for f in os.listdir(RESULTS_PATH):
        if f.endswith(".png"):
            shutil.copy2(os.path.join(RESULTS_PATH, f),
                         os.path.join(MODEL_PATH, f))
            print(f"  Copied: {f}")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    t0 = time.time()
    header("DRUG EFFECT DETECTION — RETRAINING (v3 — Accuracy Boost)")

    # ── Load data ───────────────────────────────────────────
    print("\n📂 Loading feature dataset (for SVM/XGBoost)...")
    X, y = load_feature_dataset()
    print(f"  Features shape: {X.shape}  (was 129, now {X.shape[1]})")

    print(f"\n📂 Loading windowed sequence dataset (for BiLSTM, {LSTM_FRAMES} frames, 50% overlap)...")
    X_seq, y_seq = load_sequence_dataset_windowed(target_frames=LSTM_FRAMES)
    print(f"  Sequences shape: {X_seq.shape}  (windowed — {X_seq.shape[0]} samples from 100 clips)")

    le = LabelEncoder()
    le.fit(CLASSES)
    joblib.dump(le, os.path.join(MODEL_PATH, "label_encoder.pkl"))
    np.save(os.path.join(MODEL_PATH, "classes.npy"), CLASSES)

    # ── Run all steps ────────────────────────────────────────
    svm_m  = train_svm(X, y, le)
    xgb_m  = train_xgboost(X, y, le)
    lstm_m = train_bilstm(X_seq, y_seq, le)
    save_comparison(svm_m, xgb_m, lstm_m)
    sync_pngs()

    total = time.time() - t0
    header(f"ALL DONE  ({total/60:.1f} min)")
    print(f"\n  Updated files in results/:")
    for f in sorted(os.listdir(RESULTS_PATH)):
        if not f.endswith(('.html',)):  # skip large html files
            sz = os.path.getsize(os.path.join(RESULTS_PATH, f))
            print(f"    {f:<50} {sz//1024:>5} KB")
    print()
