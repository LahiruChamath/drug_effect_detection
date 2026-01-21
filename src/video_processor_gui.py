"""
Video Processor GUI
Drag & drop or select videos to process.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pose_extractor import PoseExtractor, PoseSequence, visualize_pose_sequence


class VideoProcessorApp:
    """GUI Application for processing videos"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drug Effect Detection - Video Processor")
        self.root.geometry("700x600")
        self.root.configure(bg='#2b2b2b')
        
        # Variables
        self.selected_files = []
        self.current_label = tk.StringVar(value="none")
        self.max_duration = tk.DoubleVar(value=10.0)
        self.processing = False
        
        # Initialize extractor
        self.extractor = None
        
        # Build UI
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI widgets"""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#2b2b2b')
        title_frame.pack(fill='x', padx=20, pady=10)
        
        title = tk.Label(
            title_frame,
            text="🎬 Video Pose Extractor",
            font=('Helvetica', 24, 'bold'),
            fg='white',
            bg='#2b2b2b'
        )
        title.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Upload videos to extract anonymized pose data",
            font=('Helvetica', 12),
            fg='#888888',
            bg='#2b2b2b'
        )
        subtitle.pack()
        
        # Settings Frame
        settings_frame = tk.LabelFrame(
            self.root,
            text="Settings",
            font=('Helvetica', 12, 'bold'),
            fg='white',
            bg='#3b3b3b',
            padx=10,
            pady=10
        )
        settings_frame.pack(fill='x', padx=20, pady=10)
        
        # Label Selection
        label_frame = tk.Frame(settings_frame, bg='#3b3b3b')
        label_frame.pack(fill='x', pady=5)
        
        tk.Label(
            label_frame,
            text="Classification Label:",
            font=('Helvetica', 11),
            fg='white',
            bg='#3b3b3b'
        ).pack(side='left')
        
        labels = [
            ("None (Baseline)", "none"),
            ("Stimulant", "stimulant"),
            ("Depressant", "depressant"),
            ("Cannabis", "cannabis")
        ]
        
        for text, value in labels:
            rb = tk.Radiobutton(
                label_frame,
                text=text,
                variable=self.current_label,
                value=value,
                font=('Helvetica', 10),
                fg='white',
                bg='#3b3b3b',
                selectcolor='#4b4b4b',
                activebackground='#3b3b3b',
                activeforeground='white'
            )
            rb.pack(side='left', padx=10)
        
        # Duration Setting
        duration_frame = tk.Frame(settings_frame, bg='#3b3b3b')
        duration_frame.pack(fill='x', pady=5)
        
        tk.Label(
            duration_frame,
            text="Max Duration (seconds):",
            font=('Helvetica', 11),
            fg='white',
            bg='#3b3b3b'
        ).pack(side='left')
        
        duration_entry = tk.Entry(
            duration_frame,
            textvariable=self.max_duration,
            width=10,
            font=('Helvetica', 11)
        )
        duration_entry.pack(side='left', padx=10)
        
        # File Selection Frame
        file_frame = tk.LabelFrame(
            self.root,
            text="Video Files",
            font=('Helvetica', 12, 'bold'),
            fg='white',
            bg='#3b3b3b',
            padx=10,
            pady=10
        )
        file_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Buttons for file selection
        button_frame = tk.Frame(file_frame, bg='#3b3b3b')
        button_frame.pack(fill='x', pady=5)
        
        select_btn = tk.Button(
            button_frame,
            text="📁 Select Videos",
            command=self._select_files,
            font=('Helvetica', 11),
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=5,
            cursor='hand2'
        )
        select_btn.pack(side='left', padx=5)
        
        select_folder_btn = tk.Button(
            button_frame,
            text="📂 Select Folder",
            command=self._select_folder,
            font=('Helvetica', 11),
            bg='#2196F3',
            fg='white',
            padx=20,
            pady=5,
            cursor='hand2'
        )
        select_folder_btn.pack(side='left', padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="🗑️ Clear List",
            command=self._clear_files,
            font=('Helvetica', 11),
            bg='#f44336',
            fg='white',
            padx=20,
            pady=5,
            cursor='hand2'
        )
        clear_btn.pack(side='left', padx=5)
        
        # File List
        list_frame = tk.Frame(file_frame, bg='#3b3b3b')
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.file_listbox = tk.Listbox(
            list_frame,
            font=('Helvetica', 10),
            bg='#1e1e1e',
            fg='white',
            selectbackground='#4CAF50',
            yscrollcommand=scrollbar.set,
            height=8
        )
        self.file_listbox.pack(fill='both', expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # File count label
        self.file_count_label = tk.Label(
            file_frame,
            text="No files selected",
            font=('Helvetica', 10),
            fg='#888888',
            bg='#3b3b3b'
        )
        self.file_count_label.pack(anchor='w')
        
        # Progress Frame
        progress_frame = tk.Frame(self.root, bg='#2b2b2b')
        progress_frame.pack(fill='x', padx=20, pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to process",
            font=('Helvetica', 10),
            fg='#888888',
            bg='#2b2b2b'
        )
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill='x', pady=5)
        
        # Process Button
        self.process_btn = tk.Button(
            self.root,
            text="🚀 Process Videos",
            command=self._start_processing,
            font=('Helvetica', 14, 'bold'),
            bg='#4CAF50',
            fg='white',
            padx=30,
            pady=10,
            cursor='hand2'
        )
        self.process_btn.pack(pady=10)
        
        # Stats Button
        stats_btn = tk.Button(
            self.root,
            text="📊 View Dataset Stats",
            command=self._show_stats,
            font=('Helvetica', 11),
            bg='#9C27B0',
            fg='white',
            padx=20,
            pady=5,
            cursor='hand2'
        )
        stats_btn.pack(pady=5)
    
    def _select_files(self):
        """Open file dialog to select videos"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.webm *.MP4 *.AVI *.MOV"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=filetypes
        )
        
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    self.file_listbox.insert(tk.END, os.path.basename(f))
            
            self._update_file_count()
    
    def _select_folder(self):
        """Open folder dialog to select all videos in a folder"""
        folder = filedialog.askdirectory(title="Select Folder Containing Videos")
        
        if folder:
            video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm')
            count = 0
            
            for filename in os.listdir(folder):
                if filename.lower().endswith(video_extensions):
                    filepath = os.path.join(folder, filename)
                    if filepath not in self.selected_files:
                        self.selected_files.append(filepath)
                        self.file_listbox.insert(tk.END, filename)
                        count += 1
            
            if count == 0:
                messagebox.showinfo("No Videos", "No video files found in the selected folder.")
            
            self._update_file_count()
    
    def _clear_files(self):
        """Clear the file list"""
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self._update_file_count()
    
    def _update_file_count(self):
        """Update the file count label"""
        count = len(self.selected_files)
        if count == 0:
            self.file_count_label.config(text="No files selected")
        elif count == 1:
            self.file_count_label.config(text="1 file selected")
        else:
            self.file_count_label.config(text=f"{count} files selected")
    
    def _start_processing(self):
        """Start processing videos in a separate thread"""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select video files first.")
            return
        
        if self.processing:
            messagebox.showinfo("Processing", "Already processing. Please wait.")
            return
        
        # Start processing in background thread
        thread = threading.Thread(target=self._process_videos)
        thread.daemon = True
        thread.start()
    
    def _process_videos(self):
        """Process all selected videos"""
        self.processing = True
        self.process_btn.config(state='disabled', bg='#888888')
        
        label = self.current_label.get()
        max_duration = self.max_duration.get()
        
        # Initialize extractor
        self.extractor = PoseExtractor(max_duration=max_duration)
        
        # Output directory
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'pose_sequences', label
        )
        os.makedirs(output_dir, exist_ok=True)
        
        total = len(self.selected_files)
        success_count = 0
        error_count = 0
        
        for i, video_path in enumerate(self.selected_files):
            try:
                # Update progress
                self.progress_label.config(
                    text=f"Processing {i+1}/{total}: {os.path.basename(video_path)}"
                )
                self.progress_bar['value'] = (i / total) * 100
                self.root.update_idletasks()
                
                # Extract poses
                sequence = self.extractor.extract_from_video(video_path, label=label)
                
                # Generate output filename
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{label}_{video_name}_{timestamp}.json"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save
                sequence.save(output_path)
                success_count += 1
                
                # Update listbox to show completion
                self.file_listbox.delete(i)
                self.file_listbox.insert(i, f"✅ {os.path.basename(video_path)}")
                
            except Exception as e:
                error_count += 1
                print(f"Error processing {video_path}: {e}")
                self.file_listbox.delete(i)
                self.file_listbox.insert(i, f"❌ {os.path.basename(video_path)}")
        
        # Complete
        self.progress_bar['value'] = 100
        self.progress_label.config(
            text=f"Complete! ✅ {success_count} succeeded, ❌ {error_count} failed"
        )
        
        self.processing = False
        self.process_btn.config(state='normal', bg='#4CAF50')
        
        # Show completion message
        messagebox.showinfo(
            "Processing Complete",
            f"Processed {total} videos:\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {error_count}\n\n"
            f"Output folder:\n{output_dir}"
        )
    
    def _show_stats(self):
        """Show dataset statistics in a popup"""
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 'pose_sequences'
        )
        
        labels = ['none', 'stimulant', 'depressant', 'cannabis']
        stats_text = "📊 Dataset Statistics\n" + "="*40 + "\n\n"
        
        total = 0
        for label in labels:
            label_path = os.path.join(base_path, label)
            if os.path.exists(label_path):
                count = len([f for f in os.listdir(label_path) if f.endswith('.json')])
            else:
                count = 0
            total += count
            
            emoji = "🟢" if count >= 10 else "🟡" if count >= 5 else "🔴"
            stats_text += f"{emoji} {label.capitalize()}: {count} samples\n"
        
        stats_text += f"\n{'='*40}\n"
        stats_text += f"Total: {total} samples\n"
        
        # Recommendation
        if total < 20:
            stats_text += "\n⚠️ Need more data for training!"
        elif total < 50:
            stats_text += "\n📈 Good start! Keep collecting."
        else:
            stats_text += "\n✅ Dataset ready for training!"
        
        messagebox.showinfo("Dataset Statistics", stats_text)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    print("Starting Video Processor GUI...")
    app = VideoProcessorApp()
    app.run()


if __name__ == "__main__":
    main()