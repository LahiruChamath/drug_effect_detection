from preprocessing import preprocess_sequence
from feature_extraction import extract_features
import numpy as np

# Replace this path with your real file path
filepath = "../data/pose_sequences/depressant/depressant_20260121_235900_000.json"

processed = preprocess_sequence(filepath)

print("Final shape:", processed.shape)
print("Any NaNs?", np.isnan(processed).any())

features = extract_features(processed)

print("Feature vector shape:", features.shape)