import vitaldb
import numpy as np

TEMP_TRACKS = ['TEMP', 'TEMP_CORE', 'TEMP_SKIN']

found = False

for track in TEMP_TRACKS:
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
    print("❌ No temperature signal found")
