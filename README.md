# SafePose

**Privacy-first classification of drug effect categories from short video clips, using only anonymised skeletal pose data.**

SafePose investigates whether broad drug-effect categories (none / stimulant / depressant / cannabis) can be distinguished from human movement alone, without ever storing identifying video. RGB frames are discarded in memory immediately after pose extraction; only 2D skeletal coordinates leave the device.

> **Important framing.** This is an undergraduate research prototype, not a diagnostic, forensic, or screening tool. The training data consists of *acted* behaviours by consenting adult volunteers performing scripts derived from peer-reviewed pharmacological literature. **No participant was ever administered any substance.** The system has not been clinically validated and must not be used to make decisions about real individuals. See [Limitations](#limitations) below.

---

## Table of Contents

1. [What it does](#what-it-does)
2. [Why this matters](#why-this-matters)
3. [Architecture](#architecture)
4. [Results](#results)
5. [Privacy design](#privacy-design)
6. [Tech stack](#tech-stack)
7. [Installation](#installation)
8. [Usage](#usage)
9. [Repository structure](#repository-structure)
10. [Limitations](#limitations)
11. [Future work](#future-work)
12. [Citation and acknowledgements](#citation-and-acknowledgements)

---

## What it does

Given a 10-second video clip of a person standing or moving in front of a camera, SafePose returns calibrated probability scores across four categories:

- **None** — baseline / sober reference
- **Stimulant** — psychomotor agitation, hyperkinesia, fine tremor
- **Depressant** — postural sway, slowed psychomotor performance, motor incoordination
- **Cannabis** — subtle motor irregularities, mild balance disturbance, slowed reaction-like movement

The pipeline:

1. The Flutter mobile app captures a 10-second clip at 30 FPS and runs MediaPipe BlazePose **on-device** to extract 33 skeletal keypoints per frame.
2. RGB frames are discarded in memory; the audio stream is stripped at load time.
3. Only the anonymised 2D keypoint sequence (~300 frames × 33 landmarks) is transmitted as JSON to a Flask REST backend over HTTPS, authenticated with JWTs.
4. The backend runs a six-stage preprocessing pipeline (low-visibility removal, linear interpolation, skeleton centring, scale normalisation, temporal resampling) and computes 230 biomechanical features across 12 categories.
5. Three heterogeneous models (SVM-RBF, XGBoost, BiLSTM) score the sample independently; a soft-voting ensemble averages their posterior probabilities.
6. The mobile app displays the predicted class, confidence bar, and per-class distribution.

## Why this matters

Existing approaches to detecting drug-influenced behaviour each have a different fatal flaw:

| Method | Limitation |
|---|---|
| Biological testing (blood, urine) | Invasive, slow, expensive, retroactive |
| Field sobriety assessments | Subjective, training-dependent, observer bias |
| Conventional video surveillance | Retains identifying imagery — privacy-corrosive at scale |
| Wearable sensors | Require specialised hardware and user compliance |

SafePose is a feasibility study for a fifth option: **anonymised behavioural inference from commodity smartphone cameras**, where the raw imagery never persists. Whether this is *useful* is a much larger empirical question — see [Limitations](#limitations) — but the privacy architecture itself is the contribution.

## Architecture

```
┌─────────────────────────────────────────┐
│  Flutter Mobile App                     │
│  ┌──────────────────────────────────┐   │
│  │  Camera (10s @ 30fps, 1080p)     │   │
│  └──────────────────────────────────┘   │
│                  │                       │
│                  ▼                       │
│  ┌──────────────────────────────────┐   │
│  │  ML Kit / BlazePose (on-device)  │   │
│  │  → 33 landmarks × ~300 frames    │   │
│  └──────────────────────────────────┘   │
│                  │                       │
│                  ▼                       │
│       [RGB frames discarded]             │
│       [Audio stripped]                   │
│                  │                       │
│         JSON keypoints only              │
└─────────────────────┬───────────────────┘
                      │
                  HTTPS + JWT
                      │
                      ▼
┌─────────────────────────────────────────┐
│  Flask REST Backend (Python)            │
│  ┌──────────────────────────────────┐   │
│  │  6-stage preprocessing            │   │
│  │  (visibility, interpolation,      │   │
│  │   centring, normalisation,        │   │
│  │   resampling)                     │   │
│  └──────────────────────────────────┘   │
│                  │                       │
│                  ▼                       │
│  ┌──────────────────────────────────┐   │
│  │  Feature extraction               │   │
│  │  → 230 biomechanical features     │   │
│  │  (velocity, tremor, sway, entropy)│   │
│  └──────────────────────────────────┘   │
│                  │                       │
│                  ▼                       │
│  ┌──────────────────────────────────┐   │
│  │  Soft-voting ensemble             │   │
│  │  • SVM (RBF kernel)               │   │
│  │  • XGBoost                        │   │
│  │  • BiLSTM                         │   │
│  └──────────────────────────────────┘   │
│                  │                       │
│                  ▼                       │
│  ┌──────────────────────────────────┐   │
│  │  AES-256 encrypted storage        │   │
│  │  (keypoints + predictions only)   │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Where the work happens, and why:**

- **On-device (Flutter + ML Kit):** Pose extraction. This is the privacy-critical step — keeping it on-device means raw frames never leave the phone.
- **Backend (Python + Flask):** Feature engineering and inference. Centralised so models can be retrained and deployed without a mobile app update.
- **Why a backend at all?** The trained models (SVM, XGBoost, BiLSTM) and 230-feature pipeline are non-trivial to ship to a mobile runtime, and centralised inference allows iteration on the model without forcing users to update.

## Results

Evaluated on a pilot dataset of **100 clips (25 per class)** using **5-fold Stratified K-Fold cross-validation**:

| Model | Accuracy | Macro F1 | Macro ROC AUC | Log Loss |
|---|---|---|---|---|
| SVM (RBF kernel) | **75.00%** | 0.745 | 0.8981 | 0.7944 |
| XGBoost | 72.00% | 0.717 | 0.8528 | 0.8511 |
| BiLSTM | 61.00% | 0.604 | 0.8372 | 1.0214 |
| **Soft-voting ensemble** | 75.00% | 0.748 | **0.9533** | **0.6989** |

**Key findings:**

- The **classical models outperformed the BiLSTM by 11–14 percentage points** on accuracy. This is consistent with the established result that recurrent architectures underperform on small datasets — at 100 clips, there is simply not enough data to train a deep sequence model competitively.
- The **soft-voting ensemble matches SVM accuracy but produces meaningfully better-calibrated probabilities** (lowest log loss, highest ROC AUC). For an application that displays a confidence score to the user, calibration matters more than marginal accuracy gains.
- **SHAP and LIME analysis confirmed** that the most influential features (velocity statistics, wrist tremor energy, postural sway, head sway, motion entropy) correspond directly to the motor effects predicted by the pharmacological literature. This is triangulated evidence that the models are learning intended signals rather than dataset artefacts. Pearson correlation between SHAP and LIME importance rankings on the top-20 features is ~0.73.

These numbers should be read as **point estimates with wide confidence intervals**, not as precise characterisations. See [Limitations](#limitations).

## Privacy design

Privacy is not a single feature — it's a chain of decisions across the system:

| Layer | Control |
|---|---|
| Capture | Audio stream stripped before any further processing |
| Pose extraction | Runs on-device; raw RGB frames discarded in memory immediately after keypoint extraction |
| Transmission | Only 2D keypoint coordinates as JSON, over HTTPS, JWT-authenticated |
| Storage | Keypoint sequences AES-256 encrypted at rest |
| Identifiability | The skeletal representation discards face, skin, clothing, and background; residual identifiability from gait alone is acknowledged as an open problem (see Limitations) |

No claim of cryptographic novelty is made — each mechanism above is mature and standard. The contribution is the **composition** of these mechanisms in a behavioural screening pipeline.

## Tech stack

**Mobile (Flutter / Dart):**
- `camera` — frame capture
- `google_mlkit_pose_detection` — on-device BlazePose inference
- `flutter_secure_storage` — JWT storage
- `dio` — HTTP client

**Backend (Python 3.11):**
- `Flask` + `Flask-JWT-Extended` — REST API and authentication
- `mediapipe` — reference pose extraction (used during dataset preparation; mobile uses ML Kit equivalent)
- `numpy`, `scipy`, `pandas` — preprocessing and feature engineering
- `scikit-learn` — SVM, cross-validation, calibration
- `xgboost` — gradient-boosted ensemble
- `tensorflow` / `keras` — BiLSTM
- `shap`, `lime` — explainability analysis
- `cryptography` — AES-256 at-rest encryption

**Database:** SQLite (development), designed for migration to PostgreSQL.

## Installation

> **Note.** This repository is currently undeployed. The instructions below run the system locally. A hosted demo is planned — see [Future work](#future-work).

### Prerequisites

- Python 3.11+
- Flutter 3.x (for the mobile app)
- 4 GB free RAM minimum (BiLSTM training is the constraint)
- Optional: CUDA-capable GPU for faster BiLSTM training

### Backend

```bash
git clone https://github.com/LahiruChamath/drug_effect_detection.git
cd drug_effect_detection/backend

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables (see .env.example)
cp .env.example .env
# Edit .env to set JWT_SECRET_KEY and other config

# Initialise database
flask db upgrade

# Run development server
flask run --host=0.0.0.0 --port=5000
```

### Mobile app

```bash
cd ../mobile
flutter pub get

# Set the backend URL in lib/config/api_config.dart
# Default: http://10.0.2.2:5000 (Android emulator → host machine)

flutter run
```

### Pretrained models

Trained model weights are not included in the repository due to file size. To train from the included pilot dataset:

```bash
cd backend
python -m safepose.training.train_all
```

Training the full ensemble takes approximately 15 minutes on a modern laptop CPU.

## Usage

1. Launch the mobile app and create an account.
2. From the home screen, tap **Scan**.
3. Position the subject 2–3 metres from the camera with the full body in frame, in adequate indoor lighting against a plain background.
4. Tap **Record**. The app captures 10 seconds at 30 FPS and overlays the detected skeleton in real time.
5. The app extracts keypoints on-device, sends them to the backend, and displays the predicted category with confidence and per-class probability distribution.
6. Past scans are accessible via the **History** tab.

## Repository structure

```
drug_effect_detection/
├── backend/
│   ├── safepose/
│   │   ├── api/              # Flask routes, auth
│   │   ├── preprocessing/    # 6-stage pipeline
│   │   ├── features/         # 230-feature extraction
│   │   ├── models/           # SVM, XGBoost, BiLSTM, ensemble
│   │   ├── training/         # Cross-validation, hyperparameter search
│   │   └── explainability/   # SHAP, LIME
│   ├── tests/
│   └── requirements.txt
├── mobile/
│   ├── lib/
│   │   ├── screens/          # Login, Camera, Result, History, etc.
│   │   ├── services/         # Pose detection, API client, auth
│   │   └── widgets/
│   └── pubspec.yaml
└── docs/
    └── thesis.pdf
```

## Limitations

This section is deliberately detailed. Reading it is the difference between using SafePose for what it is — a feasibility study — and misusing it.

**Dataset limitations.**
- **100 clips are small.** Differences of 1–2 percentage points between models cannot be reliably attributed to true model differences rather than fold-assignment variance. Reported metrics are point estimates with wide confidence intervals.
- **Acted, not chemically induced.** The single most significant validity gap in the study. The acting scripts are derived from peer-reviewed pharmacology, but trained actors performing scripts may produce caricatured signatures rather than realistic motor patterns. Performance on genuinely drug-influenced subjects is unknown and may be substantially lower.
- **Narrow demographics.** Participants were recruited from the author's peer network and share a narrow range of body types, ages, ethnicities, and movement styles. Generalisation to demographically distinct users has not been characterised. A model trained on this dataset may have learned participant-specific rather than category-specific patterns.

**Model limitations.**
- BiLSTM almost certainly underperformed because of dataset size, not architectural unsuitability. At dataset sizes in the thousands, sequence models or transformers may overtake the classical models.
- Hyperparameter search was modest. More extensive search could improve performance, but at this sample size also risks overfitting to cross-validation scores.
- The equal-weight ensemble is a deliberately conservative choice. Weighted or stacking ensembles may perform better at scale.

**Methodological limitations.**
- 5-fold Stratified K-Fold was used rather than leave-one-out (cost) or participant-wise cross-validation (infeasible at this sample size). Participant-wise CV would give more honest generalisation estimates and is a priority for the scaled dataset.

**Scope limitations.**
- The system has not been evaluated under adverse conditions (poor lighting, occlusion, non-frontal angles, multiple subjects in frame).
- Model drift over time, adversarial robustness, and deployment reliability are not evaluated.
- No clinical validation has been attempted.

**What this system is not, and should never be used as:**
- A diagnostic or medical screening tool.
- A forensic or law-enforcement instrument.
- A reliable indicator of drug use in any individual.

It is an undergraduate feasibility study suggesting that pose-based behavioural classification is technically achievable at pilot scale with a privacy-preserving architecture. The path from this prototype to anything clinically or practically useful is long, and most of the steps on that path are listed in [Future work](#future-work).

## Future work

In rough priority order:

1. **Dataset expansion** to 200+ clips with explicit demographic diversity and participant-wise cross-validation.
2. **Weighted ensemble** with weights derived from per-class cross-validated ROC AUC.
3. **Spectral tremor features** (FFT-based wrist trajectory analysis) to capture frequency-domain signatures the current time-domain features miss.
4. **Real-time streaming inference** to remove the 10-second batch constraint.
5. **Transformer-based sequence models** at the scaled dataset size.
6. **Clinical validation** with chemically confirmed subjects under appropriate ethics approval — the only way to close the acted-vs-real validity gap.
7. **Federated learning** for fully on-device training without ever transmitting any data.
8. **Adversarial robustness** evaluation against deliberate evasion attempts.
9. **Hosted demo deployment** (Hugging Face Spaces or Render free tier) so reviewers can interact with the system without local setup.

## Citation and acknowledgements

If you reference this work, please cite the thesis:

> Chamath, J. A. L. (2026). *SafePose: Privacy-First Drug Effect Classification Through Movement Analysis*. BSc (Hons) Software Engineering thesis, University of Bedfordshire.

**Supervisor:** Mr. Chan Sri Manukalpa, University of Bedfordshire.

**Acknowledgements.** Thanks to the volunteers who contributed acted recordings under written informed consent, and to the usability testing participants whose feedback shaped the application interface.

---

**Author.** Lahiru Chamath — [GitHub](https://github.com/LahiruChamath) · [LinkedIn](https://linkedin.com/in/lahiru-chamath-3bb49624a)

**Status.** Thesis submitted, awaiting examination. Code archived; deployment in progress.

**License.** See LICENSE file in repository root.
