import numpy as np
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.optimizers import Adam

# Paths
DATA_PATH = "medical_iot_ids/processed/X_windows.npy"
MODEL_DIR = "medical_iot_ids/model"
MODEL_PATH = os.path.join(MODEL_DIR, "lstm_autoencoder.h5")

os.makedirs(MODEL_DIR, exist_ok=True)

# Load data
X = np.load(DATA_PATH)
print("Loaded data shape:", X.shape)

TIMESTEPS = X.shape[1]   # 60
FEATURES = X.shape[2]    # 5

# Build LSTM Autoencoder
model = Sequential([
    LSTM(64, activation="tanh", input_shape=(TIMESTEPS, FEATURES)),
    RepeatVector(TIMESTEPS),
    LSTM(64, activation="tanh", return_sequences=True),
    TimeDistributed(Dense(FEATURES))
])

model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss="mse"
)

model.summary()

# Train
history = model.fit(
    X, X,
    epochs=30,
    batch_size=32,
    validation_split=0.1,
    shuffle=True
)

# Save model
model.save(MODEL_PATH)
print("✅ LSTM Autoencoder trained and saved")
