import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Ensure model directory exists
os.makedirs("medical_iot_ids/model", exist_ok=True)

df = pd.read_csv("medical_iot_ids/processed/final_5sensor.csv")

scaler = StandardScaler()
X = scaler.fit_transform(df)

joblib.dump(scaler, "medical_iot_ids/model/scaler.pkl")

pd.DataFrame(X, columns=df.columns)\
  .to_csv("medical_iot_ids/processed/final_5sensor_norm.csv", index=False)

print("✅ Normalization done")
