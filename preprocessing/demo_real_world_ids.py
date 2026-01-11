import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

WINDOW_SIZE = 60
THRESHOLD = 0.86

# Load REAL normalized data
df = pd.read_csv("medical_iot_ids/processed/final_5sensor_norm.csv")
data = df.values

# 👉 Pick ONE real window (you can change the index)
start_index = 3000   # try different values if needed
window = data[start_index:start_index + WINDOW_SIZE]

# Load trained model
model = load_model(
    "medical_iot_ids/model/lstm_autoencoder.h5",
    compile=False
)

# Prepare window
window = window.reshape(1, WINDOW_SIZE, 5)

# Predict & compute error
reconstruction = model.predict(window, verbose=0)
error = np.mean((window - reconstruction) ** 2)

# Final IDS decision
print("\n🔍 REAL-WORLD IDS DEMONSTRATION\n")
print("Reconstruction Error :", round(error, 4))
print("Threshold            :", THRESHOLD)

if error > THRESHOLD:
    print("🚨 Attack classified as ATTACK? True")
else:
    print("✅ Attack classified as ATTACK? False")
