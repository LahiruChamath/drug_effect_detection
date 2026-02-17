"""
Pose Extractor Module - Video Upload Version
Extracts anonymized pose keypoints from uploaded videos.
Processes only the first 10 seconds of each video.
Privacy-preserving: only skeletal data is saved, no images.
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from tqdm import tqdm


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class PoseFrame:
    """Single frame of pose data"""
    frame_number: int
    timestamp: float
    landmarks: Optional[np.ndarray]  # Shape: (33, 4) - x, y, z, visibility
    
    def to_dict(self) -> dict:
        return {
            'frame_number': self.frame_number,
            'timestamp': self.timestamp,
            'landmarks': self.landmarks.tolist() if self.landmarks is not None else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PoseFrame':
        return cls(
            frame_number=data.get('frame_number, 0'),
            timestamp=data['timestamp'],
            landmarks=np.array(data['landmarks']) if data['landmarks'] else None
        )


@dataclass
class PoseSequence:
    """Complete pose sequence with metadata"""
    frames: List[PoseFrame]
    fps: float
    duration: float
    original_video: str
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def num_frames(self) -> int:
        return len(self.frames)
    
    @property
    def detection_rate(self) -> float:
        """Percentage of frames with successful detection"""
        if not self.frames:
            return 0.0
        detected = sum(1 for f in self.frames if f.landmarks is not None)
        return detected / len(self.frames)
    
    @property
    def detected_frames(self) -> int:
        """Number of frames with successful detection"""
        return sum(1 for f in self.frames if f.landmarks is not None)
    
    def to_numpy(self) -> np.ndarray:
        """
        Convert to numpy array for processing.
        Returns shape: (num_frames, 33, 4)
        Missing detections filled with NaN.
        """
        result = []
        for frame in self.frames:
            if frame.landmarks is not None:
                result.append(frame.landmarks)
            else:
                result.append(np.full((33, 4), np.nan))
        return np.array(result)
    
    def get_landmark_trajectory(self, landmark_idx: int) -> np.ndarray:
        """
        Get trajectory of a specific landmark over time.
        Returns shape: (num_frames, 4) - x, y, z, visibility
        """
        data = self.to_numpy()
        return data[:, landmark_idx, :]
    
    def save(self, filepath: str):
        """Save to JSON file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = {
            'fps': self.fps,
            'duration': self.duration,
            'original_video': self.original_video,
            'label': self.label,
            'metadata': self.metadata,
            'num_frames': self.num_frames,
            'detected_frames': self.detected_frames,
            'detection_rate': self.detection_rate,
            'extracted_at': datetime.now().isoformat(),
            'frames': [f.to_dict() for f in self.frames]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f)
        
        print(f"✅ Saved: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'PoseSequence':
        """Load from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(
            frames=[PoseFrame.from_dict(f) for f in data['frames']],
            fps=data['fps'],
            duration=data['duration'],
            original_video=data.get('original_video', 'unknown'),
            label=data.get('label'),
            metadata=data.get('metadata', {})
        )
    
    def summary(self) -> str:
        """Get a summary string"""
        return (
            f"PoseSequence Summary:\n"
            f"  Source: {self.original_video}\n"
            f"  Label: {self.label}\n"
            f"  Duration: {self.duration:.2f}s\n"
            f"  FPS: {self.fps:.1f}\n"
            f"  Total Frames: {self.num_frames}\n"
            f"  Detected Frames: {self.detected_frames}\n"
            f"  Detection Rate: {self.detection_rate:.1%}"
        )


# ============================================
# LANDMARK REFERENCE
# ============================================

LANDMARK_NAMES = {
    0: 'nose',
    1: 'left_eye_inner', 2: 'left_eye', 3: 'left_eye_outer',
    4: 'right_eye_inner', 5: 'right_eye', 6: 'right_eye_outer',
    7: 'left_ear', 8: 'right_ear',
    9: 'mouth_left', 10: 'mouth_right',
    11: 'left_shoulder', 12: 'right_shoulder',
    13: 'left_elbow', 14: 'right_elbow',
    15: 'left_wrist', 16: 'right_wrist',
    17: 'left_pinky', 18: 'right_pinky',
    19: 'left_index', 20: 'right_index',
    21: 'left_thumb', 22: 'right_thumb',
    23: 'left_hip', 24: 'right_hip',
    25: 'left_knee', 26: 'right_knee',
    27: 'left_ankle', 28: 'right_ankle',
    29: 'left_heel', 30: 'right_heel',
    31: 'left_foot_index', 32: 'right_foot_index'
}

# Key landmarks for analysis
KEY_LANDMARKS = {
    'nose': 0,
    'left_shoulder': 11, 'right_shoulder': 12,
    'left_elbow': 13, 'right_elbow': 14,
    'left_wrist': 15, 'right_wrist': 16,
    'left_hip': 23, 'right_hip': 24,
    'left_knee': 25, 'right_knee': 26,
    'left_ankle': 27, 'right_ankle': 28,
}


# ============================================
# POSE EXTRACTOR
# ============================================

class PoseExtractor:
    """
    Main class for extracting pose data from uploaded videos.
    Processes only the first N seconds of each video.
    """
    
    def __init__(self,
                 model_complexity: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 max_duration: float = 10.0):
        """
        Initialize the PoseExtractor.
        
        Args:
            model_complexity: 0 (fast), 1 (balanced), 2 (accurate)
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            max_duration: Maximum seconds to extract (default 10s)
        """
        self.model_complexity = model_complexity
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.max_duration = max_duration
        
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        print(f"PoseExtractor initialized:")
        print(f"  Model complexity: {model_complexity}")
        print(f"  Max duration: {max_duration}s")
    
    def _create_pose_detector(self):
        """Create a new pose detector instance"""
        return self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.model_complexity,
            smooth_landmarks=True,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
    
    def _landmarks_to_array(self, landmarks) -> np.ndarray:
        """Convert MediaPipe landmarks to numpy array"""
        return np.array([
            [lm.x, lm.y, lm.z, lm.visibility]
            for lm in landmarks.landmark
        ])
    
    def get_video_info(self, video_path: str) -> dict:
        """Get information about a video file"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        
        info = {
            'path': video_path,
            'filename': os.path.basename(video_path),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }
        info['duration'] = info['total_frames'] / info['fps'] if info['fps'] > 0 else 0
        
        cap.release()
        return info
    
    def extract_from_video(self, 
                           video_path: str,
                           label: Optional[str] = None,
                           show_progress: bool = True) -> PoseSequence:
        """
        Extract pose sequence from a video file.
        Only processes the first max_duration seconds.
        
        Args:
            video_path: Path to the video file
            label: Optional label ('none', 'stimulant', 'depressant', 'cannabis')
            show_progress: Whether to show progress bar
            
        Returns:
            PoseSequence containing extracted pose data
        """
        # Get video info
        video_info = self.get_video_info(video_path)
        
        print(f"\n{'='*50}")
        print(f"Processing: {video_info['filename']}")
        print(f"{'='*50}")
        print(f"  Resolution: {video_info['width']}x{video_info['height']}")
        print(f"  FPS: {video_info['fps']:.1f}")
        print(f"  Total duration: {video_info['duration']:.2f}s")
        
        # Calculate frames to process
        fps = video_info['fps']
        max_frames = int(self.max_duration * fps)
        frames_to_process = min(max_frames, video_info['total_frames'])
        actual_duration = frames_to_process / fps
        
        print(f"  Processing: first {actual_duration:.2f}s ({frames_to_process} frames)")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        # Create progress bar
        if show_progress:
            pbar = tqdm(total=frames_to_process, desc="Extracting poses")
        
        with self._create_pose_detector() as pose:
            frame_idx = 0
            
            while cap.isOpened() and frame_idx < frames_to_process:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Calculate timestamp
                timestamp = frame_idx / fps
                
                # Convert to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process pose
                results = pose.process(rgb_frame)
                
                # Extract landmarks
                if results.pose_landmarks:
                    landmarks = self._landmarks_to_array(results.pose_landmarks)
                else:
                    landmarks = None
                
                # Store frame data
                frames.append(PoseFrame(
                    frame_number=frame_idx,
                    timestamp=timestamp,
                    landmarks=landmarks
                ))
                
                frame_idx += 1
                
                if show_progress:
                    pbar.update(1)
        
        if show_progress:
            pbar.close()
        
        cap.release()
        
        # Create sequence
        sequence = PoseSequence(
            frames=frames,
            fps=fps,
            duration=actual_duration,
            original_video=video_info['filename'],
            label=label,
            metadata={
                'video_info': video_info,
                'max_duration_setting': self.max_duration,
                'model_complexity': self.model_complexity
            }
        )
        
        # Print summary
        print(f"\n{sequence.summary()}")
        
        return sequence
    
    def process_video_folder(self,
                             input_folder: str,
                             output_folder: str,
                             label: str,
                             video_extensions: tuple = ('.mp4', '.avi', '.mov', '.mkv', '.webm')) -> List[str]:
        """
        Process all videos in a folder.
        
        Args:
            input_folder: Folder containing videos
            output_folder: Folder to save pose sequences
            label: Label for all videos in this folder
            video_extensions: Valid video file extensions
            
        Returns:
            List of saved file paths
        """
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Input folder not found: {input_folder}")
        
        # Find video files
        video_files = []
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(video_extensions):
                video_files.append(os.path.join(input_folder, filename))
        
        if not video_files:
            print(f"No video files found in {input_folder}")
            return []
        
        print(f"\nFound {len(video_files)} videos to process")
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        saved_files = []
        
        for i, video_path in enumerate(video_files):
            print(f"\n[{i+1}/{len(video_files)}] Processing...")
            
            try:
                # Extract pose sequence
                sequence = self.extract_from_video(video_path, label=label)
                
                # Generate output filename
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{label}_{video_name}_{timestamp}.json"
                output_path = os.path.join(output_folder, output_filename)
                
                # Save
                sequence.save(output_path)
                saved_files.append(output_path)
                
            except Exception as e:
                print(f"❌ Error processing {video_path}: {e}")
        
        print(f"\n{'='*50}")
        print(f"Batch processing complete!")
        print(f"  Processed: {len(saved_files)}/{len(video_files)} videos")
        print(f"  Output folder: {output_folder}")
        print(f"{'='*50}")
        
        return saved_files
    
    def preview_video_with_pose(self, video_path: str, playback_speed: float = 1.0):
        """
        Preview a video with pose overlay.
        Useful for checking video quality before processing.
        
        Args:
            video_path: Path to video file
            playback_speed: Playback speed multiplier
        """
        video_info = self.get_video_info(video_path)
        
        print(f"Previewing: {video_info['filename']}")
        print(f"Press 'q' to quit, SPACE to pause/resume")
        
        cap = cv2.VideoCapture(video_path)
        delay = int(1000 / (video_info['fps'] * playback_speed))
        paused = False
        
        with self._create_pose_detector() as pose:
            while cap.isOpened():
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Get current position
                    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                    current_time = current_frame / video_info['fps']
                    
                    # Process pose
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = pose.process(rgb_frame)
                    
                    # Draw pose
                    if results.pose_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            results.pose_landmarks,
                            self.mp_pose.POSE_CONNECTIONS
                        )
                        status = "Pose Detected"
                        color = (0, 255, 0)
                    else:
                        status = "No Pose"
                        color = (0, 0, 255)
                    
                    # Draw info
                    cv2.putText(frame, f"Time: {current_time:.2f}s / {video_info['duration']:.2f}s",
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(frame, status,
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                    
                    # Show 10s boundary
                    if current_time <= self.max_duration:
                        cv2.putText(frame, f"[Within {self.max_duration}s limit]",
                                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    else:
                        cv2.putText(frame, f"[Beyond {self.max_duration}s limit - will be cut]",
                                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                
                cv2.imshow('Video Preview', frame)
                
                key = cv2.waitKey(delay if not paused else 0) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord(' '):
                    paused = not paused
        
        cap.release()
        cv2.destroyAllWindows()


# ============================================
# VISUALIZATION
# ============================================

def visualize_pose_sequence(sequence: PoseSequence, delay: int = 33):
    """
    Visualize a saved pose sequence as skeleton animation.
    Shows only anonymized pose data - no original video.
    
    Args:
        sequence: PoseSequence to visualize
        delay: Delay between frames in ms
    """
    print(f"Visualizing: {sequence.original_video}")
    print(f"Press 'q' to quit, SPACE to pause/resume")
    
    paused = False
    frame_idx = 0
    
    # Define skeleton connections
    connections = [
        (11, 12),  # shoulders
        (11, 13), (13, 15),  # left arm
        (12, 14), (14, 16),  # right arm
        (11, 23), (12, 24),  # torso sides
        (23, 24),  # hips
        (23, 25), (25, 27),  # left leg
        (24, 26), (26, 28),  # right leg
    ]
    
    while frame_idx < len(sequence.frames):
        # Create blank canvas
        canvas = np.zeros((480, 640, 3), dtype=np.uint8)
        
        frame = sequence.frames[frame_idx]
        
        if frame.landmarks is not None:
            # Draw connections
            for start_idx, end_idx in connections:
                start = frame.landmarks[start_idx]
                end = frame.landmarks[end_idx]
                
                if start[3] > 0.5 and end[3] > 0.5:
                    pt1 = (int(start[0] * 640), int(start[1] * 480))
                    pt2 = (int(end[0] * 640), int(end[1] * 480))
                    cv2.line(canvas, pt1, pt2, (0, 255, 0), 2)
            
            # Draw landmarks
            for i, lm in enumerate(frame.landmarks):
                if lm[3] > 0.5:
                    pt = (int(lm[0] * 640), int(lm[1] * 480))
                    cv2.circle(canvas, pt, 5, (0, 0, 255), -1)
        
        # Draw info
        cv2.putText(canvas, f"Frame: {frame_idx}/{len(sequence.frames)}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(canvas, f"Time: {frame.timestamp:.2f}s",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if sequence.label:
            cv2.putText(canvas, f"Label: {sequence.label}",
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        if paused:
            cv2.putText(canvas, "PAUSED", (270, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        cv2.imshow('Pose Sequence Viewer', canvas)
        
        key = cv2.waitKey(delay if not paused else 0) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused
        
        if not paused:
            frame_idx += 1
    
    cv2.destroyAllWindows()


# ============================================
# MAIN / TESTING
# ============================================

if __name__ == "__main__":
    print("="*50)
    print("POSE EXTRACTOR - Video Upload Version")
    print("="*50)
    
    extractor = PoseExtractor(max_duration=10.0)
    
    # Check for test video
    test_videos = [
        "test_video.mp4",
        "data/raw_videos/test.mp4",
        "sample.mp4"
    ]
    
    test_video = None
    for path in test_videos:
        if os.path.exists(path):
            test_video = path
            break
    
    if test_video:
        print(f"\nFound test video: {test_video}")
        
        # Preview
        preview = input("Preview video with pose overlay? (y/n): ").lower()
        if preview == 'y':
            extractor.preview_video_with_pose(test_video)
        
        # Extract
        extract = input("Extract pose sequence? (y/n): ").lower()
        if extract == 'y':
            sequence = extractor.extract_from_video(test_video, label='none')
            
            # Save
            output_path = "data/pose_sequences/none/test_extraction.json"
            sequence.save(output_path)
            
            # Visualize
            visualize = input("Visualize extracted sequence? (y/n): ").lower()
            if visualize == 'y':
                visualize_pose_sequence(sequence)
    else:
        print("\nNo test video found.")
        print("To test, place a video file named 'test_video.mp4' in the project folder.")
        print("\nUsage example:")
        print("  extractor = PoseExtractor(max_duration=10.0)")
        print("  sequence = extractor.extract_from_video('path/to/video.mp4', label='none')")
        print("  sequence.save('output.json')")