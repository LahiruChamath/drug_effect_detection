"""
SHAP & LIME Explainability for SVM Classification
===================================================
Generates:
  1. SHAP summary (beeswarm) plot           – global feature importance
  2. SHAP mean |SHAP| bar plot              – per-class contribution
  3. LIME explanation for one sample/class   – local interpretability
  4. Combined feature importance comparison  – SHAP vs LIME side by side
"""

import os
import sys
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")            # headless backend for saving figures
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

# ── Path setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from src.preprocessing import preprocess_sequence
from src.feature_extraction import extract_features

DATA_PATH   = os.path.join(BASE_DIR, "data", "pose_sequences")
MODEL_PATH  = os.path.join(BASE_DIR, "models")
RESULTS_PATH = os.path.join(BASE_DIR, "results")
CLASSES = ["none", "stimulant", "depressant", "cannabis"]

os.makedirs(RESULTS_PATH, exist_ok=True)


# ==========================================================
# FEATURE NAMES  (must match extract_features() output order)
# ==========================================================

JOINT_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]


def build_feature_names():
    """Return human-readable names matching extract_features() output.

    Must follow the EXACT order in extract_features():
      1. Raw position stats          (5)
      2. Velocity stats              (5)
      3. Velocity joint energy       (99)   = 33 joints × 3 dims
      4. Per-joint velocity stats    (66)   = 33 mean + 33 std   ← NEW v2
      5. Acceleration stats          (5)
      6. Per-joint accel magnitude   (33)                        ← NEW v2
      7. Jerk stats                  (5)
      8. Postural sway               (2)
      9. Head sway                   (2)                         ← NEW v2
     10. Wrist tremor                (2)
     11. Symmetry                    (5)
     12. Motion entropy              (1)
                                   ─────
                              Total: 230
    """
    names = []

    # 1. Raw position stats (5)
    for s in ["mean", "std", "max", "min", "median"]:
        names.append(f"pos_{s}")

    # 2. Velocity stats (5)
    for s in ["mean", "std", "max", "min", "median"]:
        names.append(f"vel_{s}")

    # 3. Velocity joint energy (33 joints × 3 dims = 99)
    for j in JOINT_NAMES:
        for d in ["x", "y", "z"]:
            names.append(f"vel_energy_{j}_{d}")

    # 4. Per-joint velocity mean & std (33 + 33 = 66)  ← NEW v2
    for j in JOINT_NAMES:
        names.append(f"vel_mean_speed_{j}")
    for j in JOINT_NAMES:
        names.append(f"vel_std_speed_{j}")

    # 5. Acceleration stats (5)
    for s in ["mean", "std", "max", "min", "median"]:
        names.append(f"acc_{s}")

    # 6. Per-joint acceleration magnitude (33)  ← NEW v2
    for j in JOINT_NAMES:
        names.append(f"acc_mag_{j}")

    # 7. Jerk stats (5)
    for s in ["mean", "std", "max", "min", "median"]:
        names.append(f"jerk_{s}")

    # 8. Postural sway (2)
    names += ["sway_x", "sway_y"]

    # 9. Head sway (2)  ← NEW v2
    names += ["head_sway_x", "head_sway_y"]

    # 10. Wrist tremor (2)
    names += ["tremor_left_wrist", "tremor_right_wrist"]

    # 11. Symmetry (5 pairs)
    sym_pairs = ["shoulder", "elbow", "wrist", "knee", "ankle"]
    for p in sym_pairs:
        names.append(f"symmetry_{p}")

    # 12. Motion entropy (1)
    names.append("motion_entropy")

    return names


# ==========================================================
# LOAD DATASET
# ==========================================================

def load_dataset():
    X, y = [], []
    for label in CLASSES:
        folder = os.path.join(DATA_PATH, label)
        if not os.path.exists(folder):
            print(f"⚠️  {folder} not found, skipping...")
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.endswith(".json"):
                try:
                    seq = preprocess_sequence(os.path.join(folder, fname))
                    X.append(extract_features(seq))
                    y.append(label)
                except Exception as e:
                    print(f"Error processing {fname}: {e}")
    return np.array(X), np.array(y)


# ==========================================================
# SHAP ANALYSIS
# ==========================================================

def run_shap_analysis(model, X, feature_names):
    """
    Use KernelExplainer (model-agnostic) because SVM with RBF kernel
    is not natively supported by TreeExplainer.
    """
    import shap

    print("\n" + "=" * 60)
    print("  SHAP ANALYSIS")
    print("=" * 60)

    # Use a background sample (k-means summary) for speed
    bg_size = min(50, len(X))
    background = shap.kmeans(X, bg_size)

    print(f"  Background samples : {bg_size}")
    print(f"  Explaining samples : {len(X)}")
    print("  Computing SHAP values (this may take a few minutes)...")

    explainer = shap.KernelExplainer(model.predict_proba, background)
    raw_shap = explainer.shap_values(X)

    # ── Normalise shape: newer SHAP versions return (n_samples, n_features, n_classes)
    #    while older versions return a list of (n_samples, n_features) per class.
    raw_shap = np.array(raw_shap)
    if raw_shap.ndim == 3 and raw_shap.shape[-1] == len(CLASSES):
        # Shape is (n_samples, n_features, n_classes) — split into per-class list
        shap_values = [raw_shap[:, :, c] for c in range(len(CLASSES))]
    elif raw_shap.ndim == 3 and raw_shap.shape[0] == len(CLASSES):
        # Shape is (n_classes, n_samples, n_features) — already a list-like
        shap_values = [raw_shap[c] for c in range(len(CLASSES))]
    else:
        # Legacy format: list of arrays
        shap_values = list(raw_shap)

    print(f"  SHAP values: {len(shap_values)} classes, each shape {shap_values[0].shape}")

    # ── 1. Summary beeswarm plot (one per class) ──────────
    print("\n📊 Generating SHAP summary plots...")
    per_class_imgs = []
    for idx, cls in enumerate(CLASSES):
        plt.figure(figsize=(10, 7))
        shap.summary_plot(
            shap_values[idx], X,
            feature_names=feature_names,
            max_display=15,
            show=False,
        )
        plt.title(f"SHAP Summary – {cls}", fontsize=13, fontweight="bold")
        plt.tight_layout()
        cls_path = os.path.join(RESULTS_PATH, f"shap_summary_{cls}_svm.png")
        plt.savefig(cls_path, dpi=150, bbox_inches="tight")
        per_class_imgs.append(cls_path)
        plt.close()
        print(f"  ✅ Saved: {cls_path}")

    # Combine individual plots into one composite image
    from PIL import Image
    imgs = [Image.open(p) for p in per_class_imgs]
    w, h = imgs[0].size
    composite = Image.new("RGB", (w * 2, h * 2), (255, 255, 255))
    for i, img in enumerate(imgs):
        composite.paste(img, ((i % 2) * w, (i // 2) * h))
    path_summary = os.path.join(RESULTS_PATH, "shap_summary_svm.png")
    composite.save(path_summary, dpi=(150, 150))
    print(f"  ✅ Saved composite: {path_summary}")

    # ── 2. Mean |SHAP| bar plot (global importance) ───────
    print("📊 Generating SHAP bar plot...")
    plt.figure(figsize=(14, 8))
    shap.summary_plot(
        shap_values, X,
        feature_names=feature_names,
        plot_type="bar",
        class_names=CLASSES,
        max_display=20,
        show=False,
    )
    plt.title("Mean |SHAP| – Feature Importance by Class (SVM)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path_bar = os.path.join(RESULTS_PATH, "shap_bar_svm.png")
    plt.savefig(path_bar, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Saved: {path_bar}")

    # ── 3. Overall global importance (average across classes) ─
    mean_abs_shap = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
    top_k = 20
    top_idx = np.argsort(mean_abs_shap)[-top_k:][::-1]

    plt.figure(figsize=(12, 7))
    colors = sns.color_palette("viridis", top_k)
    bars = plt.barh(
        range(top_k),
        mean_abs_shap[top_idx][::-1],
        color=colors,
    )
    plt.yticks(range(top_k), [feature_names[i] for i in top_idx][::-1], fontsize=10)
    plt.xlabel("Mean |SHAP value|", fontsize=12)
    plt.title("Top 20 Features – Global SHAP Importance (SVM)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path_global = os.path.join(RESULTS_PATH, "shap_global_importance_svm.png")
    plt.savefig(path_global, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Saved: {path_global}")

    return shap_values, mean_abs_shap


# ==========================================================
# LIME ANALYSIS
# ==========================================================

def run_lime_analysis(model, X, y, feature_names):
    """
    Generate LIME explanations for representative samples.
    """
    import lime
    import lime.lime_tabular

    print("\n" + "=" * 60)
    print("  LIME ANALYSIS")
    print("=" * 60)

    explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data=X,
        feature_names=feature_names,
        class_names=CLASSES,
        mode="classification",
        discretize_continuous=True,
        random_state=42,
    )

    # ── 1. Per-class LIME explanations ────────────────────
    lime_importances_all = np.zeros(len(feature_names))
    n_explanations = 0

    fig, axes = plt.subplots(2, 2, figsize=(22, 16))
    fig.suptitle("LIME Explanations – One Sample per Class (SVM)",
                 fontsize=16, fontweight="bold", y=1.01)

    for cls_idx, cls_name in enumerate(CLASSES):
        # Pick a representative sample of this class
        class_mask = (y == cls_name)
        class_indices = np.where(class_mask)[0]

        if len(class_indices) == 0:
            print(f"  ⚠️  No samples for class '{cls_name}', skipping LIME")
            continue

        sample_idx = class_indices[len(class_indices) // 2]   # middle sample
        exp = explainer.explain_instance(
            X[sample_idx],
            model.predict_proba,
            num_features=15,
            top_labels=len(CLASSES),
        )

        # Accumulate importances
        for feat_name, weight in exp.as_list(label=cls_idx):
            # LIME bins features; try to match back to original name
            for fi, fn in enumerate(feature_names):
                if fn in feat_name:
                    lime_importances_all[fi] += abs(weight)
                    break
            n_explanations += 1

        # Plot on sub-axis
        ax = axes[cls_idx // 2][cls_idx % 2]
        feat_weights = exp.as_list(label=cls_idx)
        feat_labels = [fw[0][:30] for fw in feat_weights]   # truncate long names
        weights = [fw[1] for fw in feat_weights]

        colors_bar = ["#2ecc71" if w > 0 else "#e74c3c" for w in weights]
        ax.barh(range(len(weights)), weights, color=colors_bar, edgecolor="white", linewidth=0.5)
        ax.set_yticks(range(len(weights)))
        ax.set_yticklabels(feat_labels, fontsize=8)
        ax.set_xlabel("Feature weight", fontsize=10)
        ax.set_title(f"True class: {cls_name} (sample #{sample_idx})",
                      fontsize=12, fontweight="bold")
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.3)

        # Save individual HTML explanation
        html_path = os.path.join(RESULTS_PATH, f"lime_explanation_{cls_name}.html")
        exp.save_to_file(html_path)
        print(f"  ✅ Saved LIME HTML: {html_path}")

    plt.tight_layout()
    path_lime = os.path.join(RESULTS_PATH, "lime_explanations_svm.png")
    plt.savefig(path_lime, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Saved: {path_lime}")

    # Normalize accumulated importance
    if n_explanations > 0:
        lime_importances_all /= n_explanations

    # ── 2. LIME Stability Analysis ────────────────────────
    print("\n📊 Running LIME stability analysis (multiple samples per class)...")
    n_per_class = 5
    class_lime_importances = {cls: np.zeros(len(feature_names)) for cls in CLASSES}

    for cls_name in CLASSES:
        class_mask = (y == cls_name)
        class_indices = np.where(class_mask)[0]
        sample_count = min(n_per_class, len(class_indices))

        chosen = np.random.RandomState(42).choice(class_indices, sample_count, replace=False)
        for si in chosen:
            exp = explainer.explain_instance(
                X[si],
                model.predict_proba,
                num_features=15,
                top_labels=len(CLASSES),
            )
            cls_label = list(CLASSES).index(cls_name)
            for feat_name, weight in exp.as_list(label=cls_label):
                for fi, fn in enumerate(feature_names):
                    if fn in feat_name:
                        class_lime_importances[cls_name][fi] += abs(weight)
                        break
        if sample_count > 0:
            class_lime_importances[cls_name] /= sample_count

    # Plot per-class LIME importance
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.suptitle("LIME Feature Importance by Class (averaged, SVM)",
                 fontsize=16, fontweight="bold", y=1.01)

    palette = sns.color_palette("Set2", 4)
    for cls_idx, cls_name in enumerate(CLASSES):
        ax = axes[cls_idx // 2][cls_idx % 2]
        imp = class_lime_importances[cls_name]
        top_k = 15
        top_idx = np.argsort(imp)[-top_k:][::-1]

        ax.barh(range(top_k), imp[top_idx][::-1], color=palette[cls_idx],
                edgecolor="white", linewidth=0.5)
        ax.set_yticks(range(top_k))
        ax.set_yticklabels([feature_names[i] for i in top_idx][::-1], fontsize=9)
        ax.set_xlabel("Mean |LIME weight|", fontsize=10)
        ax.set_title(f"Class: {cls_name}", fontsize=12, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    path_lime_cls = os.path.join(RESULTS_PATH, "lime_importance_per_class_svm.png")
    plt.savefig(path_lime_cls, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Saved: {path_lime_cls}")

    return lime_importances_all


# ==========================================================
# COMPARISON: SHAP vs LIME
# ==========================================================

def compare_shap_lime(shap_importance, lime_importance, feature_names):
    """Side-by-side comparison of global importance from both methods."""

    print("\n" + "=" * 60)
    print("  SHAP vs LIME COMPARISON")
    print("=" * 60)

    top_k = 20

    # Normalise to [0,1] for fair comparison
    shap_norm = shap_importance / (shap_importance.max() + 1e-10)
    lime_norm = lime_importance / (lime_importance.max() + 1e-10)

    # Union of top features from both
    top_shap = set(np.argsort(shap_norm)[-top_k:])
    top_lime = set(np.argsort(lime_norm)[-top_k:])
    top_union = sorted(top_shap | top_lime, key=lambda i: shap_norm[i] + lime_norm[i], reverse=True)[:top_k]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
    fig.suptitle("SHAP vs LIME – Feature Importance Comparison (SVM)",
                 fontsize=16, fontweight="bold")

    y_pos = np.arange(len(top_union))
    bar_height = 0.35

    # Left panel – horizontal bar comparison
    ax1.barh(y_pos - bar_height / 2, [shap_norm[i] for i in top_union],
             bar_height, label="SHAP", color="#3498db", edgecolor="white")
    ax1.barh(y_pos + bar_height / 2, [lime_norm[i] for i in top_union],
             bar_height, label="LIME", color="#e67e22", edgecolor="white")
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels([feature_names[i] for i in top_union], fontsize=9)
    ax1.set_xlabel("Normalised importance", fontsize=11)
    ax1.set_title("Top Features (both methods)", fontsize=13)
    ax1.legend(fontsize=11)
    ax1.invert_yaxis()
    ax1.grid(axis="x", alpha=0.3)

    # Right panel – scatter (correlation)
    ax2.scatter(shap_norm, lime_norm, alpha=0.5, s=30, c="#2c3e50")
    for i in top_union[:10]:
        ax2.annotate(feature_names[i], (shap_norm[i], lime_norm[i]),
                     fontsize=7, alpha=0.8)
    ax2.set_xlabel("SHAP (normalised)", fontsize=11)
    ax2.set_ylabel("LIME (normalised)", fontsize=11)
    ax2.set_title("Correlation of Feature Importance", fontsize=13)
    ax2.plot([0, 1], [0, 1], "k--", alpha=0.3, label="y = x")
    ax2.legend()
    ax2.grid(alpha=0.3)

    correlation = np.corrcoef(shap_norm, lime_norm)[0, 1]
    ax2.text(0.05, 0.92, f"Pearson r = {correlation:.3f}",
             transform=ax2.transAxes, fontsize=12,
             bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"))

    plt.tight_layout()
    path_cmp = os.path.join(RESULTS_PATH, "shap_vs_lime_comparison_svm.png")
    plt.savefig(path_cmp, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✅ Saved: {path_cmp}")
    print(f"  📈 Pearson correlation (SHAP vs LIME): {correlation:.4f}")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  SVM EXPLAINABILITY – SHAP & LIME")
    print("  SafePose — Drug Effect Detection")
    print("=" * 60)

    # ── Load data ─────────────────────────────────────────
    print("\n📂 Loading dataset...")
    X, y = load_dataset()
    feature_names = build_feature_names()

    # Trim or pad feature names to match actual feature count
    n_features = X.shape[1]
    if len(feature_names) > n_features:
        feature_names = feature_names[:n_features]
    elif len(feature_names) < n_features:
        feature_names += [f"feature_{i}" for i in range(len(feature_names), n_features)]

    print(f"  Samples       : {X.shape[0]}")
    print(f"  Features      : {n_features}")
    print(f"  Feature names : {len(feature_names)}")
    print(f"  Classes       : {CLASSES}")
    print(f"  Distribution  : {dict(zip(*np.unique(y, return_counts=True)))}")

    # ── Load or train SVM model ──────────────────────────
    model_file = os.path.join(MODEL_PATH, "drug_classifier_svm.pkl")
    if os.path.exists(model_file):
        print(f"\n📦 Loading saved SVM model: {model_file}")
        model = joblib.load(model_file)
    else:
        print("\n⚠️  No saved model found. Training a new SVM...")
        from sklearn.svm import SVC
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        model = Pipeline([
            ("scaler", StandardScaler()),
            ("svm", SVC(kernel="rbf", C=100, gamma="scale", probability=True))
        ])
        model.fit(X, y)
        joblib.dump(model, model_file)
        print(f"  ✅ Model trained and saved: {model_file}")

    # Quick sanity – verify predictions work
    test_pred = model.predict(X[:2])
    test_prob = model.predict_proba(X[:2])
    print(f"  Sanity check – Predictions: {test_pred}, Probabilities shape: {test_prob.shape}")

    # ── Run SHAP ─────────────────────────────────────────
    shap_values, shap_importance = run_shap_analysis(model, X, feature_names)

    # ── Run LIME ─────────────────────────────────────────
    lime_importance = run_lime_analysis(model, X, y, feature_names)

    # ── Compare SHAP vs LIME ─────────────────────────────
    compare_shap_lime(shap_importance, lime_importance, feature_names)

    # ── Summary ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  EXPLAINABILITY ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"\n📁 All results saved to: {RESULTS_PATH}/")
    print("\nFiles generated:")
    print("  SHAP:")
    print("    - shap_summary_svm.png              (beeswarm per class)")
    print("    - shap_bar_svm.png                  (mean |SHAP| bar)")
    print("    - shap_global_importance_svm.png    (top 20 global)")
    print("  LIME:")
    print("    - lime_explanations_svm.png         (per-class local)")
    print("    - lime_importance_per_class_svm.png (averaged per-class)")
    print("    - lime_explanation_<class>.html      (interactive HTML)")
    print("  Comparison:")
    print("    - shap_vs_lime_comparison_svm.png   (side-by-side)")
