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
        self.model = joblib.load(Config.MODEL_PATH)
        self.scaler = joblib.load(Config.SCALER_PATH)
        self.label_encoder = joblib.load(Config.ENCODER_PATH)
        print(f"✅ Models loaded! Classes: {self.label_encoder.classes_}")
    
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
        """Extract features from pose sequence"""
        
        features = []
        
        # Stats features
        def stats_features(data):
            reshaped = data.reshape(data.shape[0], -1)
            return [
                np.mean(reshaped),
                np.std(reshaped),
                np.max(reshaped),
                np.min(reshaped),
                np.median(reshaped)
            ]
        
        # Velocity
        velocity = np.diff(sequence, axis=0)
        acceleration = np.diff(velocity, axis=0)
        jerk = np.diff(acceleration, axis=0)
        
        # Raw position stats
        features += stats_features(sequence)
        
        # Velocity stats + energy
        features += stats_features(velocity)
        energy = np.sum(velocity ** 2, axis=0)
        features += energy.flatten().tolist()
        
        # Acceleration stats
        features += stats_features(acceleration)
        
        # Jerk stats
        features += stats_features(jerk)
        
        # Postural sway
        left_hip = sequence[:, 23, :]
        right_hip = sequence[:, 24, :]
        hip_center = (left_hip + right_hip) / 2
        features += [np.std(hip_center[:, 0]), np.std(hip_center[:, 1])]
        
        # Wrist tremor
        left_wrist = velocity[:, 15, :]
        right_wrist = velocity[:, 16, :]
        features += [np.sum(left_wrist ** 2), np.sum(right_wrist ** 2)]
        
        # Symmetry
        pairs = [(11, 12), (13, 14), (15, 16), (25, 26), (27, 28)]
        for left, right in pairs:
            diff = sequence[:, left, :] - sequence[:, right, :]
            features.append(np.mean(np.abs(diff)))
        
        # Entropy
        reshaped = sequence.reshape(sequence.shape[0], -1)
        hist, _ = np.histogram(reshaped, bins=20, density=True)
        hist = hist + 1e-8
        entropy = -np.sum(hist * np.log(hist))
        features.append(entropy)
        
        return np.array(features)
    
    def predict(self, frames):
        """Full prediction pipeline"""
        
        # Preprocess
        sequence = self.preprocess_sequence(frames)
        
        # Extract features
        features = self.extract_features(sequence)
        features = features.reshape(1, -1)
        
        # Scale
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Get class name
        class_name = self.label_encoder.inverse_transform([prediction])[0]
        confidence = float(np.max(probabilities))
        
        # All probabilities
        class_probs = {
            self.label_encoder.classes_[i]: float(prob)
            for i, prob in enumerate(probabilities)
        }
        
        return {
            'prediction': class_name,
            'confidence': confidence,
            'probabilities': class_probs
        }


# Singleton instance
ml_service = MLService()