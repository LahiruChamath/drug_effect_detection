"""
TUTORIAL 3: Extract and Save Pose Data
This is the foundation of your data collection!
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import os
from datetime import datetime

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


def extract_landmarks_to_array(landmarks) -> np.ndarray:
    """
    Convert MediaPipe landmarks to a numpy array.
    
    Returns:
        np.ndarray of shape (33, 4) containing [x, y, z, visibility] for each landmark
    """
    return np.array([
        [lm.x, lm.y, lm.z, lm.visibility]
        for lm in landmarks.landmark
    ])


def save_pose_sequence(frames_data: list, metadata: dict, filepath: str):
    """
    Save pose sequence to JSON file.
    This is your anonymized, privacy-safe data format!
    """
    data = {
        'metadata': metadata,
        'frames': frames_data
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Saved {len(frames_data)} frames to {filepath}")


def record_pose_sequence(duration_seconds: float = 10.0, 
                         output_dir: str = "data/pose_sequences"):
    """
    Record a pose sequence from webcam.
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0  # Default to 30 if unknown
    
    frames_data = []
    start_time = None
    recording = False
    
    with mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:
        
        print("\n" + "="*50)
        print("POSE SEQUENCE RECORDER")
        print("="*50)
        print(f"Duration: {duration_seconds} seconds")
        print("Press SPACE to start recording")
        print("Press 'q' to quit")
        print("="*50 + "\n")
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            
            # Draw skeleton
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )
            
            # Recording logic
            if recording:
                elapsed = cv2.getTickCount() / cv2.getTickFrequency() - start_time
                remaining = duration_seconds - elapsed
                
                if remaining <= 0:
                    # Recording complete
                    recording = False
                    
                    # Generate filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"pose_sequence_{timestamp}.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save data
                    metadata = {
                        'fps': fps,
                        'duration': duration_seconds,
                        'total_frames': len(frames_data),
                        'recorded_at': timestamp,
                        'label': None  # To be filled during labeling
                    }
                    
                    save_pose_sequence(frames_data, metadata, filepath)
                    
                    # Reset
                    frames_data = []
                    print("\nRecording complete! Press SPACE to record another.")
                else:
                    # Save current frame
                    if results.pose_landmarks:
                        landmarks_array = extract_landmarks_to_array(results.pose_landmarks)
                        frames_data.append({
                            'timestamp': elapsed,
                            'landmarks': landmarks_array.tolist()
                        })
                    else:
                        # No detection - save null
                        frames_data.append({
                            'timestamp': elapsed,
                            'landmarks': None
                        })
                    
                    # Show recording indicator
                    cv2.circle(frame, (30, 30), 15, (0, 0, 255), -1)
                    cv2.putText(frame, f"REC {remaining:.1f}s", (50, 40),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.putText(frame, f"Frames: {len(frames_data)}", (50, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            else:
                # Not recording - show instructions
                cv2.putText(frame, "Press SPACE to record", (w//2 - 150, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            cv2.imshow('Pose Recorder', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space bar
                if not recording:
                    print("Recording started...")
                    recording = True
                    start_time = cv2.getTickCount() / cv2.getTickFrequency()
                    frames_data = []
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    record_pose_sequence(duration_seconds=10.0)