# 🔧 TODO: Upgrade Ensemble Method After Retraining

> **Trigger**: After adding more data and retraining all 3 models, if accuracy is still low, implement a better ensemble strategy.

## Current Setup
- **Ensemble**: Equal-weight Soft Voting (1/3 each)
- **File**: `api/services/ml_service.py` (line ~179)
- **Models**: XGBoost (85%), SVM (83.3%), LSTM (58.3%)

## Upgrade Options (in order of priority)

### Option 1: Weighted Soft Voting (Quick Fix)
- Assign weights based on ROC AUC: XGBoost 0.45, SVM 0.40, LSTM 0.15
- ~5 line change in `ml_service.py`

### Option 2: Stacking with Meta-Learner (Best Results)
- Train a Logistic Regression on top of 3 models' probability outputs
- Requires cross-validated base model outputs for training
- Gold standard for heterogeneous ensembles

### Option 3: Confidence-Gated Ensemble
- Only include LSTM vote when its confidence > 0.7
- Otherwise fall back to XGBoost + SVM only

## Key Insight
The LSTM (58.3%) drags down the two strong classifiers. However, LSTM has 100% recall on depressants — so class-specific weighting via stacking could be very powerful.
