"""
TUTORIAL 2: Understanding Pose Landmarks
Learn what data MediaPipe gives you for each body point.
"""

import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Landmark names for reference
LANDMARK_NAMES = {
    0: 'NOSE',
    1: 'LEFT_EYE_INNER', 2: 'LEFT_EYE', 3: 'LEFT_EYE_OUTER',
    4: 'RIGHT_EYE_INNER', 5: 'RIGHT_EYE', 6: 'RIGHT_EYE_OUTER',
    7: 'LEFT_EAR', 8: 'RIGHT_EAR',
    9: 'MOUTH_LEFT', 10: 'MOUTH_RIGHT',
    11: 'LEFT_SHOULDER', 12: 'RIGHT_SHOULDER',
    13: 'LEFT_ELBOW', 14: 'RIGHT_ELBOW',
    15: 'LEFT_WRIST', 16: 'RIGHT_WRIST',
    17: 'LEFT_PINKY', 18: 'RIGHT_PINKY',
    19: 'LEFT_INDEX', 20: 'RIGHT_INDEX',
    21: 'LEFT_THUMB', 22: 'RIGHT_THUMB',
    23: 'LEFT_HIP', 24: 'RIGHT_HIP',
    25: 'LEFT_KNEE', 26: 'RIGHT_KNEE',
    27: 'LEFT_ANKLE', 28: 'RIGHT_ANKLE',
    29: 'LEFT_HEEL', 30: 'RIGHT_HEEL',
    31: 'LEFT_FOOT_INDEX', 32: 'RIGHT_FOOT_INDEX'
}

cap = cv2.VideoCapture(0)

with mp_pose.Pose(min_detection_confidence=0.5) as pose:
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        if results.pose_landmarks:
            # Draw skeleton
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS
            )
            
            # Let's examine specific landmarks
            landmarks = results.pose_landmarks.landmark
            
            # Example: Get nose position
            nose = landmarks[0]
            
            # Each landmark has:
            # - x: horizontal position (0 to 1, left to right)
            # - y: vertical position (0 to 1, top to bottom)
            # - z: depth (smaller = closer to camera)
            # - visibility: confidence that landmark is visible (0 to 1)
            
            # Convert normalized coordinates to pixel coordinates
            nose_x = int(nose.x * w)
            nose_y = int(nose.y * h)
            
            # Draw info box
            info_y = 30
            cv2.putText(frame, "LANDMARK DATA:", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            info_y += 25
            cv2.putText(frame, f"Nose X: {nose.x:.3f} (pixel: {nose_x})", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            info_y += 20
            cv2.putText(frame, f"Nose Y: {nose.y:.3f} (pixel: {nose_y})", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            info_y += 20
            cv2.putText(frame, f"Nose Z: {nose.z:.3f} (depth)", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            info_y += 20
            cv2.putText(frame, f"Visibility: {nose.visibility:.3f}", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Draw circle on nose
            cv2.circle(frame, (nose_x, nose_y), 10, (0, 0, 255), -1)
            
            # Show wrist positions (important for your project!)
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            
            info_y += 30
            cv2.putText(frame, f"Left Wrist: ({left_wrist.x:.2f}, {left_wrist.y:.2f})", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            info_y += 20
            cv2.putText(frame, f"Right Wrist: ({right_wrist.x:.2f}, {right_wrist.y:.2f})", 
                       (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        cv2.imshow('Understanding Landmarks', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()