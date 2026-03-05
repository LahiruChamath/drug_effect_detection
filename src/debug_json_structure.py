# debug_json_structure.py
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR if 'src' not in SCRIPT_DIR else os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "pose_sequences")

CLASSES = ["none", "stimulant", "depressant", "cannabis"]

print("=" * 60)
print("DETAILED JSON STRUCTURE ANALYSIS")
print("=" * 60)

for label in CLASSES[:1]:  # Just check 'none' for now
    folder = os.path.join(DATA_PATH, label)
    files = [f for f in os.listdir(folder) if f.endswith('.json')]
    
    if not files:
        continue
    
    filepath = os.path.join(folder, files[0])
    
    print(f"\n{'='*60}")
    print(f"ANALYZING: {label.upper()} - {files[0]}")
    print(f"{'='*60}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Top-level metadata
    print(f"\n--- TOP LEVEL METADATA ---")
    for key in ['fps', 'duration', 'num_frames', 'detected_frames', 'detection_rate', 'label']:
        if key in data:
            print(f"{key}: {data[key]}")
    
    # Frames analysis
    if 'frames' in data:
        frames = data['frames']
        print(f"\n--- FRAMES ---")
        print(f"Type: {type(frames)}")
        print(f"Number of frames: {len(frames) if isinstance(frames, list) else 'N/A'}")
        
        if isinstance(frames, list) and len(frames) > 0:
            print(f"\n--- FIRST FRAME ---")
            frame1 = frames[0]
            print(f"Type: {type(frame1)}")
            
            if isinstance(frame1, dict):
                print(f"Keys: {list(frame1.keys())}")
                
                # Check for pose_landmarks
                if 'pose_landmarks' in frame1:
                    pl = frame1['pose_landmarks']
                    print(f"\n--- POSE LANDMARKS ---")
                    print(f"Type: {type(pl)}")
                    
                    if pl is not None and isinstance(pl, list):
                        print(f"Number of landmarks: {len(pl)}")
                        
                        if len(pl) > 0:
                            print(f"\n--- FIRST LANDMARK ---")
                            print(f"Type: {type(pl[0])}")
                            print(f"Content: {pl[0]}")
                            
                            if isinstance(pl[0], dict):
                                print(f"Keys: {list(pl[0].keys())}")
                    elif pl is None:
                        print("⚠️ pose_landmarks is None")
                    else:
                        print(f"⚠️ pose_landmarks is not a list: {type(pl)}")
                
                # Print full frame (limited)
                print(f"\n--- FULL FIRST FRAME (first 1000 chars) ---")
                print(str(frame1)[:1000])
            
            # Check a few more frames
            print(f"\n--- FRAME SUMMARY (first 5 frames) ---")
            for i in range(min(5, len(frames))):
                f = frames[i]
                if isinstance(f, dict):
                    has_pl = 'pose_landmarks' in f
                    pl_len = len(f['pose_landmarks']) if has_pl and f['pose_landmarks'] else 0
                    print(f"Frame {i}: has_pose_landmarks={has_pl}, landmarks_count={pl_len}")
    
    break  # Only check first class

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)