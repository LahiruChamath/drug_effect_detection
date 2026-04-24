import numpy as np
import joblib
from config import Config


class MLService:
    """Machine Learning Service for predictions"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        """Load ML models"""
        print("Loading ML models...")
        self.xgb_model = joblib.load(Config.MODEL_PATH)
        self.svm_model = joblib.load(Config.SVM_PATH)
        self.scaler = joblib.load(Config.SCALER_PATH)
        self.label_encoder = joblib.load(Config.ENCODER_PATH)
        
        try:
            from tensorflow.keras.models import load_model
            self.lstm_model = load_model(Config.LSTM_PATH)
            print("✅ LSTM model loaded!")
        except Exception as e:
            print(f"❌ Failed to load LSTM model: {e}")
            self.lstm_model = None
            
        print(f"✅ XGBoost and SVM models loaded! Classes: {self.label_encoder.classes_}")
    
    def preprocess_sequence(self, frames, target_frames=200):
        """Preprocess raw landmark data"""
        
        data = np.array(frames)
        coords = data[:, :, :3]
        visibility = data[:, :, 3]
        
        # Clean low visibility
        coords[visibility < 0.5] = np.nan
        
        # Interpolate
        frames_count, joints, dims = coords.shape
        for j in range(joints):
            for d in range(dims):
                series = coords[:, j, d]
                if np.isnan(series).any():
                    valid = ~np.isnan(series)
                    if valid.sum() > 1:
                        coords[:, j, d] = np.interp(
                            np.arange(frames_count),
                            np.where(valid)[0],
                            series[valid]
                        )
                    else:
                        coords[:, j, d] = 0
        
        # Center skeleton
        left_hip = coords[:, 23, :]
        right_hip = coords[:, 24, :]
        hip_center = (left_hip + right_hip) / 2
        coords = coords - hip_center[:, np.newaxis, :]
        
        # Scale normalize
        left_shoulder = coords[:, 11, :]
        right_shoulder = coords[:, 12, :]
        shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder, axis=1)
        shoulder_dist[shoulder_dist == 0] = 1e-6
        coords = coords / shoulder_dist[:, np.newaxis, np.newaxis]
        
        # Resample
        original_frames = coords.shape[0]
        new_data = np.zeros((target_frames, joints, dims))
        
        old_indices = np.linspace(0, original_frames - 1, original_frames)
        new_indices = np.linspace(0, original_frames - 1, target_frames)
        
        for j in range(joints):
            for d in range(dims):
                new_data[:, j, d] = np.interp(new_indices, old_indices, coords[:, j, d])
        
        return new_data
    
    def extract_features(self, sequence):
        """Extract features from pose sequence — v2 (230 features)
        
        Must match src/feature_extraction.py exactly:
          5  raw position stats
          5  velocity stats
         99  joint energy (velocity)
         66  per-joint velocity mean+std   (NEW)
          5  acceleration stats
         33  per-joint acceleration mag    (NEW)
          5  jerk stats
          2  postural sway
          2  head sway                     (NEW)
          2  wrist tremor
          5  symmetry
          1  entropy
        ───────
        230  total
        """
        
        features = []
        
        # Stats features helper
        def stats_features(data):
            reshaped = data.reshape(data.shape[0], -1)
            return [
                np.mean(reshaped),
                np.std(reshaped),
                np.max(reshaped),
                np.min(reshaped),
                np.median(reshaped)
            ]
        
        # Derivatives
        velocity = np.diff(sequence, axis=0)
        acceleration = np.diff(velocity, axis=0)
        jerk = np.diff(acceleration, axis=0)
        
        # ---- Raw position stats (5) ----
        features += stats_features(sequence)
        
        # ---- Velocity stats (5) + joint energy (99) ----
        features += stats_features(velocity)
        energy = np.sum(velocity ** 2, axis=0)
        features += energy.flatten().tolist()
        
        # ---- Per-joint velocity mean & std (66) — NEW ----
        speed = np.linalg.norm(velocity, axis=2)       # (T-1, 33)
        mean_speed = np.mean(speed, axis=0)             # (33,)
        std_speed  = np.std(speed, axis=0)              # (33,)
        features += np.concatenate([mean_speed, std_speed]).tolist()
        
        # ---- Acceleration stats (5) ----
        features += stats_features(acceleration)
        
        # ---- Per-joint acceleration magnitude (33) — NEW ----
        accel_mag = np.linalg.norm(acceleration, axis=2)  # (T-2, 33)
        features += np.mean(accel_mag, axis=0).tolist()    # (33,)
        
        # ---- Jerk stats (5) ----
        features += stats_features(jerk)
        
        # ---- Postural sway (2) ----
        left_hip = sequence[:, 23, :]
        right_hip = sequence[:, 24, :]
        hip_center = (left_hip + right_hip) / 2
        features += [np.std(hip_center[:, 0]), np.std(hip_center[:, 1])]
        
        # ---- Head sway (2) — NEW ----
        nose = sequence[:, 0, :]
        features += [np.std(nose[:, 0]), np.std(nose[:, 1])]
        
        # ---- Wrist tremor (2) ----
        left_wrist = velocity[:, 15, :]
        right_wrist = velocity[:, 16, :]
        features += [np.sum(left_wrist ** 2), np.sum(right_wrist ** 2)]
        
        # ---- Symmetry (5) ----
        pairs = [(11, 12), (13, 14), (15, 16), (25, 26), (27, 28)]
        for left, right in pairs:
            diff = sequence[:, left, :] - sequence[:, right, :]
            features.append(np.mean(np.abs(diff)))
        
        # ---- Entropy (1) ----
        reshaped = sequence.reshape(sequence.shape[0], -1)
        hist, _ = np.histogram(reshaped, bins=20, density=True)
        hist = hist + 1e-8
        entropy = -np.sum(hist * np.log(hist))
        features.append(entropy)
        
        return np.array(features)
    
    def predict(self, frames):
        """Full prediction pipeline with Ensemble Soft Voting"""
        
        # 1. Pipeline for XGBoost and SVM (200 frames -> 230 extracted features)
        sequence_200 = self.preprocess_sequence(frames, target_frames=200)
        features = self.extract_features(sequence_200)
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        
        xgb_probs = self.xgb_model.predict_proba(features_scaled)[0]
        svm_probs = self.svm_model.predict_proba(features_scaled)[0]
        
        # 2. Pipeline for LSTM (60 frames, 99 features = 33 joints × 3 coords)
        if hasattr(self, 'lstm_model') and self.lstm_model is not None:
            raw_data = np.array(frames)
            # Extract X, Y, Z (33 joints * 3 coords = 99 features per frame)
            raw_xyz = raw_data[:, :, :3].reshape(raw_data.shape[0], 99)
            
            target_frames = 60
            if len(raw_xyz) > target_frames:
                indices = np.linspace(0, len(raw_xyz)-1, target_frames, dtype=int)
                lstm_seq = raw_xyz[indices]
            elif len(raw_xyz) < target_frames:
                padding = np.zeros((target_frames - len(raw_xyz), 99), dtype=np.float32)
                lstm_seq = np.vstack([raw_xyz, padding])
            else:
                lstm_seq = raw_xyz
                
            lstm_input = lstm_seq.reshape(1, target_frames, 99).astype(np.float32)
            lstm_probs = self.lstm_model.predict(lstm_input, verbose=0)[0]
            
            # Average 3 models
            avg_probs = (xgb_probs + svm_probs + lstm_probs) / 3.0
        else:
            # Fallback to 2 models if LSTM isn't loaded
            avg_probs = (xgb_probs + svm_probs) / 2.0
            
        # Predict class index using averaged probabilities
        prediction_idx = np.argmax(avg_probs)
        class_name = self.label_encoder.inverse_transform([prediction_idx])[0]
        confidence = float(np.max(avg_probs))
        
        # Format probabilities dict mapping
        class_probs = {
            self.label_encoder.classes_[i]: float(prob)
            for i, prob in enumerate(avg_probs)
        }
        
        return {
            'prediction': class_name,
            'confidence': confidence,
            'probabilities': class_probs
        }


# Singleton instance
ml_service = MLService()