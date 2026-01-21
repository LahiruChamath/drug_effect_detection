"""
Data Collection Interface for Drug Effect Detection Project
Handles the complete workflow for collecting and labeling pose data.
"""

import os
import json
from datetime import datetime
from typing import Optional
from pose_extractor import PoseExtractor, PoseSequence


class DataCollector:
    """
    Manages data collection sessions with proper labeling.
    """
    
    VALID_LABELS = ['none', 'stimulant', 'depressant', 'cannabis']
    
    def __init__(self, 
                 data_dir: str = "data/pose_sequences",
                 duration: float = 10.0):
        """
        Initialize the data collector.
        
        Args:
            data_dir: Directory to save pose sequences
            duration: Default recording duration in seconds
        """
        self.data_dir = data_dir
        self.duration = duration
        self.extractor = PoseExtractor(model_complexity=1)
        
        # Create directories for each label
        for label in self.VALID_LABELS:
            os.makedirs(os.path.join(data_dir, label), exist_ok=True)
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.samples_collected = {label: 0 for label in self.VALID_LABELS}
        
        print(f"DataCollector initialized")
        print(f"  Session ID: {self.session_id}")
        print(f"  Data directory: {data_dir}")
        print(f"  Recording duration: {duration}s")
    
    def collect_sample(self, 
                       label: str,
                       participant_id: Optional[str] = None,
                       notes: Optional[str] = None) -> str:
        """
        Collect a single labeled sample.
        
        Args:
            label: One of 'none', 'stimulant', 'depressant', 'cannabis'
            participant_id: Anonymous participant identifier
            notes: Any additional notes about the sample
            
        Returns:
            Path to saved file
        """
        if label not in self.VALID_LABELS:
            raise ValueError(f"Invalid label: {label}. Must be one of {self.VALID_LABELS}")
        
        print("\n" + "="*60)
        print(f"COLLECTING SAMPLE - Label: {label.upper()}")
        print("="*60)
        print("\nInstructions for acted simulation:")
        print(self._get_instructions(label))
        print("\n" + "-"*60)
        input("Press ENTER when ready to start recording...")
        
        # Record pose sequence
        sequence = self.extractor.extract_realtime(
            duration=self.duration,
            show_preview=True,
            countdown=3
        )
        
        # Add metadata
        sequence.label = label
        sequence.metadata.update({
            'session_id': self.session_id,
            'participant_id': participant_id,
            'notes': notes,
            'sample_number': self.samples_collected[label] + 1
        })
        
        # Generate filename and save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{label}_{timestamp}_{self.samples_collected[label]:03d}.json"
        filepath = os.path.join(self.data_dir, label, filename)
        
        sequence.save(filepath)
        
        self.samples_collected[label] += 1
        
        print(f"\n✓ Sample saved: {filepath}")
        print(f"  Detection rate: {sequence.detection_rate:.1%}")
        print(f"  Total {label} samples this session: {self.samples_collected[label]}")
        
        return filepath
    
    def _get_instructions(self, label: str) -> str:
        """Get acting instructions for each condition"""
        instructions = {
            'none': """
    BASELINE (No Effect):
    - Stand or sit naturally
    - Move normally as you would in everyday life
    - You can shift weight, look around, gesture naturally
    - Keep movements relaxed and natural
            """,
            
            'stimulant': """
    SIMULATED STIMULANT EFFECT:
    (Based on literature: increased activity, possible tremors, jerky movements)
    - Move more quickly than usual
    - Show slight restlessness (shifting weight, fidgeting)
    - Optional: simulate slight hand tremors
    - Movements may be quicker but less smooth
    - You might touch face, adjust clothing more
    
    IMPORTANT: This is an ACTED simulation for research purposes.
            """,
            
            'depressant': """
    SIMULATED DEPRESSANT EFFECT:
    (Based on literature: slowed movement, increased sway, reduced activity)
    - Move more slowly than usual
    - Show slight swaying when standing
    - Movements are slower to initiate
    - May appear drowsy (slower head movements)
    - Reduced overall activity level
    
    IMPORTANT: This is an ACTED simulation for research purposes.
            """,
            
            'cannabis': """
    SIMULATED CANNABIS EFFECT:
    (Based on literature: altered timing, fine motor changes)
    - Movements may have slightly irregular timing
    - Possible slower reaction to internal cues
    - May show subtle coordination differences
    - Movement patterns might be less predictable
    
    IMPORTANT: This is an ACTED simulation for research purposes.
            """
        }
        return instructions.get(label, "No specific instructions.")
    
    def run_collection_session(self, 
                               samples_per_class: int = 5,
                               participant_id: Optional[str] = None):
        """
        Run a full collection session.
        
        Args:
            samples_per_class: Number of samples to collect for each class
            participant_id: Anonymous participant identifier
        """
        print("\n" + "="*60)
        print("DATA COLLECTION SESSION")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print(f"Samples per class: {samples_per_class}")
        print(f"Total samples to collect: {samples_per_class * len(self.VALID_LABELS)}")
        print("="*60)
        
        # Randomize order to reduce bias
        import random
        collection_order = self.VALID_LABELS * samples_per_class
        random.shuffle(collection_order)
        
        for i, label in enumerate(collection_order):
            print(f"\n[{i+1}/{len(collection_order)}] Next sample: {label.upper()}")
            
            continue_collecting = input("Collect this sample? (y/n/skip): ").lower()
            
            if continue_collecting == 'n':
                print("Session ended by user.")
                break
            elif continue_collecting == 'skip':
                print("Skipping this sample.")
                continue
            
            try:
                self.collect_sample(label, participant_id=participant_id)
            except Exception as e:
                print(f"Error collecting sample: {e}")
                retry = input("Retry? (y/n): ").lower()
                if retry == 'y':
                    self.collect_sample(label, participant_id=participant_id)
        
        self._print_session_summary()
    
    def _print_session_summary(self):
        """Print summary of collection session"""
        print("\n" + "="*60)
        print("SESSION SUMMARY")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print("\nSamples collected:")
        
        total = 0
        for label, count in self.samples_collected.items():
            print(f"  {label}: {count}")
            total += count
        
        print(f"\nTotal: {total} samples")
        print("="*60)
    
    def get_dataset_stats(self) -> dict:
        """Get statistics about the collected dataset"""
        stats = {}
        
        for label in self.VALID_LABELS:
            label_dir = os.path.join(self.data_dir, label)
            files = [f for f in os.listdir(label_dir) if f.endswith('.json')]
            
            detection_rates = []
            durations = []
            
            for filename in files:
                filepath = os.path.join(label_dir, filename)
                try:
                    seq = PoseSequence.load(filepath)
                    detection_rates.append(seq.detection_rate)
                    durations.append(seq.duration)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
            
            stats[label] = {
                'count': len(files),
                'avg_detection_rate': sum(detection_rates) / len(detection_rates) if detection_rates else 0,
                'avg_duration': sum(durations) / len(durations) if durations else 0
            }
        
        return stats


if __name__ == "__main__":
    collector = DataCollector(
        data_dir="data/pose_sequences",
        duration=10.0
    )
    
    # Example: Collect 3 samples per class
    collector.run_collection_session(
        samples_per_class=3,
        participant_id="P001"
    )