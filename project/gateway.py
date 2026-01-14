import socket
import json
import time
from datetime import datetime
from config import HOST_IP, TARGET_IP, GATEWAY_PORT, COLLECTOR_PORT

# ======================================================
# CONFIG
# ======================================================
GATEWAY_LISTEN_PORT = GATEWAY_PORT
COLLECTOR_FORWARD_PORT = COLLECTOR_PORT
COLLECTOR_IP = "127.0.0.1"

VALID_SENSOR_IDS = ['S1', 'S2', 'S3', 'S4', 'S5']
MAX_PACKETS_PER_SECOND = 50
TIMESTAMP_TOLERANCE = 10

IDS_TESTING_MODE = True   # KEEP TRUE FOR IDS EXPERIMENTS

# ======================================================
# GATEWAY
# ======================================================
class NetworkGateway:
    def __init__(self):
        self.sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sensor_socket.bind((HOST_IP, GATEWAY_LISTEN_PORT))

        self.collector_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet_tracker = {}

        print("=" * 70)
        print("NETWORK GATEWAY — Medical IoT")
        print("=" * 70)
        print(f"Listening on {HOST_IP}:{GATEWAY_LISTEN_PORT}")
        print(f"Forwarding to {COLLECTOR_IP}:{COLLECTOR_FORWARD_PORT}")
        print("IDS TESTING MODE:", IDS_TESTING_MODE)
        print("=" * 70)
        print("✅ Gateway running...\n")

    # ---------------- VALIDATION ----------------
    def is_valid_sensor_id(self, sensor_id):
        return True if IDS_TESTING_MODE else sensor_id in VALID_SENSOR_IDS

    def check_rate_limit(self, sensor_id):
        if IDS_TESTING_MODE:
            return True

        now = time.time()
        self.packet_tracker.setdefault(sensor_id, [])
        self.packet_tracker[sensor_id] = [
            t for t in self.packet_tracker[sensor_id] if now - t < 1
        ]

        if len(self.packet_tracker[sensor_id]) >= MAX_PACKETS_PER_SECOND:
            return False

        self.packet_tracker[sensor_id].append(now)
        return True

    def validate_timestamp(self, ts):
        if IDS_TESTING_MODE:
            return True
        try:
            pkt_time = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S.%f')
            return abs((datetime.now() - pkt_time).total_seconds()) <= TIMESTAMP_TOLERANCE
        except:
            return False

    def validate_packet(self, packet):
        sid = packet.get("sensor_id", "")
        if not self.is_valid_sensor_id(sid):
            return False, "Invalid Sensor ID"
        if not self.check_rate_limit(sid):
            return False, "Rate Limit"
        if not self.validate_timestamp(packet.get("timestamp", "")):
            return False, "Bad Timestamp"
        return True, "OK"

    # ---------------- FORWARD ----------------
    def forward_to_collector(self, packet):
        self.collector_socket.sendto(
            json.dumps(packet).encode(),
            (COLLECTOR_IP, COLLECTOR_FORWARD_PORT)
        )

    # ---------------- MAIN LOOP ----------------
    def run(self):
        while True:
            try:
                # 🔴 CRITICAL FIX: buffer size increased
                data, addr = self.sensor_socket.recvfrom(4096)

                try:
                    packet = json.loads(data.decode())
                except Exception as e:
                    print("⚠️ Dropped malformed packet:", e)
                    continue

                is_valid, reason = self.validate_packet(packet)

                if is_valid:
                    self.forward_to_collector(packet)
                    print(
                        f"➡️ FORWARDED [{packet.get('timestamp','--')}] "
                        f"{packet.get('sensor_id','?')} | "
                        f"{packet.get('sensor_type','?')} : {packet.get('value','?')}"
                    )
                else:
                    print(
                        f"🚫 BLOCKED [{reason}] "
                        f"{packet.get('sensor_id','?')} | "
                        f"{packet.get('sensor_type','?')} : {packet.get('value','?')}"
                    )

            except KeyboardInterrupt:
                print("\n🛑 Gateway stopped by user")
                break
            except Exception as e:
                # 🔥 THIS PREVENTS TERMINATION
                print("❌ Gateway error (ignored):", e)
                time.sleep(0.2)

        self.sensor_socket.close()
        self.collector_socket.close()

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    gateway = NetworkGateway()
    gateway.run()
