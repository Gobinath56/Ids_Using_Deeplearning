import numpy as np
import pandas as pd

WINDOW_SIZE = 60

INPUT = "medical_iot_ids/processed/final_5sensor_norm.csv"
OUTPUT = "medical_iot_ids/processed/X_windows.npy"

df = pd.read_csv(INPUT)
data = df.values

windows = []
for i in range(len(data) - WINDOW_SIZE):
    windows.append(data[i:i + WINDOW_SIZE])

X = np.array(windows)

np.save(OUTPUT, X)

print("✅ Sliding windows created")
print("Shape:", X.shape)
