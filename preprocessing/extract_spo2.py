import vitaldb
import pandas as pd

data = vitaldb.load_case(1, ['SPO2'])
df = pd.DataFrame(data, columns=['SpO2'])

df = df.dropna()

df.to_csv("medical_iot_ids/processed/spo2.csv", index=False)
print("SpO2 extracted:", len(df))
