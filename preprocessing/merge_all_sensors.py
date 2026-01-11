import pandas as pd

# Load all signals
fhr_toco = pd.read_csv("medical_iot_ids/processed/fhr_toco_ctu.csv")
spo2 = pd.read_csv("medical_iot_ids/processed/spo2.csv")
resp = pd.read_csv("medical_iot_ids/processed/resp.csv")
temp = pd.read_csv("medical_iot_ids/processed/temp.csv")

# Ensure same length (important)
min_len = min(len(fhr_toco), len(spo2), len(resp), len(temp))

df = pd.concat([
    fhr_toco.iloc[:min_len].reset_index(drop=True),
    spo2.iloc[:min_len].reset_index(drop=True),
    resp.iloc[:min_len].reset_index(drop=True),
    temp.iloc[:min_len].reset_index(drop=True)
], axis=1)

df.columns = ['FHR', 'TOCO', 'SpO2', 'RespRate', 'Temp']

df.to_csv("medical_iot_ids/processed/final_5sensor.csv", index=False)

print("✅ Final 5-sensor dataset created")
print(df.head())
print("Shape:", df.shape)
