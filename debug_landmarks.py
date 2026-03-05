# debug_landmarks.py
import json
import os

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data", "pose_sequences", "none"
)

# Get first file
files = [f for f in os.listdir(DATA_PATH) if f.endswith('.json')]
filepath = os.path.join(DATA_PATH, files[0])

print(f"File: {files[0]}")

with open(filepath, 'r') as f:
    data = json.load(f)

# Get first frame
frame = data['frames'][0]
landmarks = frame['landmarks']

print(f"\nlandmarks type: {type(landmarks)}")
print(f"landmarks length: {len(landmarks)}")
print(f"\nFirst 5 elements:")
for i in range(min(5, len(landmarks))):
    print(f"  [{i}] type={type(landmarks[i])}, value={landmarks[i]}")

print(f"\nFull landmarks (first 20 values):")
print(landmarks[:20])