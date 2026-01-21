"""
TUTORIAL 1: Basic Pose Detection
This script shows the simplest way to detect pose in a webcam feed.
"""

import cv2
import mediapipe as mp

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Start webcam
cap = cv2.VideoCapture(0)

# Create pose detector
# - static_image_mode=False: Optimized for video (uses tracking)
# - model_complexity=1: Balance between speed and accuracy (0, 1, or 2)
# - min_detection_confidence: How confident before detecting
# - min_tracking_confidence: How confident to keep tracking

with mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose:
    
    print("Press 'q' to quit")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to read from webcam")
            break
        
        # Flip for mirror effect (optional)
        frame = cv2.flip(frame, 1)
        
        # IMPORTANT: MediaPipe needs RGB, OpenCV uses BGR
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = pose.process(rgb_frame)
        
        # Draw the pose if detected
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style()
            )
        
        # Display
        cv2.imshow('Basic Pose Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print("Done!")