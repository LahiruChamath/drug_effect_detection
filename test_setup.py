# test_setup.py
import sys
print(f"Python version: {sys.version}")

print("\nChecking packages...")

try:
    import cv2
    print(f"✅ OpenCV: {cv2.__version__}")
except ImportError as e:
    print(f"❌ OpenCV: {e}")

try:
    import mediapipe as mp
    print(f"✅ MediaPipe: {mp.__version__}")
except ImportError as e:
    print(f"❌ MediaPipe: {e}")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError as e:
    print(f"❌ NumPy: {e}")

try:
    import pandas as pd
    print(f"✅ Pandas: {pd.__version__}")
except ImportError as e:
    print(f"❌ Pandas: {e}")

try:
    import scipy
    print(f"✅ SciPy: {scipy.__version__}")
except ImportError as e:
    print(f"❌ SciPy: {e}")

try:
    import sklearn
    print(f"✅ Scikit-learn: {sklearn.__version__}")
except ImportError as e:
    print(f"❌ Scikit-learn: {e}")

print("\n" + "="*50)
print("Testing MediaPipe Pose...")
print("="*50)

try:
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=True)
    print("✅ MediaPipe Pose initialized successfully!")
    pose.close()
except Exception as e:
    print(f"❌ MediaPipe Pose failed: {e}")

print("\n🎉 Setup complete! You're ready to start!")
