import vitaldb
import pandas as pd
import numpy as np

case_id = 1
TRACK = 'RR'

data = vitaldb.load_case(case_id, [TRACK])
print("Raw RR shape:", data.shape)

df = pd.DataFrame(data, columns=['RespRate'])

# Interpolate sparse RR values
df['RespRate'] = df['RespRate'].interpolate(
    method='linear', limit_direction='both'
)

# Forward/backward fill remaining gaps
df['RespRate'] = df['RespRate'].ffill().bfill()

print("Missing after fill:", df.isna().sum())

df.to_csv("medical_iot_ids/processed/resp.csv", index=False)
print("Resp extracted:", len(df))
print(df.head())
