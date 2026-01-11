import numpy as np
from tensorflow.keras.models import load_model

X = np.load("medical_iot_ids/processed/X_windows.npy")

# 🔥 IMPORTANT FIX HERE
model = load_model(
    "medical_iot_ids/model/lstm_autoencoder.h5",
    compile=False
)

X_pred = model.predict(X, verbose=0)

errors = np.mean((X - X_pred) ** 2, axis=(1, 2))

print("Reconstruction error stats:")
print("Min :", errors.min())
print("Mean:", errors.mean())
print("Max :", errors.max())

print("\nSuggested thresholds:")
print("95% percentile:", np.percentile(errors, 95))
print("99% percentile:", np.percentile(errors, 99))
