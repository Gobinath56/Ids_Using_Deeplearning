import vitaldb
import numpy as np

RESP_TRACKS = ['RESP_RATE', 'RR', 'ETCO2_RESP', 'RESP']

found = False

for track in RESP_TRACKS:
    print(f"\nTrying track: {track}")
    for case_id in range(1, 200):
        try:
            data = vitaldb.load_case(case_id, [track])
            if not np.all(np.isnan(data)):
                print(f"✅ Found {track} in case {case_id}")
                found = True
                break
        except:
            continue
    if found:
        break

if not found:
    print("❌ No respiration signal found in tested cases")
