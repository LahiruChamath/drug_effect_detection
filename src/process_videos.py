"""
Video Processing Script
Easy interface for processing videos and building your dataset.
"""

import os
import sys
from pose_extractor import PoseExtractor, PoseSequence, visualize_pose_sequence


def process_single_video():
    """Process a single video file"""
    print("\n" + "="*50)
    print("PROCESS SINGLE VIDEO")
    print("="*50)
    
    # Get video path
    video_path = input("\nEnter video file path: ").strip()
    
    # Remove quotes if present
    video_path = video_path.strip('"').strip("'")
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        return
    
    # Get label
    print("\nSelect label:")
    print("  1. none (baseline)")
    print("  2. stimulant")
    print("  3. depressant")
    print("  4. cannabis")
    
    label_map = {'1': 'none', '2': 'stimulant', '3': 'depressant', '4': 'cannabis'}
    label_choice = input("Enter choice (1-4): ").strip()
    label = label_map.get(label_choice, 'none')
    
    print(f"\nLabel selected: {label}")
    
    # Process
    extractor = PoseExtractor(max_duration=10.0)
    sequence = extractor.extract_from_video(video_path, label=label)
    
    # Save
    output_dir = f"data/pose_sequences/{label}"
    os.makedirs(output_dir, exist_ok=True)
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_path = os.path.join(output_dir, f"{label}_{video_name}.json")
    
    sequence.save(output_path)
    
    # Visualize?
    viz = input("\nVisualize extracted sequence? (y/n): ").lower()
    if viz == 'y':
        visualize_pose_sequence(sequence)


def process_folder():
    """Process all videos in a folder"""
    print("\n" + "="*50)
    print("PROCESS VIDEO FOLDER")
    print("="*50)
    
    # Get folder path
    folder_path = input("\nEnter folder path containing videos: ").strip()
    folder_path = folder_path.strip('"').strip("'")
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Get label
    print("\nSelect label for ALL videos in this folder:")
    print("  1. none (baseline)")
    print("  2. stimulant")
    print("  3. depressant")
    print("  4. cannabis")
    
    label_map = {'1': 'none', '2': 'stimulant', '3': 'depressant', '4': 'cannabis'}
    label_choice = input("Enter choice (1-4): ").strip()
    label = label_map.get(label_choice, 'none')
    
    print(f"\nLabel selected: {label}")
    
    # Process
    extractor = PoseExtractor(max_duration=10.0)
    output_folder = f"data/pose_sequences/{label}"
    
    saved_files = extractor.process_video_folder(
        input_folder=folder_path,
        output_folder=output_folder,
        label=label
    )
    
    print(f"\n✅ Processed {len(saved_files)} videos")


def view_dataset_stats():
    """View statistics about collected dataset"""
    print("\n" + "="*50)
    print("DATASET STATISTICS")
    print("="*50)
    
    base_path = "data/pose_sequences"
    labels = ['none', 'stimulant', 'depressant', 'cannabis']
    
    total_samples = 0
    
    for label in labels:
        label_path = os.path.join(base_path, label)
        
        if os.path.exists(label_path):
            files = [f for f in os.listdir(label_path) if f.endswith('.json')]
            count = len(files)
            total_samples += count
            
            # Get average detection rate
            if count > 0:
                detection_rates = []
                for f in files[:5]:  # Sample first 5
                    try:
                        seq = PoseSequence.load(os.path.join(label_path, f))
                        detection_rates.append(seq.detection_rate)
                    except:
                        pass
                avg_detection = sum(detection_rates) / len(detection_rates) if detection_rates else 0
                print(f"  {label}: {count} samples (avg detection: {avg_detection:.1%})")
            else:
                print(f"  {label}: {count} samples")
        else:
            print(f"  {label}: 0 samples (folder not found)")
    
    print(f"\n  Total: {total_samples} samples")


def preview_video():
    """Preview a video with pose overlay"""
    print("\n" + "="*50)
    print("PREVIEW VIDEO")
    print("="*50)
    
    video_path = input("\nEnter video file path: ").strip()
    video_path = video_path.strip('"').strip("'")
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        return
    
    extractor = PoseExtractor(max_duration=10.0)
    extractor.preview_video_with_pose(video_path)


def view_saved_sequence():
    """View a saved pose sequence"""
    print("\n" + "="*50)
    print("VIEW SAVED SEQUENCE")
    print("="*50)
    
    json_path = input("\nEnter JSON file path: ").strip()
    json_path = json_path.strip('"').strip("'")
    
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        return
    
    sequence = PoseSequence.load(json_path)
    print(f"\n{sequence.summary()}")
    
    viz = input("\nVisualize sequence? (y/n): ").lower()
    if viz == 'y':
        visualize_pose_sequence(sequence)


def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("DRUG EFFECT DETECTION - DATA COLLECTION")
        print("="*50)
        print("\nOptions:")
        print("  1. Process single video")
        print("  2. Process folder of videos")
        print("  3. Preview video with pose overlay")
        print("  4. View saved sequence")
        print("  5. View dataset statistics")
        print("  6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            process_single_video()
        elif choice == '2':
            process_folder()
        elif choice == '3':
            preview_video()
        elif choice == '4':
            view_saved_sequence()
        elif choice == '5':
            view_dataset_stats()
        elif choice == '6':
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
