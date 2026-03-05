import os
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler, LabelEncoder, label_binarize
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    auc,
    roc_auc_score,
    log_loss
)
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

from src.preprocessing import preprocess_sequence
from src.feature_extraction import extract_features


# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "pose_sequences")
RESULTS_PATH = os.path.join(BASE_DIR, "results")
CLASSES = ["none", "stimulant", "depressant", "cannabis"]
N_CLASSES = len(CLASSES)

# Create results directory
os.makedirs(RESULTS_PATH, exist_ok=True)


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
# LOAD SEQUENCE DATA (FOR LSTM)
# ==========================================================

def load_sequence_data(target_frames=30):
    """Load raw sequences for LSTM"""
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
                    sequence = preprocess_sequence(filepath, target_frames=target_frames)
                    # Reshape: (frames, 33, 3) -> (frames, 99) or (frames, 66)
                    sequence_flat = sequence.reshape(target_frames, -1)
                    X.append(sequence_flat)
                    y.append(label)

                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    return np.array(X), np.array(y)


# ==========================================================
# COMPUTE ALL METRICS
# ==========================================================

def compute_metrics(y_true, y_pred, y_prob, classes):
    """Compute all classification metrics"""
    
    metrics = {}
    
    # Basic metrics
    metrics['accuracy'] = accuracy_score(y_true, y_pred)
    metrics['precision_macro'] = precision_score(y_true, y_pred, average='macro')
    metrics['precision_weighted'] = precision_score(y_true, y_pred, average='weighted')
    metrics['recall_macro'] = recall_score(y_true, y_pred, average='macro')
    metrics['recall_weighted'] = recall_score(y_true, y_pred, average='weighted')
    metrics['f1_macro'] = f1_score(y_true, y_pred, average='macro')
    metrics['f1_weighted'] = f1_score(y_true, y_pred, average='weighted')
    
    # Per-class metrics
    metrics['precision_per_class'] = precision_score(y_true, y_pred, average=None)
    metrics['recall_per_class'] = recall_score(y_true, y_pred, average=None)
    metrics['f1_per_class'] = f1_score(y_true, y_pred, average=None)
    
    # Loss (cross-entropy)
    if y_prob is not None:
        metrics['log_loss'] = log_loss(y_true, y_prob)
    else:
        metrics['log_loss'] = None
    
    # ROC AUC (One-vs-Rest)
    if y_prob is not None:
        # Binarize labels for ROC
        y_true_bin = label_binarize(y_true, classes=range(len(classes)))
        
        # Compute ROC AUC for each class
        metrics['roc_auc_per_class'] = {}
        for i, class_name in enumerate(classes):
            fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_prob[:, i])
            metrics['roc_auc_per_class'][class_name] = auc(fpr, tpr)
        
        # Macro average ROC AUC
        metrics['roc_auc_macro'] = roc_auc_score(y_true_bin, y_prob, average='macro')
        metrics['roc_auc_weighted'] = roc_auc_score(y_true_bin, y_prob, average='weighted')
    else:
        metrics['roc_auc_per_class'] = None
        metrics['roc_auc_macro'] = None
        metrics['roc_auc_weighted'] = None
    
    return metrics


# ==========================================================
# PLOT ROC CURVES
# ==========================================================

def plot_roc_curves(y_true, y_prob, classes, model_name, save_path):
    """Plot ROC curves for each class"""
    
    y_true_bin = label_binarize(y_true, classes=range(len(classes)))
    
    plt.figure(figsize=(10, 8))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    for i, (class_name, color) in enumerate(zip(classes, colors)):
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_prob[:, i])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, color=color, lw=2,
                 label=f'{class_name} (AUC = {roc_auc:.3f})')
    
    plt.plot([0, 1], [0, 1], 'k--', lw=2, label='Random (AUC = 0.500)')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title(f'ROC Curves - {model_name}', fontsize=14)
    plt.legend(loc='lower right', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"✅ Saved: {save_path}")


# ==========================================================
# PLOT CONFUSION MATRIX
# ==========================================================

def plot_confusion_matrix(y_true, y_pred, classes, model_name, save_path):
    """Plot confusion matrix"""
    
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes,
                yticklabels=classes)
    plt.xlabel('Predicted', fontsize=12)
    plt.ylabel('Actual', fontsize=12)
    plt.title(f'Confusion Matrix - {model_name}', fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"✅ Saved: {save_path}")


# ==========================================================
# PRINT REPORT
# ==========================================================

def print_full_report(model_name, metrics, classes):
    """Print formatted classification report"""
    
    print("\n" + "=" * 70)
    print(f"  {model_name} - COMPLETE CLASSIFICATION REPORT")
    print("=" * 70)
    
    # Overall Metrics
    print("\n📊 OVERALL METRICS")
    print("-" * 40)
    print(f"  Accuracy:           {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"  Precision (macro):  {metrics['precision_macro']:.4f}")
    print(f"  Precision (weighted): {metrics['precision_weighted']:.4f}")
    print(f"  Recall (macro):     {metrics['recall_macro']:.4f}")
    print(f"  Recall (weighted):  {metrics['recall_weighted']:.4f}")
    print(f"  F1-Score (macro):   {metrics['f1_macro']:.4f}")
    print(f"  F1-Score (weighted): {metrics['f1_weighted']:.4f}")
    
    if metrics['log_loss'] is not None:
        print(f"  Log Loss:           {metrics['log_loss']:.4f}")
    
    if metrics['roc_auc_macro'] is not None:
        print(f"  ROC AUC (macro):    {metrics['roc_auc_macro']:.4f}")
        print(f"  ROC AUC (weighted): {metrics['roc_auc_weighted']:.4f}")
    
    # Per-Class Metrics
    print("\n📈 PER-CLASS METRICS")
    print("-" * 70)
    print(f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'ROC AUC':<12}")
    print("-" * 70)
    
    for i, class_name in enumerate(classes):
        precision = metrics['precision_per_class'][i]
        recall = metrics['recall_per_class'][i]
        f1 = metrics['f1_per_class'][i]
        
        if metrics['roc_auc_per_class'] is not None:
            roc_auc = metrics['roc_auc_per_class'][class_name]
            print(f"{class_name:<15} {precision:<12.4f} {recall:<12.4f} {f1:<12.4f} {roc_auc:<12.4f}")
        else:
            print(f"{class_name:<15} {precision:<12.4f} {recall:<12.4f} {f1:<12.4f} {'N/A':<12}")
    
    print("-" * 70)


# ==========================================================
# SAVE REPORT TO FILE
# ==========================================================

def save_report_to_file(model_name, metrics, classes, filepath):
    """Save report to text file"""
    
    with open(filepath, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write(f"  {model_name} - COMPLETE CLASSIFICATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("OVERALL METRICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Accuracy:             {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)\n")
        f.write(f"Precision (macro):    {metrics['precision_macro']:.4f}\n")
        f.write(f"Precision (weighted): {metrics['precision_weighted']:.4f}\n")
        f.write(f"Recall (macro):       {metrics['recall_macro']:.4f}\n")
        f.write(f"Recall (weighted):    {metrics['recall_weighted']:.4f}\n")
        f.write(f"F1-Score (macro):     {metrics['f1_macro']:.4f}\n")
        f.write(f"F1-Score (weighted):  {metrics['f1_weighted']:.4f}\n")
        
        if metrics['log_loss'] is not None:
            f.write(f"Log Loss:             {metrics['log_loss']:.4f}\n")
        
        if metrics['roc_auc_macro'] is not None:
            f.write(f"ROC AUC (macro):      {metrics['roc_auc_macro']:.4f}\n")
            f.write(f"ROC AUC (weighted):   {metrics['roc_auc_weighted']:.4f}\n")
        
        f.write("\n\nPER-CLASS METRICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'ROC AUC':<12}\n")
        f.write("-" * 70 + "\n")
        
        for i, class_name in enumerate(classes):
            precision = metrics['precision_per_class'][i]
            recall = metrics['recall_per_class'][i]
            f1 = metrics['f1_per_class'][i]
            
            if metrics['roc_auc_per_class'] is not None:
                roc_auc = metrics['roc_auc_per_class'][class_name]
                f.write(f"{class_name:<15} {precision:<12.4f} {recall:<12.4f} {f1:<12.4f} {roc_auc:<12.4f}\n")
            else:
                f.write(f"{class_name:<15} {precision:<12.4f} {recall:<12.4f} {f1:<12.4f} {'N/A':<12}\n")
    
    print(f"✅ Saved: {filepath}")


# ==========================================================
# EVALUATE SVM
# ==========================================================

def evaluate_svm(X, y, le):
    """Train and evaluate SVM with full metrics"""
    
    print("\n" + "=" * 70)
    print("  EVALUATING SVM")
    print("=" * 70)
    
    y_encoded = le.transform(y)
    
    # Best parameters from your training
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(kernel='rbf', C=100, gamma='scale', probability=True))
    ])
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Get predictions and probabilities
    y_pred = cross_val_predict(model, X, y_encoded, cv=skf)
    y_prob = cross_val_predict(model, X, y_encoded, cv=skf, method='predict_proba')
    
    # Compute metrics
    metrics = compute_metrics(y_encoded, y_pred, y_prob, CLASSES)
    
    # Print report
    print_full_report("SVM", metrics, CLASSES)
    
    # Plot confusion matrix
    plot_confusion_matrix(y_encoded, y_pred, CLASSES, "SVM",
                         os.path.join(RESULTS_PATH, "confusion_matrix_svm.png"))
    
    # Plot ROC curves
    plot_roc_curves(y_encoded, y_prob, CLASSES, "SVM",
                   os.path.join(RESULTS_PATH, "roc_curves_svm.png"))
    
    # Save report
    save_report_to_file("SVM", metrics, CLASSES,
                       os.path.join(RESULTS_PATH, "classification_report_svm.txt"))
    
    return metrics


# ==========================================================
# EVALUATE XGBOOST
# ==========================================================

def evaluate_xgboost(X, y, le):
    """Train and evaluate XGBoost with full metrics"""
    
    print("\n" + "=" * 70)
    print("  EVALUATING XGBOOST")
    print("=" * 70)
    
    y_encoded = le.transform(y)
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Best parameters from your training
    model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.2,
        subsample=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric='mlogloss'
    )
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Get predictions and probabilities
    y_pred = cross_val_predict(model, X_scaled, y_encoded, cv=skf)
    y_prob = cross_val_predict(model, X_scaled, y_encoded, cv=skf, method='predict_proba')
    
    # Compute metrics
    metrics = compute_metrics(y_encoded, y_pred, y_prob, CLASSES)
    
    # Print report
    print_full_report("XGBoost", metrics, CLASSES)
    
    # Plot confusion matrix
    plot_confusion_matrix(y_encoded, y_pred, CLASSES, "XGBoost",
                         os.path.join(RESULTS_PATH, "confusion_matrix_xgboost.png"))
    
    # Plot ROC curves
    plot_roc_curves(y_encoded, y_prob, CLASSES, "XGBoost",
                   os.path.join(RESULTS_PATH, "roc_curves_xgboost.png"))
    
    # Save report
    save_report_to_file("XGBoost", metrics, CLASSES,
                       os.path.join(RESULTS_PATH, "classification_report_xgboost.txt"))
    
    return metrics


# ==========================================================
# EVALUATE LSTM
# ==========================================================

def evaluate_lstm(X_seq, y, le):
    """Train and evaluate LSTM with full metrics"""
    
    print("\n" + "=" * 70)
    print("  EVALUATING LSTM")
    print("=" * 70)
    
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization
        from tensorflow.keras.utils import to_categorical
        from sklearn.model_selection import train_test_split
    except ImportError:
        print("❌ TensorFlow not installed. Skipping LSTM evaluation.")
        return None
    
    y_encoded = le.transform(y)
    y_cat = to_categorical(y_encoded, num_classes=N_CLASSES)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_seq, y_cat, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Build model
    model = Sequential([
        Bidirectional(LSTM(64, return_sequences=True), input_shape=(X_seq.shape[1], X_seq.shape[2])),
        Dropout(0.3),
        Bidirectional(LSTM(32)),
        Dropout(0.3),
        Dense(32, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(N_CLASSES, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Train
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=4,
        validation_data=(X_test, y_test),
        verbose=0
    )
    
    # Predictions
    y_prob = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_prob, axis=1)
    y_true = np.argmax(y_test, axis=1)
    
    # Compute metrics
    metrics = compute_metrics(y_true, y_pred, y_prob, CLASSES)
    
    # Add training loss
    metrics['training_loss'] = history.history['loss'][-1]
    metrics['validation_loss'] = history.history['val_loss'][-1]
    
    # Print report
    print_full_report("LSTM", metrics, CLASSES)
    print(f"\n  Training Loss:     {metrics['training_loss']:.4f}")
    print(f"  Validation Loss:   {metrics['validation_loss']:.4f}")
    
    # Plot confusion matrix
    plot_confusion_matrix(y_true, y_pred, CLASSES, "LSTM",
                         os.path.join(RESULTS_PATH, "confusion_matrix_lstm.png"))
    
    # Plot ROC curves
    plot_roc_curves(y_true, y_prob, CLASSES, "LSTM",
                   os.path.join(RESULTS_PATH, "roc_curves_lstm.png"))
    
    # Save report
    save_report_to_file("LSTM", metrics, CLASSES,
                       os.path.join(RESULTS_PATH, "classification_report_lstm.txt"))
    
    # Plot training history
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('LSTM - Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('LSTM - Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_PATH, "lstm_training_history.png"), dpi=150)
    plt.close()
    print(f"✅ Saved: {os.path.join(RESULTS_PATH, 'lstm_training_history.png')}")
    
    return metrics


# ==========================================================
# COMPARISON SUMMARY
# ==========================================================

def create_comparison_summary(svm_metrics, xgb_metrics, lstm_metrics):
    """Create comparison table of all models"""
    
    print("\n" + "=" * 70)
    print("  MODEL COMPARISON SUMMARY")
    print("=" * 70)
    
    # Table header
    print(f"\n{'Metric':<25} {'SVM':<15} {'XGBoost':<15} {'LSTM':<15}")
    print("-" * 70)
    
    # Accuracy
    lstm_acc = lstm_metrics['accuracy'] if lstm_metrics else 'N/A'
    print(f"{'Accuracy':<25} {svm_metrics['accuracy']:<15.4f} {xgb_metrics['accuracy']:<15.4f} {lstm_acc if isinstance(lstm_acc, str) else f'{lstm_acc:<15.4f}'}")
    
    # Precision
    lstm_prec = lstm_metrics['precision_macro'] if lstm_metrics else 'N/A'
    print(f"{'Precision (macro)':<25} {svm_metrics['precision_macro']:<15.4f} {xgb_metrics['precision_macro']:<15.4f} {lstm_prec if isinstance(lstm_prec, str) else f'{lstm_prec:<15.4f}'}")
    
    # Recall
    lstm_rec = lstm_metrics['recall_macro'] if lstm_metrics else 'N/A'
    print(f"{'Recall (macro)':<25} {svm_metrics['recall_macro']:<15.4f} {xgb_metrics['recall_macro']:<15.4f} {lstm_rec if isinstance(lstm_rec, str) else f'{lstm_rec:<15.4f}'}")
    
    # F1
    lstm_f1 = lstm_metrics['f1_macro'] if lstm_metrics else 'N/A'
    print(f"{'F1-Score (macro)':<25} {svm_metrics['f1_macro']:<15.4f} {xgb_metrics['f1_macro']:<15.4f} {lstm_f1 if isinstance(lstm_f1, str) else f'{lstm_f1:<15.4f}'}")
    
    # Log Loss
    lstm_loss = lstm_metrics['log_loss'] if lstm_metrics else 'N/A'
    print(f"{'Log Loss':<25} {svm_metrics['log_loss']:<15.4f} {xgb_metrics['log_loss']:<15.4f} {lstm_loss if isinstance(lstm_loss, str) else f'{lstm_loss:<15.4f}'}")
    
    # ROC AUC
    lstm_auc = lstm_metrics['roc_auc_macro'] if lstm_metrics else 'N/A'
    print(f"{'ROC AUC (macro)':<25} {svm_metrics['roc_auc_macro']:<15.4f} {xgb_metrics['roc_auc_macro']:<15.4f} {lstm_auc if isinstance(lstm_auc, str) else f'{lstm_auc:<15.4f}'}")
    
    print("-" * 70)
    
    # Save comparison to file
    comparison_file = os.path.join(RESULTS_PATH, "model_comparison_summary.txt")
    with open(comparison_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("  MODEL COMPARISON SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"{'Metric':<25} {'SVM':<15} {'XGBoost':<15} {'LSTM':<15}\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Accuracy':<25} {svm_metrics['accuracy']:<15.4f} {xgb_metrics['accuracy']:<15.4f} {lstm_acc if isinstance(lstm_acc, str) else f'{lstm_acc:<15.4f}'}\n")
        f.write(f"{'Precision (macro)':<25} {svm_metrics['precision_macro']:<15.4f} {xgb_metrics['precision_macro']:<15.4f} {lstm_prec if isinstance(lstm_prec, str) else f'{lstm_prec:<15.4f}'}\n")
        f.write(f"{'Recall (macro)':<25} {svm_metrics['recall_macro']:<15.4f} {xgb_metrics['recall_macro']:<15.4f} {lstm_rec if isinstance(lstm_rec, str) else f'{lstm_rec:<15.4f}'}\n")
        f.write(f"{'F1-Score (macro)':<25} {svm_metrics['f1_macro']:<15.4f} {xgb_metrics['f1_macro']:<15.4f} {lstm_f1 if isinstance(lstm_f1, str) else f'{lstm_f1:<15.4f}'}\n")
        f.write(f"{'Log Loss':<25} {svm_metrics['log_loss']:<15.4f} {xgb_metrics['log_loss']:<15.4f} {lstm_loss if isinstance(lstm_loss, str) else f'{lstm_loss:<15.4f}'}\n")
        f.write(f"{'ROC AUC (macro)':<25} {svm_metrics['roc_auc_macro']:<15.4f} {xgb_metrics['roc_auc_macro']:<15.4f} {lstm_auc if isinstance(lstm_auc, str) else f'{lstm_auc:<15.4f}'}\n")
    
    print(f"\n✅ Saved: {comparison_file}")


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    
    print("=" * 70)
    print("  COMPLETE MODEL EVALUATION")
    print("  SafePose - Drug Effect Detection")
    print("=" * 70)
    
    # Load data
    print("\n📂 Loading feature data...")
    X, y = load_dataset()
    print(f"   Features shape: {X.shape}")
    print(f"   Labels: {np.unique(y, return_counts=True)}")
    
    # Label encoder
    le = LabelEncoder()
    le.fit(CLASSES)
    
    # Load sequence data for LSTM
    print("\n📂 Loading sequence data for LSTM...")
    X_seq, y_seq = load_sequence_data(target_frames=30)
    print(f"   Sequences shape: {X_seq.shape}")
    
    # Evaluate all models
    svm_metrics = evaluate_svm(X, y, le)
    xgb_metrics = evaluate_xgboost(X, y, le)
    lstm_metrics = evaluate_lstm(X_seq, y_seq, le)
    
    # Comparison summary
    create_comparison_summary(svm_metrics, xgb_metrics, lstm_metrics)
    
    print("\n" + "=" * 70)
    print("  EVALUATION COMPLETE!")
    print("=" * 70)
    print(f"\n📁 All results saved to: {RESULTS_PATH}/")
    print("\nFiles generated:")
    print("  - classification_report_svm.txt")
    print("  - classification_report_xgboost.txt")
    print("  - classification_report_lstm.txt")
    print("  - confusion_matrix_svm.png")
    print("  - confusion_matrix_xgboost.png")
    print("  - confusion_matrix_lstm.png")
    print("  - roc_curves_svm.png")
    print("  - roc_curves_xgboost.png")
    print("  - roc_curves_lstm.png")
    print("  - lstm_training_history.png")
    print("  - model_comparison_summary.txt")