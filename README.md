# Drug Effect Detection using Pose Estimation

A privacy-preserving system that uses MediaPipe pose estimation to detect behavioral patterns associated with different drug effect categories from video data.

## 🎯 Project Overview

This project explores whether anonymized movement data (pose keypoints) can distinguish between:
- **None** - Baseline behavior
- **Stimulant** - Increased activity, tremors
- **Depressant** - Slowed movement, sway
- **Cannabis** - Altered timing patterns

**Privacy-First**: Only skeletal pose data is extracted and stored. No identifying visual information is retained.

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/drug_effect_detection.git
cd drug_effect_detection

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# or: venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
