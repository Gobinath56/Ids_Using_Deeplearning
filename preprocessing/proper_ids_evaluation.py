import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    precision_recall_curve,
    f1_score,
    accuracy_score
)
from tensorflow.keras.models import load_model

# ===========================
# CONFIGURATION
# ===========================
WINDOW_SIZE = 60
THRESHOLD = 0.86  # You can tune this
DATASET_PATH = "medical_iot_ids/processed/final_5sensor_norm.csv"
MODEL_PATH = "medical_iot_ids/model/lstm_autoencoder.h5"
SCALER_PATH = "medical_iot_ids/model/scaler.pkl"

print("=" * 80)
print("     COMPREHENSIVE IDS EVALUATION WITH SYNTHETIC ATTACKS")
print("=" * 80)

# ===========================
# LOAD MODEL & DATA
# ===========================
print("\n[1/6] Loading model and data...")
model = load_model(MODEL_PATH, compile=False)
scaler = joblib.load(SCALER_PATH)
df_norm = pd.read_csv(DATASET_PATH)
data_norm = df_norm.values

print(f"✓ Model loaded")
print(f"✓ Dataset shape: {data_norm.shape}")
print(f"✓ Detection threshold: {THRESHOLD}")


# ===========================
# ATTACK INJECTION FUNCTIONS
# ===========================

def inject_dos_flooding(window):
    """DoS: Random noise + high variance"""
    attack = window.copy()
    noise = np.random.normal(0, 1.5, window.shape)
    attack += noise
    return attack


def inject_spoofing(window):
    """Spoofing: Out-of-range extreme values"""
    attack = window.copy()
    # Randomly select sensors to spoof
    sensors_to_spoof = np.random.choice(5, size=2, replace=False)
    for s in sensors_to_spoof:
        attack[:, s] = np.random.uniform(3, 6)  # Extreme values
    return attack


def inject_mitm(window):
    """MITM: Systematic value manipulation"""
    attack = window.copy()
    attack[:, 0] += np.random.uniform(2.0, 3.5)  # FHR spike
    attack[:, 2] -= np.random.uniform(1.5, 2.5)  # SpO2 drop
    attack[:, 4] += np.random.uniform(1.2, 2.0)  # Temp increase
    return attack


def inject_jamming(window):
    """Jamming: Zeros or constant values"""
    attack = window.copy()
    # Random portion gets jammed
    start = np.random.randint(0, WINDOW_SIZE - 20)
    jam_length = np.random.randint(10, min(30, WINDOW_SIZE - start))
    end = start + jam_length
    attack[start:end, :] = np.random.choice([-5, 0, 5], size=(jam_length, 5))
    return attack


def inject_replay(window):
    """Replay: Repeat a segment"""
    attack = window.copy()
    # Take first 20 samples and repeat them
    segment = window[:20]
    attack[20:40] = segment
    attack[40:60] = segment
    return attack


def inject_data_injection(window):
    """False data injection: Random patterns"""
    attack = window.copy()
    # Inject random periodic pattern
    for i in range(WINDOW_SIZE):
        if i % 5 == 0:
            attack[i] += np.random.uniform(2, 4, 5)
    return attack


def inject_resource_exhaustion(window):
    """Resource exhaustion: Burst patterns"""
    attack = window.copy()
    # Create burst effect - sudden spikes
    burst_points = np.random.choice(WINDOW_SIZE, size=15, replace=False)
    for bp in burst_points:
        attack[bp] += np.random.uniform(2.5, 4.0, 5)
    return attack


# ===========================
# CREATE LABELED TEST SET
# ===========================

print("\n[2/6] Creating labeled test dataset...")

# We'll create a balanced dataset:
# - 500 normal windows
# - 500 attack windows (distributed across attack types)

X_test = []
y_test = []
attack_types = []

attack_functions = {
    'DoS_Flooding': inject_dos_flooding,
    'Spoofing': inject_spoofing,
    'MITM': inject_mitm,
    'Jamming': inject_jamming,
    'Replay': inject_replay,
    'Data_Injection': inject_data_injection,
    'Resource_Exhaustion': inject_resource_exhaustion
}

# === NORMAL SAMPLES ===
print("Creating 500 normal windows...")
for i in range(500):
    # Random starting point
    start = np.random.randint(0, len(data_norm) - WINDOW_SIZE)
    window = data_norm[start:start + WINDOW_SIZE]
    X_test.append(window)
    y_test.append(0)  # 0 = Normal
    attack_types.append('Normal')

# === ATTACK SAMPLES ===
print("Creating 500 attack windows (70 of each type)...")
attacks_per_type = 70

for attack_name, attack_func in attack_functions.items():
    print(f"  Injecting {attack_name}...")
    for i in range(attacks_per_type):
        # Start with normal window
        start = np.random.randint(0, len(data_norm) - WINDOW_SIZE)
        window = data_norm[start:start + WINDOW_SIZE].copy()

        # Inject attack
        attack_window = attack_func(window)

        X_test.append(attack_window)
        y_test.append(1)  # 1 = Attack
        attack_types.append(attack_name)

X_test = np.array(X_test)
y_test = np.array(y_test)

print(f"\n✓ Test set created:")
print(f"  Total samples: {len(X_test)}")
print(f"  Normal: {np.sum(y_test == 0)}")
print(f"  Attack: {np.sum(y_test == 1)}")

# ===========================
# PREDICT ON TEST SET
# ===========================

print("\n[3/6] Running predictions...")

y_scores = []
y_pred = []

for i, window in enumerate(X_test):
    if (i + 1) % 200 == 0:
        print(f"  Processed {i + 1}/{len(X_test)} windows...")

    w = window.reshape(1, WINDOW_SIZE, 5)
    recon = model.predict(w, verbose=0)
    error = np.mean((w - recon) ** 2)

    y_scores.append(error)
    y_pred.append(1 if error > THRESHOLD else 0)

y_scores = np.array(y_scores)
y_pred = np.array(y_pred)

print("✓ Predictions complete")

# ===========================
# CALCULATE METRICS
# ===========================

print("\n[4/6] Calculating performance metrics...")

# Basic metrics
accuracy = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()

# Derived metrics
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
f1 = f1_score(y_test, y_pred)
fpr_rate = fp / (fp + tn) if (fp + tn) > 0 else 0

# ROC curve
fpr, tpr, thresholds = roc_curve(y_test, y_scores)
roc_auc = auc(fpr, tpr)

# Precision-Recall curve
precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_scores)
pr_auc = auc(recall_curve, precision_curve)

print("✓ Metrics calculated")

# ===========================
# DISPLAY RESULTS
# ===========================

print("\n" + "=" * 80)
print("                        EVALUATION RESULTS")
print("=" * 80)

print(f"\n📊 OVERALL PERFORMANCE:")
print(f"   Accuracy:        {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(f"   Precision:       {precision:.4f}")
print(f"   Recall (TPR):    {recall:.4f}")
print(f"   Specificity:     {specificity:.4f}")
print(f"   F1-Score:        {f1:.4f}")
print(f"   ROC AUC:         {roc_auc:.4f}")
print(f"   PR AUC:          {pr_auc:.4f}")

print(f"\n📈 CONFUSION MATRIX:")
print(f"   True Negatives:  {tn}")
print(f"   False Positives: {fp}")
print(f"   False Negatives: {fn}")
print(f"   True Positives:  {tp}")
print(f"   False Positive Rate: {fpr_rate:.4f}")

print("\n📋 DETAILED CLASSIFICATION REPORT:")
print(classification_report(y_test, y_pred,
                            target_names=["Normal", "Attack"],
                            digits=4))

# Per-attack type analysis
print("\n🔍 PER-ATTACK TYPE ANALYSIS:")
for attack_name in ['Normal'] + list(attack_functions.keys()):
    mask = np.array(attack_types) == attack_name
    if np.sum(mask) > 0:
        subset_true = y_test[mask]
        subset_pred = y_pred[mask]
        subset_acc = accuracy_score(subset_true, subset_pred)
        detected = np.sum(subset_pred == 1)
        total = len(subset_true)
        print(f"   {attack_name:20s}: {detected}/{total} detected ({subset_acc * 100:.1f}% accuracy)")

# ===========================
# VISUALIZATIONS
# ===========================

print("\n[5/6] Generating visualizations...")

fig = plt.figure(figsize=(16, 12))

# 1. Confusion Matrix
ax1 = plt.subplot(2, 3, 1)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
            xticklabels=['Normal', 'Attack'],
            yticklabels=['Normal', 'Attack'])
plt.title(f'Confusion Matrix\nAccuracy: {accuracy:.3f}', fontsize=12, fontweight='bold')
plt.ylabel('True Label')
plt.xlabel('Predicted Label')

# 2. ROC Curve
ax2 = plt.subplot(2, 3, 2)
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC (AUC = {roc_auc:.3f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve', fontsize=12, fontweight='bold')
plt.legend(loc="lower right")
plt.grid(alpha=0.3)

# 3. Precision-Recall Curve
ax3 = plt.subplot(2, 3, 3)
plt.plot(recall_curve, precision_curve, color='blue', lw=2, label=f'PR (AUC = {pr_auc:.3f})')
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision-Recall Curve', fontsize=12, fontweight='bold')
plt.legend(loc="lower left")
plt.grid(alpha=0.3)

# 4. Reconstruction Error Distribution
ax4 = plt.subplot(2, 3, 4)
plt.hist(y_scores[y_test == 0], bins=50, alpha=0.7, label='Normal', color='green', edgecolor='black')
plt.hist(y_scores[y_test == 1], bins=50, alpha=0.7, label='Attack', color='red', edgecolor='black')
plt.axvline(THRESHOLD, color='black', linestyle='--', linewidth=2, label=f'Threshold={THRESHOLD}')
plt.xlabel('Reconstruction Error')
plt.ylabel('Frequency')
plt.title('Error Distribution', fontsize=12, fontweight='bold')
plt.legend()
plt.grid(alpha=0.3)

# 5. Per-Attack Type Detection Rate
ax5 = plt.subplot(2, 3, 5)
attack_names = list(attack_functions.keys())
detection_rates = []
for attack_name in attack_names:
    mask = np.array(attack_types) == attack_name
    detected = np.sum(y_pred[mask] == 1)
    total = np.sum(mask)
    detection_rates.append(detected / total * 100 if total > 0 else 0)

plt.barh(attack_names, detection_rates, color='steelblue', edgecolor='black')
plt.xlabel('Detection Rate (%)')
plt.title('Attack Detection Rate by Type', fontsize=12, fontweight='bold')
plt.xlim([0, 105])
for i, v in enumerate(detection_rates):
    plt.text(v + 2, i, f'{v:.1f}%', va='center')
plt.grid(axis='x', alpha=0.3)

# 6. Metrics Comparison
ax6 = plt.subplot(2, 3, 6)
metrics_names = ['Accuracy', 'Precision', 'Recall', 'Specificity', 'F1-Score']
metrics_values = [accuracy, precision, recall, specificity, f1]
colors_bars = ['#2ecc71' if v >= 0.9 else '#f39c12' if v >= 0.8 else '#e74c3c' for v in metrics_values]
plt.bar(metrics_names, metrics_values, color=colors_bars, edgecolor='black')
plt.ylim([0, 1.1])
plt.ylabel('Score')
plt.title('Performance Metrics Summary', fontsize=12, fontweight='bold')
plt.xticks(rotation=45, ha='right')
for i, v in enumerate(metrics_values):
    plt.text(i, v + 0.03, f'{v:.3f}', ha='center', fontweight='bold')
plt.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('ids_evaluation_results.png', dpi=300, bbox_inches='tight')
print("✓ Visualization saved: ids_evaluation_results.png")

plt.show()

print("\n[6/6] Evaluation complete!")
print("=" * 80)

# ===========================
# THRESHOLD OPTIMIZATION
# ===========================

print("\n🔧 THRESHOLD OPTIMIZATION:")
print("\nTrying different thresholds...\n")

best_f1 = 0
best_threshold = THRESHOLD

for thresh in np.arange(0.1, 2.0, 0.1):
    y_pred_temp = (y_scores > thresh).astype(int)
    f1_temp = f1_score(y_test, y_pred_temp)
    acc_temp = accuracy_score(y_test, y_pred_temp)

    if f1_temp > best_f1:
        best_f1 = f1_temp
        best_threshold = thresh

    print(f"Threshold={thresh:.2f} → Accuracy={acc_temp:.4f}, F1={f1_temp:.4f}")

print(f"\n✨ Best threshold: {best_threshold:.2f} (F1={best_f1:.4f})")
print(f"   Current threshold: {THRESHOLD:.2f}")

if best_threshold != THRESHOLD:
    print(f"\n💡 Suggestion: Update THRESHOLD to {best_threshold:.2f} for better performance")

print("\n" + "=" * 80)
print("                    EVALUATION COMPLETE! ✓")
print("=" * 80)