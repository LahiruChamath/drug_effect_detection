"""
Data Viewer - See what's in your dataset
"""

import os
import json
from datetime import datetime

def view_dataset():
    base_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pose_sequences')
    labels = ['none', 'stimulant', 'depressant', 'cannabis']
    
    print("\n" + "="*60)
    print("📊 DATASET OVERVIEW")
    print("="*60)
    
    total_files = 0
    all_files = []
    
    for label in labels:
        folder = os.path.join(base_path, label)
        
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith('.json')]
            count = len(files)
            total_files += count
            
            # Status emoji
            if count >= 20:
                emoji = "✅"
            elif count >= 10:
                emoji = "🟡"
            elif count > 0:
                emoji = "🟠"
            else:
                emoji = "❌"
            
            print(f"\n{emoji} {label.upper()}: {count} samples")
            
            # Show file details
            for filename in files[:3]:  # Show first 3
                filepath = os.path.join(folder, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    detection = data.get('detection_rate', 0)
                    frames = data.get('num_frames', 0)
                    duration = data.get('duration', 0)
                    
                    print(f"   📄 {filename[:40]}...")
                    print(f"      └─ {frames} frames, {duration:.1f}s, {detection:.1%} detected")
                    
                    all_files.append({
                        'label': label,
                        'filename': filename,
                        'path': filepath,
                        'frames': frames,
                        'duration': duration,
                        'detection_rate': detection
                    })
                except Exception as e:
                    print(f"   ⚠️  Error reading {filename}: {e}")
            
            if count > 3:
                print(f"   ... and {count - 3} more files")
        else:
            print(f"\n❌ {label.upper()}: Folder not found")
    
    print("\n" + "="*60)
    print(f"📈 TOTAL: {total_files} samples")
    print("="*60)
    
    # Recommendations
    print("\n�� RECOMMENDATIONS:")
    if total_files == 0:
        print("   → Upload some videos to get started!")
        print("   → Go to http://localhost:8080")
    elif total_files < 40:
        print("   → Need more data for good model training")
        print("   → Aim for at least 20 samples per class")
    else:
        print("   → Good dataset size! Ready for feature extraction.")
    
    return all_files


def view_single_file(filepath):
    """View details of a single JSON file"""
    
    print(f"\n📄 Viewing: {os.path.basename(filepath)}")
    print("="*60)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    print(f"Label: {data.get('label', 'N/A')}")
    print(f"Original Video: {data.get('original_video', 'N/A')}")
    print(f"Duration: {data.get('duration', 0):.2f} seconds")
    print(f"FPS: {data.get('fps', 0):.1f}")
    print(f"Total Frames: {data.get('num_frames', 0)}")
    print(f"Detected Frames: {data.get('detected_frames', 0)}")
    print(f"Detection Rate: {data.get('detection_rate', 0):.1%}")
    
    if 'metadata' in data:
        print(f"\nMetadata:")
        for key, value in data['metadata'].items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    # Show sample frame data
    if 'frames' in data and len(data['frames']) > 0:
        print(f"\nSample Frame Data (Frame 0):")
        frame = data['frames'][0]
        print(f"  Timestamp: {frame.get('timestamp', 0):.3f}s")
        if frame.get('landmarks'):
            print(f"  Landmarks: {len(frame['landmarks'])} points detected")
            print(f"  First landmark (nose): {frame['landmarks'][0][:3]}")
        else:
            print(f"  Landmarks: None detected")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # View specific file
        view_single_file(sys.argv[1])
    else:
        # View dataset overview
        view_dataset()
