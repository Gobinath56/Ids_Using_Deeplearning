import numpy as np
import pandas as pd
import joblib
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

# ---- NORMAL TEST ----
print("\n🟢 Testing NORMAL data")
normal_window = data[0:WINDOW_SIZE]
normal_window = normal_window.reshape(1, WINDOW_SIZE, 5)

recon = model.predict(normal_window, verbose=0)
normal_error = np.mean((normal_window - recon) ** 2)

print("Normal reconstruction error:", normal_error)
print("Normal classified as ATTACK?", normal_error > THRESHOLD)

# ---- ATTACK SIMULATION ----
print("\n🔴 Testing ANOMALOUS data")

attack_window = normal_window.copy()

# Simulate MITM / spoofing style attack
attack_window[:, :, 0] += 3.0     # FHR spike
attack_window[:, :, 2] -= 2.0     # SpO2 drop
attack_window[:, :, 4] += 1.5     # Temp spike

recon_attack = model.predict(attack_window, verbose=0)
attack_error = np.mean((attack_window - recon_attack) ** 2)

print("Attack reconstruction error:", attack_error)
print("Attack classified as ATTACK?", attack_error > THRESHOLD)
