import vitaldb
import pandas as pd
import numpy as np

TRACKS = ['SPO2', 'RESP', 'TEMP']
case_id = 1

data = vitaldb.load_case(case_id, TRACKS)
print("Raw data shape:", data.shape)

df = pd.DataFrame(data, columns=['SpO2', 'RespRate', 'Temp'])

# Step 1: interpolate missing values
df = df.interpolate(method='linear', limit_direction='both')

# Step 2: forward/backward fill if still missing
df = df.fillna(method='ffill').fillna(method='bfill')

print("After interpolation shape:", df.shape)
print("Missing values:\n", df.isna().sum())

df.to_csv("medical_iot_ids/processed/spo2_rr_temp.csv", index=False)

print("VitalDB extraction done")
print(df.head())
