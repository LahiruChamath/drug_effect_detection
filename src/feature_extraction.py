import numpy as np


# ==========================================================
# BASIC MOTION DERIVATIVES
# ==========================================================

def compute_velocity(sequence):
    return np.diff(sequence, axis=0)


def compute_acceleration(velocity):
    return np.diff(velocity, axis=0)


def compute_jerk(acceleration):
    return np.diff(acceleration, axis=0)


# ==========================================================
# STATISTICAL FEATURE EXTRACTOR (global)
# ==========================================================

def stats_features(data):
    """
    Extract statistical descriptors from motion data.
    """
    features = []

    # Flatten joints but preserve time
    reshaped = data.reshape(data.shape[0], -1)

    features.append(np.mean(reshaped))
    features.append(np.std(reshaped))
    features.append(np.max(reshaped))
    features.append(np.min(reshaped))
    features.append(np.median(reshaped))

    return features


# ==========================================================
# PER-JOINT VELOCITY STATISTICS  (NEW — v2)
# ==========================================================

def per_joint_velocity_stats(velocity):
    """
    For each of the 33 joints compute: mean speed + std speed.
    velocity shape: (T-1, 33, 3)
    Output: 33*2 = 66 features
    """
    speed = np.linalg.norm(velocity, axis=2)  # (T-1, 33)
    mean_speed = np.mean(speed, axis=0)        # (33,)
    std_speed  = np.std(speed, axis=0)         # (33,)
    return np.concatenate([mean_speed, std_speed]).tolist()


# ==========================================================
# PER-JOINT ACCELERATION MAGNITUDE (NEW — v2)
# ==========================================================

def per_joint_accel_magnitude(acceleration):
    """
    Mean acceleration magnitude per joint.
    acceleration shape: (T-2, 33, 3)
    Output: 33 features
    """
    mag = np.linalg.norm(acceleration, axis=2)  # (T-2, 33)
    return np.mean(mag, axis=0).tolist()          # (33,)


# ==========================================================
# JOINT ENERGY FEATURES
# ==========================================================

def joint_energy(data):
    """
    Energy = sum of squared movement
    """
    energy = np.sum(data ** 2, axis=0)
    return energy.flatten().tolist()


# ==========================================================
# POSTURAL SWAY (HIP MOVEMENT)
# ==========================================================

def postural_sway(sequence):
    left_hip = sequence[:, 23, :]
    right_hip = sequence[:, 24, :]
    hip_center = (left_hip + right_hip) / 2

    sway_x = np.std(hip_center[:, 0])
    sway_y = np.std(hip_center[:, 1])

    return [sway_x, sway_y]


# ==========================================================
# HEAD SWAY (NOSE TRAJECTORY)  (NEW — v2)
# ==========================================================

def head_sway(sequence):
    """
    Std of nose (landmark 0) x/y movement — captures head tremor / nodding.
    Output: 2 features
    """
    nose = sequence[:, 0, :]
    return [np.std(nose[:, 0]), np.std(nose[:, 1])]


# ==========================================================
# WRIST TREMOR ENERGY
# ==========================================================

def wrist_tremor_energy(velocity):
    left_wrist = velocity[:, 15, :]
    right_wrist = velocity[:, 16, :]

    tremor_left = np.sum(left_wrist ** 2)
    tremor_right = np.sum(right_wrist ** 2)

    return [tremor_left, tremor_right]


# ==========================================================
# SYMMETRY FEATURES
# ==========================================================

def symmetry_features(sequence):
    """
    Compare left vs right limbs
    """
    pairs = [
        (11, 12),  # shoulders
        (13, 14),  # elbows
        (15, 16),  # wrists
        (25, 26),  # knees
        (27, 28),  # ankles
    ]

    features = []

    for left, right in pairs:
        diff = sequence[:, left, :] - sequence[:, right, :]
        features.append(np.mean(np.abs(diff)))

    return features


# ==========================================================
# ENTROPY OF MOTION
# ==========================================================

def motion_entropy(sequence, bins=20):
    reshaped = sequence.reshape(sequence.shape[0], -1)
    hist, _ = np.histogram(reshaped, bins=bins, density=True)
    hist = hist + 1e-8
    entropy = -np.sum(hist * np.log(hist))
    return [entropy]


# ==========================================================
# MASTER FEATURE FUNCTION
# ==========================================================

def extract_features(sequence):
    """
    Input:
        (200, 33, 3)

    Output:
        Feature vector (~230 features, up from 129)

    Changelog:
        v2 — Added per_joint_velocity_stats (+66),
              per_joint_accel_magnitude (+33), head_sway (+2)
              Total: 129 + 66 + 33 + 2 = 230 features
    """

    features = []

    # ---- Raw position stats ----
    features += stats_features(sequence)

    # ---- Velocity ----
    velocity = compute_velocity(sequence)
    features += stats_features(velocity)
    features += joint_energy(velocity)

    # ---- Per-joint velocity mean & std (NEW) ----
    features += per_joint_velocity_stats(velocity)

    # ---- Acceleration ----
    acceleration = compute_acceleration(velocity)
    features += stats_features(acceleration)

    # ---- Per-joint acceleration magnitude (NEW) ----
    features += per_joint_accel_magnitude(acceleration)

    # ---- Jerk ----
    jerk = compute_jerk(acceleration)
    features += stats_features(jerk)

    # ---- Postural sway ----
    features += postural_sway(sequence)

    # ---- Head sway (NEW) ----
    features += head_sway(sequence)

    # ---- Tremor ----
    features += wrist_tremor_energy(velocity)

    # ---- Symmetry ----
    features += symmetry_features(sequence)

    # ---- Entropy ----
    features += motion_entropy(sequence)

    return np.array(features)