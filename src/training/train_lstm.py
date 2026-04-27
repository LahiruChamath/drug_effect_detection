import os
import json
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, "data", "pose_sequences")
MODEL_PATH = os.path.join(BASE_DIR, "models")
CLASSES = ["none", "stimulant", "depressant", "cannabis"]

SEQUENCE_LENGTH = 30
N_KEYPOINTS = 33
N_FEATURES = N_KEYPOINTS * 2  # 66


# ==========================================================
# LOAD SEQUENCES - CORRECT VERSION
# ==========================================================

def load_sequences(max_length=SEQUENCE_LENGTH):
    """Load sequences with correct landmark parsing"""
    X = []
    y = []
    
    for label in CLASSES:
        folder = os.path.join(DATA_PATH, label)
        
        if not os.path.exists(folder):
            continue
        
        files = [f for f in os.listdir(folder) if f.endswith(".json")]
        print(f"\n{label}: Processing {len(files)} files...")
        
        for filename in files:
            filepath = os.path.join(folder, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if 'frames' not in data:
                    continue
                
                frames_data = data['frames']
                sequence = []
                
                for frame in frames_data:
                    if not isinstance(frame, dict) or 'landmarks' not in frame:
                        continue
                    
                    landmarks = frame['landmarks']
                    
                    if not isinstance(landmarks, list) or len(landmarks) != 33:
                        continue
                    
                    # Extract x, y from each landmark [x, y, z, visibility]
                    frame_keypoints = []
                    for lm in landmarks:
                        if isinstance(lm, list) and len(lm) >= 2:
                            frame_keypoints.append(float(lm[0]))  # x
                            frame_keypoints.append(float(lm[1]))  # y
                    
                    if len(frame_keypoints) == N_FEATURES:
                        sequence.append(frame_keypoints)
                
                if len(sequence) == 0:
                    continue
                
                sequence = np.array(sequence, dtype=np.float32)
                
                # Pad or truncate
                if len(sequence) > max_length:
                    indices = np.linspace(0, len(sequence)-1, max_length, dtype=int)
                    sequence = sequence[indices]
                elif len(sequence) < max_length:
                    padding = np.zeros((max_length - len(sequence), N_FEATURES), dtype=np.float32)
                    sequence = np.vstack([sequence, padding])
                
                X.append(sequence)
                y.append(label)
                
            except Exception as e:
                print(f"❌ {filename}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Loaded: {len(X)} sequences")
    print(f"{'='*60}")
    
    if len(X) == 0:
        raise ValueError("No sequences loaded!")
    
    return np.array(X, dtype=np.float32), np.array(y)


# ==========================================================
# BUILD MODEL
# ==========================================================

def build_lstm_model(sequence_length, n_features, n_classes):
    model = Sequential([
        Bidirectional(LSTM(64, return_sequences=True),
                     input_shape=(sequence_length, n_features)),
        Dropout(0.4),
        
        Bidirectional(LSTM(32, return_sequences=False)),
        Dropout(0.4),
        
        Dense(32, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        
        Dense(n_classes, activation='softmax')
    ])
    
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model


# ==========================================================
# PLOT CONFUSION MATRIX
# ==========================================================

def plot_confusion_matrix(y_true, y_pred, classes, save_path):
    from sklearn.metrics import confusion_matrix
    
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix - LSTM')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"✅ Saved: {save_path}")
    plt.close()


# ==========================================================
# PLOT TRAINING HISTORY
# ==========================================================

def plot_training_history(history, save_path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.plot(history.history['accuracy'], label='Train', linewidth=2)
    ax1.plot(history.history['val_accuracy'], label='Validation', linewidth=2)
    ax1.set_title('Model Accuracy', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Accuracy')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(history.history['loss'], label='Train', linewidth=2)
    ax2.plot(history.history['val_loss'], label='Validation', linewidth=2)
    ax2.set_title('Model Loss', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    print(f"✅ Saved: {save_path}")
    plt.close()


# ==========================================================
# MAIN
# ==========================================================

def train_lstm():
    print("=" * 60)
    print("LOADING SEQUENCE DATA")
    print("=" * 60)
    
    X, y = load_sequences()
    
    print(f"\nX shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"Classes: {np.unique(y, return_counts=True)}")
    
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    y_categorical = to_categorical(y_encoded, num_classes=len(CLASSES))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_categorical, test_size=0.2, stratify=y_encoded, random_state=42
    )
    
    print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")
    
    print("\n" + "=" * 60)
    print("BUILDING LSTM MODEL")
    print("=" * 60)
    
    model = build_lstm_model(SEQUENCE_LENGTH, N_FEATURES, len(CLASSES))
    model.summary()
    
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True, verbose=1),
        ModelCheckpoint(os.path.join(MODEL_PATH, 'best_lstm_model.h5'),
                       monitor='val_accuracy', save_best_only=True, verbose=1),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=1e-7, verbose=1)
    ]
    
    print("\n" + "=" * 60)
    print("TRAINING LSTM")
    print("=" * 60)
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=100,
        batch_size=4,
        callbacks=callbacks,
        verbose=1
    )
    
    print("\n" + "=" * 60)
    print("EVALUATION")
    print("=" * 60)
    
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test Accuracy: {test_accuracy:.2%}")
    print(f"Test Loss: {test_loss:.4f}")
    
    y_pred_proba = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_proba, axis=1)
    y_true = np.argmax(y_test, axis=1)
    
    from sklearn.metrics import classification_report, confusion_matrix
    
    print("\n" + classification_report(y_true, y_pred, target_names=le.classes_))
    print("Confusion Matrix:")
    print(confusion_matrix(y_true, y_pred))
    
    plot_confusion_matrix(y_true, y_pred, le.classes_,
                         os.path.join(MODEL_PATH, 'confusion_matrix_lstm.png'))
    
    plot_training_history(history, os.path.join(MODEL_PATH, 'lstm_training_history.png'))
    
    model.save(os.path.join(MODEL_PATH, 'drug_classifier_lstm.h5'))
    print(f"\n✅ Model saved!")
    
    print("\n" + "=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)
    print(f"SVM:      83.33%")
    print(f"XGBoost:  85.00%")
    print(f"LSTM:     {test_accuracy:.2%}")
    
    if test_accuracy > 0.85:
        print("\n🎉 LSTM WINS!")
    elif test_accuracy > 0.80:
        print("\n✅ LSTM is competitive")
    else:
        print("\n⚠️ LSTM underperforming (small dataset)")
    
    return model, history


if __name__ == "__main__":
    os.makedirs(MODEL_PATH, exist_ok=True)
    model, history = train_lstm()