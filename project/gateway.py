import socket
import json
import time
from datetime import datetime
from config import HOST_IP, TARGET_IP, GATEWAY_PORT, COLLECTOR_PORT

# Gateway Configuration
GATEWAY_LISTEN_PORT = GATEWAY_PORT
COLLECTOR_FORWARD_PORT = COLLECTOR_PORT
COLLECTOR_IP = "127.0.0.1"

# Security Settings
VALID_SENSOR_IDS = ['S1', 'S2', 'S3', 'S4', 'S5']
MAX_PACKETS_PER_SECOND = 50
TIMESTAMP_TOLERANCE = 10

# IDS TESTING MODE - Set to True to allow all attacks through
IDS_TESTING_MODE = True  # ← NEW: Toggle this for testing


class NetworkGateway:
    def __init__(self):
        self.sensor_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sensor_socket.bind((HOST_IP, GATEWAY_LISTEN_PORT))
        self.collector_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet_tracker = {}

        print("=" * 70)
        print("          NETWORK GATEWAY - Medical Sensor Network")
        print("=" * 70)
        print(f"Listening on: {HOST_IP}:{GATEWAY_LISTEN_PORT}")
        print(f"  (Accessible from network as: {TARGET_IP}:{GATEWAY_LISTEN_PORT})")
        print(f"Forwarding to collector: {COLLECTOR_IP}:{COLLECTOR_FORWARD_PORT}")
        print(f"\nSecurity Features:")
        print(f"  • Sensor Authentication (Valid IDs: {', '.join(VALID_SENSOR_IDS)})")
        print(f"  • Rate Limiting (Max {MAX_PACKETS_PER_SECOND} packets/sec per sensor)")
        print(f"  • Timestamp Validation (±{TIMESTAMP_TOLERANCE}s tolerance)")

        if IDS_TESTING_MODE:
            print(f"\n🔓 IDS TESTING MODE: ENABLED")
            print(f"     All attacks will pass through for IDS detection!")
        else:
            print(f"\n⚠️  NOTE: Gateway is configured with LENIENT security for testing")
            print(f"     Most attacks will pass through for IDS to detect!")

        print("=" * 70)
        print("\n✅ Gateway is running...\n")

    def is_valid_sensor_id(self, sensor_id):
        # IDS TESTING MODE: Allow all sensor IDs
        if IDS_TESTING_MODE:
            return True

        # Normal mode: Only allow registered sensors
        return sensor_id in VALID_SENSOR_IDS

    def check_rate_limit(self, sensor_id):
        # IDS TESTING MODE: Disable rate limiting
        if IDS_TESTING_MODE:
            return True

        current_time = time.time()
        if sensor_id not in self.packet_tracker:
            self.packet_tracker[sensor_id] = []
        self.packet_tracker[sensor_id] = [
            t for t in self.packet_tracker[sensor_id] if current_time - t < 1.0
        ]
        if len(self.packet_tracker[sensor_id]) >= MAX_PACKETS_PER_SECOND:
            return False
        self.packet_tracker[sensor_id].append(current_time)
        return True

    def validate_timestamp(self, packet_timestamp):
        # IDS TESTING MODE: Skip timestamp validation
        if IDS_TESTING_MODE:
            return True

        try:
            packet_time = datetime.strptime(packet_timestamp, '%Y-%m-%d %H:%M:%S.%f')
            current_time = datetime.now()
            time_diff = abs((current_time - packet_time).total_seconds())
            return time_diff <= TIMESTAMP_TOLERANCE
        except:
            return False

    def validate_packet(self, packet):
        sensor_id = packet.get('sensor_id', '')

        if not self.is_valid_sensor_id(sensor_id):
            print(f"⚠️  BLOCKED: Unknown sensor ID '{sensor_id}'")
            return False, "Invalid Sensor ID"

        if not self.check_rate_limit(sensor_id):
            print(f"⚠️  BLOCKED: Rate limit exceeded for {sensor_id}")
            return False, "Rate Limit Exceeded"

        if not self.validate_timestamp(packet.get('timestamp', '')):
            print(f"⚠️  BLOCKED: Invalid/old timestamp from {sensor_id}")
            return False, "Invalid Timestamp"

        return True, "Valid"

    def forward_to_collector(self, packet):
        try:
            self.collector_socket.sendto(
                json.dumps(packet).encode(),
                (COLLECTOR_IP, COLLECTOR_FORWARD_PORT)
            )
        except Exception as e:
            print(f"❌ Error forwarding packet: {e}")

    def run(self):
        try:
            while True:
                data, addr = self.sensor_socket.recvfrom(1024)
                packet = json.loads(data.decode())
                sensor_id = packet.get('sensor_id', 'UNKNOWN')
                sensor_type = packet.get('sensor_type', 'UNKNOWN')
                value = packet.get('value', 0)
                is_attack = packet.get('is_attack', 0)

                is_valid, reason = self.validate_packet(packet)

                if is_valid:
                    self.forward_to_collector(packet)

                    # Show different symbols for attacks vs normal
                    if is_attack == 1:
                        attack_type = packet.get('attack_type', 'Unknown')
                        print(
                            f"🔴 [{packet['timestamp']}] FORWARDED (ATTACK): {sensor_id} | {sensor_type}: {value} | Type: {attack_type}")
                    else:
                        print(f"✅ [{packet['timestamp']}] FORWARDED: {sensor_id} | {sensor_type}: {value}")
                else:
                    print(
                        f"🚫 [{packet.get('timestamp', 'NO_TIME')}] BLOCKED ({reason}): {sensor_id} | {sensor_type}: {value}")

        except KeyboardInterrupt:
            print("\n\n🛑 Gateway shutting down...")
            self.sensor_socket.close()
            self.collector_socket.close()


if __name__ == "__main__":
    gateway = NetworkGateway()
    gateway.run()