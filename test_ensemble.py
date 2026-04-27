import sys
import os
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
sys.path.append(os.path.join(base_dir, 'api'))

from services.ml_service import ml_service

print("Testing Ensemble Prediction...")
# Create mock 3D tensor representing 35 frames of pose data 
# shape = (35 frames, 33 joints, 4 coords/visibility)
mock_frames = np.random.rand(35, 33, 4).tolist()

try:
    result = ml_service.predict(mock_frames)
    print("\n✅ SUCCESS! Predicted Output:")
    print(result)
except Exception as e:
    print(f"\n❌ FAILURE:")
    import traceback
    traceback.print_exc()
