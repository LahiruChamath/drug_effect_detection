import numpy as np
from src.pose_extractor import PoseSequence


# ==========================================================
# STEP 1 — LOAD SEQUENCE
# ==========================================================

def load_sequence(filepath):
    """
    Load PoseSequence JSON and convert to numpy array.

    Returns:
        ndarray of shape (frames, 33, 4)
    """
    seq = PoseSequence.load(filepath)
    return seq.to_numpy()


# ==========================================================
# STEP 2 — REMOVE LOW VISIBILITY
# ==========================================================

def clean_visibility(raw_data, visibility_threshold=0.5):
    """
    Replace low-visibility joints with NaN.
    Remove visibility channel.

    Input:
        (frames, 33, 4)

    Output:
        (frames, 33, 3)
    """
    coords = raw_data[:, :, :3]
    visibility = raw_data[:, :, 3]

    coords[visibility < visibility_threshold] = np.nan
    return coords


# ==========================================================
# STEP 3 — INTERPOLATE MISSING VALUES
# ==========================================================

def interpolate_sequence(data):
    """
    Interpolate NaN values across time.
    Ensures no missing values remain.
    """
    frames, joints, dims = data.shape

    for j in range(joints):
        for d in range(dims):
            series = data[:, j, d]

            if np.isnan(series).any():
                valid = ~np.isnan(series)

                if valid.sum() > 1:
                    data[:, j, d] = np.interp(
                        np.arange(frames),
                        np.where(valid)[0],
                        series[valid]
                    )
                else:
                    data[:, j, d] = 0

    return data


# ==========================================================
# STEP 4 — CENTER SKELETON (HIP MIDPOINT)
# ==========================================================

def center_skeleton(data):
    """
    Remove global body translation using hip midpoint.
    """
    left_hip = data[:, 23, :]
    right_hip = data[:, 24, :]

    hip_center = (left_hip + right_hip) / 2
    data = data - hip_center[:, np.newaxis, :]

    return data


# ==========================================================
# STEP 5 — SCALE NORMALIZATION (SHOULDER WIDTH)
# ==========================================================

def scale_normalize(data):
    """
    Normalize body size using shoulder distance.
    """
    left_shoulder = data[:, 11, :]
    right_shoulder = data[:, 12, :]

    shoulder_dist = np.linalg.norm(left_shoulder - right_shoulder, axis=1)

    # Avoid division by zero
    shoulder_dist[shoulder_dist == 0] = 1e-6

    data = data / shoulder_dist[:, np.newaxis, np.newaxis]

    return data


# ==========================================================
# STEP 6 — RESAMPLE TO FIXED LENGTH
# ==========================================================

def resample_sequence(data, target_frames=200):
    """
    Resample sequence to fixed number of frames.
    """
    original_frames, joints, dims = data.shape

    new_data = np.zeros((target_frames, joints, dims))

    old_indices = np.linspace(0, original_frames - 1, original_frames)
    new_indices = np.linspace(0, original_frames - 1, target_frames)

    for j in range(joints):
        for d in range(dims):
            new_data[:, j, d] = np.interp(
                new_indices,
                old_indices,
                data[:, j, d]
            )

    return new_data


# ==========================================================
# MASTER PIPELINE
# ==========================================================

def preprocess_sequence(filepath, target_frames=200):
    """
    Full preprocessing pipeline.

    Output:
        (target_frames, 33, 3)
    """

    raw = load_sequence(filepath)

    coords = clean_visibility(raw)
    coords = interpolate_sequence(coords)
    coords = center_skeleton(coords)
    coords = scale_normalize(coords)
    coords = resample_sequence(coords, target_frames)

    # Final safety check
    if np.isnan(coords).any():
        raise ValueError("NaNs detected after preprocessing.")

    return coords