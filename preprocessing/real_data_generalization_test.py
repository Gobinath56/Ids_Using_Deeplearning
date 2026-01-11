import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model

WINDOW_SIZE = 60

# Load normalized real data
df = pd.read_csv("medical_iot_ids/processed/final_5sensor_norm.csv")
data = df.values

# Create windows
windows = []
for i in range(len(data) - WINDOW_SIZE):
    windows.append(data[i:i+WINDOW_SIZE])

X = np.array(windows)

# Train/Test split (70/30)
split_idx = int(0.7 * len(X))
X_train = X[:split_idx]
X_test = X[split_idx:]

print("Train windows:", X_train.shape)
print("Test windows :", X_test.shape)

# Load trained model
model = load_model(
    "medical_iot_ids/model/lstm_autoencoder.h5",
    compile=False
)

# Reconstruction errors
def reconstruction_error(X):
    X_pred = model.predict(X, verbose=0)
    return np.mean((X - X_pred) ** 2, axis=(1,2))

train_errors = reconstruction_error(X_train)
test_errors = reconstruction_error(X_test)

# Stats
print("\nTrain Error Stats")
print("Min:", train_errors.min())
print("Mean:", train_errors.mean())
print("Max:", train_errors.max())

print("\nTest Error Stats")
print("Min:", test_errors.min())
print("Mean:", test_errors.mean())
print("Max:", test_errors.max())

# Plot distribution
plt.figure(figsize=(8,5))
plt.hist(train_errors, bins=50, alpha=0.7, label="Train (Real)")
plt.hist(test_errors, bins=50, alpha=0.7, label="Test (Real)")
plt.xlabel("Reconstruction Error")
plt.ylabel("Frequency")
plt.title("Real Data Generalization Test (No Attacks)")
plt.legend()
plt.show()
