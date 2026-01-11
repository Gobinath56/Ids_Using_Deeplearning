import vitaldb
import pandas as pd
import numpy as np

CASE_ID = 5          # from: "Found TEMP in case 5"
TRACK = 'TEMP'

# Load TEMP data (numpy array)
data = vitaldb.load_case(CASE_ID, [TRACK])
print("Raw TEMP shape:", data.shape)

# Convert to DataFrame
df = pd.DataFrame(data, columns=['Temp'])

# Interpolate sparse temperature values
df['Temp'] = df['Temp'].interpolate(
    method='linear', limit_direction='both'
)

# Forward + backward fill
df['Temp'] = df['Temp'].ffill().bfill()

print("Missing after fill:", df.isna().sum())

# Save
df.to_csv("medical_iot_ids/processed/temp.csv", index=False)

print("Temp extracted:", len(df))
print(df.head())
