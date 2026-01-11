import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc
from tensorflow.keras.models import load_model

WINDOW_SIZE = 60
THRESHOLD = 0.86

# Load artifacts
scaler = joblib.load("medical_iot_ids/model/scaler.pkl")
model = load_model(
    "medical_iot_ids/model/lstm_autoencoder.h5",
    compile=False
)

# Load normalized data
df = pd.read_csv("medical_iot_ids/processed/final_5sensor_norm.csv")
data = df.values

X = []
y_true = []

# -------- NORMAL DATA --------
for i in range(300):
    X.append(data[i:i+WINDOW_SIZE])
    y_true.append(0)

# -------- ATTACK DATA (Injected) --------
for i in range(300, 600):
    window = data[i:i+WINDOW_SIZE].copy()
    window[:, 0] += 3.0     # FHR spike
    window[:, 2] -= 2.0     # SpO2 drop
    window[:, 4] += 1.5     # Temp spike
    X.append(window)
    y_true.append(1)

X = np.array(X)
y_true = np.array(y_true)

# -------- PREDICTION --------
y_scores = []
y_pred = []

for w in X:
    w = w.reshape(1, WINDOW_SIZE, 5)
    recon = model.predict(w, verbose=0)
    error = np.mean((w - recon) ** 2)
    y_scores.append(error)
    y_pred.append(1 if error > THRESHOLD else 0)

y_scores = np.array(y_scores)
y_pred = np.array(y_pred)

# -------- METRICS --------
print("\n📊 Classification Report\n")
print(classification_report(y_true, y_pred, target_names=["Normal", "Attack"]))

cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:\n", cm)

# -------- CONFUSION MATRIX PLOT --------
plt.figure()
plt.imshow(cm, cmap="Blues")
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.colorbar()
plt.xticks([0,1], ["Normal", "Attack"])
plt.yticks([0,1], ["Normal", "Attack"])
for i in range(2):
    for j in range(2):
        plt.text(j, i, cm[i,j], ha="center", va="center")
plt.show()

# -------- ROC CURVE --------
fpr, tpr, _ = roc_curve(y_true, y_scores)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}")
plt.plot([0,1], [0,1], linestyle="--")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend()
plt.show()

# -------- ERROR DISTRIBUTION --------
plt.figure()
plt.hist(y_scores[y_true==0], bins=50, alpha=0.7, label="Normal")
plt.hist(y_scores[y_true==1], bins=50, alpha=0.7, label="Attack")
plt.axvline(THRESHOLD, color="red", linestyle="--", label="Threshold")
plt.xlabel("Reconstruction Error")
plt.ylabel("Frequency")
plt.title("Reconstruction Error Distribution")
plt.legend()
plt.show()
