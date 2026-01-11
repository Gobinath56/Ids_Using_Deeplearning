import wfdb
import pandas as pd
import os

DATA_DIR = "medical_iot_ids/raw/CTU_CHB"
rows = []

for file in os.listdir(DATA_DIR):
    if file.endswith(".hea"):
        record = file.replace(".hea", "")
        rec = wfdb.rdrecord(os.path.join(DATA_DIR, record))

        fhr = rec.p_signal[:, 0]
        toco = rec.p_signal[:, 1]

        for i in range(len(fhr)):
            rows.append([fhr[i], toco[i]])

df = pd.DataFrame(rows, columns=["FHR", "TOCO"])
df.to_csv("medical_iot_ids/processed/fhr_toco_ctu.csv", index=False)

print("CTU-CHB extraction done")
