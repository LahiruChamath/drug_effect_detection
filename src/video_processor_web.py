"""
Video Processor - Web Interface
Works on any Mac without compatibility issues.
Open in your browser to upload and process videos.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Import pose extractor
from pose_extractor import PoseExtractor, PoseSequence

# Initialize Flask app
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pose_sequences')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v'}
MAX_DURATION = 10.0

# Create folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
for label in ['none', 'stimulant', 'depressant', 'cannabis']:
    os.makedirs(os.path.join(OUTPUT_FOLDER, label), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Initialize extractor
extractor = PoseExtractor(max_duration=MAX_DURATION)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Pose Extractor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 10px;
            color: #4ecca3;
        }
        
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        
        .card h2 {
            color: #4ecca3;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .label-options {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .label-option {
            flex: 1;
            min-width: 120px;
        }
        
        .label-option input {
            display: none;
        }
        
        .label-option label {
            display: block;
            padding: 15px;
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .label-option input:checked + label {
            background: rgba(78, 204, 163, 0.3);
            border-color: #4ecca3;
        }
        
        .label-option label:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .upload-area {
            border: 3px dashed rgba(255, 255, 255, 0.3);
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .upload-area:hover, .upload-area.dragover {
            border-color: #4ecca3;
            background: rgba(78, 204, 163, 0.1);
        }
        
        .upload-area h3 {
            font-size: 1.5rem;
            margin-bottom: 10px;
        }
        
        .upload-area p {
            color: #888;
        }
        
        #fileInput {
            display: none;
        }
        
        .file-list {
            margin-top: 20px;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .file-item .name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .file-item .status {
            margin-left: 15px;
            font-size: 0.9rem;
        }
        
        .file-item .status.pending { color: #888; }
        .file-item .status.processing { color: #f0ad4e; }
        .file-item .status.success { color: #4ecca3; }
        .file-item .status.error { color: #e74c3c; }
        
        .file-item .remove {
            margin-left: 10px;
            color: #e74c3c;
            cursor: pointer;
            font-size: 1.2rem;
        }
        
        .btn {
            display: inline-block;
            padding: 15px 40px;
            font-size: 1.1rem;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: #4ecca3;
            color: #1a1a2e;
        }
        
        .btn-primary:hover {
            background: #3db892;
            transform: translateY(-2px);
        }
        
        .btn-primary:disabled {
            background: #555;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-container {
            text-align: center;
            margin-top: 20px;
        }
        
        .progress-container {
            margin-top: 20px;
            display: none;
        }
        
        .progress-bar {
            height: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ecca3, #45b393);
            width: 0%;
            transition: width 0.3s;
        }
        
        .progress-text {
            text-align: center;
            margin-top: 10px;
            color: #888;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-card .number {
            font-size: 2rem;
            font-weight: bold;
            color: #4ecca3;
        }
        
        .stat-card .label {
            color: #888;
            margin-top: 5px;
        }
        
        .settings-row {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 15px;
        }
        
        .settings-row label {
            color: #888;
        }
        
        .settings-row input {
            padding: 8px 12px;
            border-radius: 5px;
            border: none;
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            width: 80px;
        }
        
        @media (max-width: 600px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .label-options {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 Video Pose Extractor</h1>
        <p class="subtitle">Upload videos to extract anonymized pose data for drug effect detection</p>
        
        <!-- Statistics -->
        <div class="card">
            <h2>📊 Dataset Statistics</h2>
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="number" id="stat-none">-</div>
                    <div class="label">None</div>
                </div>
                <div class="stat-card">
                    <div class="number" id="stat-stimulant">-</div>
                    <div class="label">Stimulant</div>
                </div>
                <div class="stat-card">
                    <div class="number" id="stat-depressant">-</div>
                    <div class="label">Depressant</div>
                </div>
                <div class="stat-card">
                    <div class="number" id="stat-cannabis">-</div>
                    <div class="label">Cannabis</div>
                </div>
            </div>
        </div>
        
        <!-- Settings -->
        <div class="card">
            <h2>⚙️ Settings</h2>
            
            <p style="margin-bottom: 15px; color: #888;">Select classification label:</p>
            <div class="label-options">
                <div class="label-option">
                    <input type="radio" name="label" id="label-none" value="none" checked>
                    <label for="label-none">🟢 None<br><small>Baseline</small></label>
                </div>
                <div class="label-option">
                    <input type="radio" name="label" id="label-stimulant" value="stimulant">
                    <label for="label-stimulant">⚡ Stimulant</label>
                </div>
                <div class="label-option">
                    <input type="radio" name="label" id="label-depressant" value="depressant">
                    <label for="label-depressant">😴 Depressant</label>
                </div>
                <div class="label-option">
                    <input type="radio" name="label" id="label-cannabis" value="cannabis">
                    <label for="label-cannabis">🌿 Cannabis</label>
                </div>
            </div>
            
            <div class="settings-row">
                <label>Max duration (seconds):</label>
                <input type="number" id="maxDuration" value="10" min="1" max="60">
            </div>
        </div>
        
        <!-- Upload -->
        <div class="card">
            <h2>📤 Upload Videos</h2>
            
            <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                <h3>📁 Click or Drag & Drop</h3>
                <p>Select video files (MP4, AVI, MOV, MKV, WebM)</p>
            </div>
            
            <input type="file" id="fileInput" multiple accept="video/*">
            
            <div class="file-list" id="fileList"></div>
            
            <div class="progress-container" id="progressContainer">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p class="progress-text" id="progressText">Processing...</p>
            </div>
            
            <div class="btn-container">
                <button class="btn btn-primary" id="processBtn" onclick="processVideos()" disabled>
                    🚀 Process Videos
                </button>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFiles = [];
        
        // Load stats on page load
        loadStats();
        
        // File input change
        document.getElementById('fileInput').addEventListener('change', function(e) {
            addFiles(e.target.files);
        });
        
        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            addFiles(e.dataTransfer.files);
        });
        
        function addFiles(files) {
            for (let file of files) {
                if (!selectedFiles.find(f => f.name === file.name)) {
                    selectedFiles.push(file);
                }
            }
            updateFileList();
        }
        
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFileList();
        }
        
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            const processBtn = document.getElementById('processBtn');
            
            if (selectedFiles.length === 0) {
                fileList.innerHTML = '';
                processBtn.disabled = true;
                return;
            }
            
            processBtn.disabled = false;
            
            fileList.innerHTML = selectedFiles.map((file, index) => `
                <div class="file-item" id="file-${index}">
                    <span class="name">📹 ${file.name}</span>
                    <span class="status pending" id="status-${index}">Pending</span>
                    <span class="remove" onclick="removeFile(${index})">✕</span>
                </div>
            `).join('');
        }
        
        async function processVideos() {
            if (selectedFiles.length === 0) return;
            
            const label = document.querySelector('input[name="label"]:checked').value;
            const maxDuration = document.getElementById('maxDuration').value;
            
            const processBtn = document.getElementById('processBtn');
            const progressContainer = document.getElementById('progressContainer');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            processBtn.disabled = true;
            progressContainer.style.display = 'block';
            
            let completed = 0;
            const total = selectedFiles.length;
            
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                const statusEl = document.getElementById(`status-${i}`);
                
                statusEl.textContent = 'Processing...';
                statusEl.className = 'status processing';
                
                try {
                    const formData = new FormData();
                    formData.append('video', file);
                    formData.append('label', label);
                    formData.append('max_duration', maxDuration);
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        statusEl.textContent = `✅ Done (${result.detection_rate})`;
                        statusEl.className = 'status success';
                    } else {
                        statusEl.textContent = '❌ Error';
                        statusEl.className = 'status error';
                    }
                } catch (error) {
                    statusEl.textContent = '❌ Failed';
                    statusEl.className = 'status error';
                }
                
                completed++;
                progressFill.style.width = `${(completed / total) * 100}%`;
                progressText.textContent = `Processed ${completed} of ${total} videos`;
            }
            
            progressText.textContent = `✅ Complete! Processed ${total} videos.`;
            processBtn.disabled = false;
            
            // Reload stats
            loadStats();
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/stats');
                const stats = await response.json();
                
                document.getElementById('stat-none').textContent = stats.none || 0;
                document.getElementById('stat-stimulant').textContent = stats.stimulant || 0;
                document.getElementById('stat-depressant').textContent = stats.depressant || 0;
                document.getElementById('stat-cannabis').textContent = stats.cannabis || 0;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and processing"""
    
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No video file'})
    
    file = request.files['video']
    label = request.form.get('label', 'none')
    max_duration = float(request.form.get('max_duration', 10.0))
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    try:
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"{timestamp}_{filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(temp_path)
        
        # Update extractor max duration
        extractor.max_duration = max_duration
        
        # Extract poses
        sequence = extractor.extract_from_video(temp_path, label=label)
        
        # Save pose sequence
        video_name = os.path.splitext(filename)[0]
        output_filename = f"{label}_{video_name}_{timestamp}.json"
        output_path = os.path.join(OUTPUT_FOLDER, label, output_filename)
        sequence.save(output_path)
        
        # Delete temporary video file (privacy)
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'frames': sequence.num_frames,
            'detection_rate': f"{sequence.detection_rate:.1%}",
            'duration': f"{sequence.duration:.2f}s"
        })
        
    except Exception as e:
        print(f"Error processing video: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/stats')
def get_stats():
    """Get dataset statistics"""
    stats = {}
    
    for label in ['none', 'stimulant', 'depressant', 'cannabis']:
        label_path = os.path.join(OUTPUT_FOLDER, label)
        if os.path.exists(label_path):
            count = len([f for f in os.listdir(label_path) if f.endswith('.json')])
            stats[label] = count
        else:
            stats[label] = 0
    
    return jsonify(stats)


if __name__ == '__main__':
    PORT = 8080  # Changed from 5000
    
    print("\n" + "="*50)
    print("🎬 Video Pose Extractor - Web Interface")
    print("="*50)
    print("\n📂 Output folder:", OUTPUT_FOLDER)
    print(f"\n🌐 Open your browser and go to:")
    print(f"\n   👉 http://localhost:{PORT}")
    print("\n" + "="*50)
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=PORT)
