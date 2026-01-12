import socket
import time
import random
import json
from datetime import datetime
from config import TARGET_IP, GATEWAY_PORT, SENSOR_RANGES

"""
REALISTIC IoT ATTACKS FOR MEDICAL SENSOR NETWORKS
(Without Attack Labels - IDS Must Detect)

Attack packets now look like normal sensor traffic.
Only the IDS model at the collector can detect anomalies.

This simulates real-world scenarios where attackers:
- Don't announce "I'm attacking!"
- Try to blend in with normal traffic
- Use subtle or obvious anomalies

The LSTM Autoencoder IDS must detect these patterns.
"""


class IoTAttackInjector:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def create_packet(self, sensor_id, sensor_type, value):
        """
        Create packet that looks like normal sensor traffic
        NO attack labels - IDS must detect anomalies
        """
        packet = {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'value': value,
            'is_attack': 0,  # Always 0 - sensors don't know they're compromised
            'attack_type': '-'  # No label - IDS must figure it out
        }
        return packet

    def send_packet(self, packet):
        """Send packet to gateway"""
        self.sock.sendto(json.dumps(packet).encode(), (TARGET_IP, GATEWAY_PORT))

    # === ATTACK 1: DoS (Denial of Service) - Flooding ===
    def dos_flooding(self, duration=15):
        """
        Real attack: Overwhelm network with excessive packets
        IDS should detect: Unusual packet rate and random noise patterns
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 1: DoS (Denial of Service) - FLOODING")
        print("=" * 70)
        print("Simulating: Network flooding with noisy data")
        print("IDS should detect: High frequency + random value patterns")
        print(f"Duration: {duration}s | Rate: 50 packets/second")
        print("-" * 70)

        sensor_configs = [
            ('S1', 'FHR'),
            ('S2', 'TOCO'),
            ('S3', 'SpO2'),
            ('S4', 'RespRate'),
            ('S5', 'Temp')
        ]

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            # Flood with noisy, erratic values
            sensor_id, sensor_type = random.choice(sensor_configs)
            min_val, max_val = SENSOR_RANGES[sensor_type]

            # Add significant noise to create anomalous patterns
            center = (min_val + max_val) / 2
            noise = random.uniform(-50, 50)  # Large noise
            value = round(center + noise, 2)

            packet = self.create_packet(sensor_id, sensor_type, value)
            self.send_packet(packet)
            count += 1

            if count % 50 == 0:
                print(f"  Sent {count} flooding packets... (IDS analyzing)")

            time.sleep(0.02)  # 50 packets/sec

        print(f"✓ Attack complete: {count} packets sent")
        print("→ Check collector for IDS detections!")

    # === ATTACK 2: Spoofing Attack - Fake Sensor with Out-of-Range Values ===
    def spoofing_attack(self, duration=15):
        """
        Real attack: Impersonate sensor with extreme values
        IDS should detect: Out-of-range values and unusual patterns
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 2: SPOOFING ATTACK - Extreme Values")
        print("=" * 70)
        print("Simulating: Attacker sending out-of-range sensor values")
        print("IDS should detect: Values far outside normal distribution")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_configs = [
            ('S1', 'FHR'),
            ('S2', 'TOCO'),
            ('S3', 'SpO2'),
            ('S4', 'RespRate'),
            ('S5', 'Temp')
        ]

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            sensor_id, sensor_type = random.choice(sensor_configs)
            min_val, max_val = SENSOR_RANGES[sensor_type]

            # Send EXTREME out-of-range values
            if random.random() < 0.5:
                value = round(max_val * 1.5, 2)  # 50% above max
            else:
                value = round(min_val * 0.5, 2)  # 50% below min

            packet = self.create_packet(sensor_id, sensor_type, value)
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] {sensor_type}: {value} (EXTREME)")
            count += 1
            time.sleep(1)

        print(f"✓ Attack complete: {count} spoofed packets sent")
        print("→ IDS should flag these as ATTACKS!")

    # === ATTACK 3: MITM - Data Manipulation ===
    def mitm_data_manipulation(self, duration=15):
        """
        Real attack: Subtle manipulation of critical sensor values
        IDS should detect: Unusual temporal patterns and value shifts
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 3: MITM (Man-in-the-Middle) - Data Manipulation")
        print("=" * 70)
        print("Simulating: Subtle manipulation of FHR, SpO2, Temp")
        print("IDS should detect: Abnormal value patterns over time")
        print(f"Duration: {duration}s")
        print("-" * 70)

        # Target critical sensors
        critical_sensors = [
            ('S1', 'FHR'),
            ('S3', 'SpO2'),
            ('S5', 'Temp')
        ]

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            sensor_id, sensor_type = random.choice(critical_sensors)
            min_val, max_val = SENSOR_RANGES[sensor_type]
            center = (min_val + max_val) / 2

            # Manipulate values - shifted but somewhat plausible
            if sensor_type == 'FHR':
                value = round(random.uniform(180, 200), 2)  # High but not impossible
            elif sensor_type == 'SpO2':
                value = round(random.uniform(88, 93), 2)  # Low oxygen
            else:  # Temp
                value = round(random.uniform(38.5, 39.5), 2)  # Fever range

            packet = self.create_packet(sensor_id, sensor_type, value)
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] {sensor_type}: {value} (manipulated)")
            count += 1
            time.sleep(0.8)

        print(f"✓ Attack complete: {count} manipulated packets sent")
        print("→ IDS should detect unusual temporal patterns!")

    # === ATTACK 4: Jamming Attack - Signal Disruption ===
    def jamming_attack(self, duration=15):
        """
        Real attack: Wireless jamming causes null/zero readings
        IDS should detect: Sudden drops to zero or constant values
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 4: JAMMING ATTACK - Signal Disruption")
        print("=" * 70)
        print("Simulating: RF jamming causing null/zero readings")
        print("IDS should detect: Sudden drops to zero or flatline")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_configs = [
            ('S1', 'FHR'),
            ('S2', 'TOCO'),
            ('S3', 'SpO2'),
            ('S4', 'RespRate'),
            ('S5', 'Temp')
        ]

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            sensor_id, sensor_type = random.choice(sensor_configs)

            # Jamming causes zeros or very low constant values
            value = random.choice([0, 0, 0, 1, -1])  # Mostly zeros

            packet = self.create_packet(sensor_id, sensor_type, value)
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] {sensor_type}: {value} (JAMMED)")
            count += 1
            time.sleep(0.5)

        print(f"✓ Attack complete: {count} jammed packets sent")
        print("→ IDS should detect flatline patterns!")

    # === ATTACK 5: Replay Attack ===
    def replay_attack(self, duration=15):
        """
        Real attack: Replay same values repeatedly
        IDS should detect: Lack of natural variation, repeated patterns
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 5: REPLAY ATTACK - Repeated Pattern")
        print("=" * 70)
        print("Simulating: Attacker replaying captured 'normal' values")
        print("IDS should detect: Unnatural repetition and lack of variation")
        print(f"Duration: {duration}s")
        print("-" * 70)

        # Capture "normal" values to replay
        captured_values = {
            'S1': 145.5,  # FHR
            'S2': 45.0,  # TOCO
            'S3': 97.0,  # SpO2
            'S4': 18.0,  # RespRate
            'S5': 37.0  # Temp
        }

        sensor_types = {
            'S1': 'FHR',
            'S2': 'TOCO',
            'S3': 'SpO2',
            'S4': 'RespRate',
            'S5': 'Temp'
        }

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            # Keep replaying SAME values (no natural variation)
            for sensor_id in ['S1', 'S2', 'S3', 'S4', 'S5']:
                sensor_type = sensor_types[sensor_id]
                value = captured_values[sensor_id]  # Always same!

                packet = self.create_packet(sensor_id, sensor_type, value)
                self.send_packet(packet)

                print(f"  [REPLAY] {sensor_type}: {value} (repeated)")
                count += 1
                time.sleep(0.2)

        print(f"✓ Attack complete: {count} replayed packets sent")
        print("→ IDS should detect lack of natural variation!")

    # === ATTACK 6: Data Injection - Random Burst ===
    def false_data_injection(self, duration=15):
        """
        Real attack: Inject random data bursts
        IDS should detect: Sudden bursts of random values
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 6: FALSE DATA INJECTION - Random Bursts")
        print("=" * 70)
        print("Simulating: Injecting random data bursts")
        print("IDS should detect: Sudden value spikes and random patterns")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_configs = [
            ('S1', 'FHR'),
            ('S2', 'TOCO'),
            ('S3', 'SpO2'),
            ('S4', 'RespRate'),
            ('S5', 'Temp')
        ]

        end_time = time.time() + duration
        count = 0

        while time.time() < end_time:
            # Inject bursts of random values
            sensor_id, sensor_type = random.choice(sensor_configs)
            min_val, max_val = SENSOR_RANGES[sensor_type]

            # Random values with huge spikes
            value = round(random.uniform(min_val * 0.3, max_val * 1.8), 2)

            packet = self.create_packet(sensor_id, sensor_type, value)
            self.send_packet(packet)

            print(f"  [{packet['timestamp']}] Injected | {sensor_type}: {value}")
            count += 1
            time.sleep(0.7)

        print(f"✓ Attack complete: {count} false packets injected")
        print("→ IDS should flag random spikes!")

    # === ATTACK 7: Resource Exhaustion - Burst Pattern ===
    def resource_exhaustion(self, duration=15):
        """
        Real attack: Rapid bursts followed by silence
        IDS should detect: Unusual burst patterns
        """
        print("\n" + "=" * 70)
        print("🔴 ATTACK 7: RESOURCE EXHAUSTION - Burst Pattern")
        print("=" * 70)
        print("Simulating: Rapid packet bursts to drain resources")
        print("IDS should detect: Unusual burst frequency patterns")
        print(f"Duration: {duration}s")
        print("-" * 70)

        sensor_configs = [
            ('S1', 'FHR'),
            ('S2', 'TOCO'),
            ('S3', 'SpO2'),
            ('S4', 'RespRate'),
            ('S5', 'Temp')
        ]

        end_time = time.time() + duration
        total_count = 0

        while time.time() < end_time:
            # Burst phase: 30 packets rapidly
            print("  🔥 BURST PHASE (30 packets)...")
            for _ in range(30):
                sensor_id, sensor_type = random.choice(sensor_configs)
                min_val, max_val = SENSOR_RANGES[sensor_type]
                center = (min_val + max_val) / 2
                value = round(center + random.uniform(-20, 20), 2)

                packet = self.create_packet(sensor_id, sensor_type, value)
                self.send_packet(packet)
                total_count += 1
                time.sleep(0.03)

            # Silence phase
            print("  💤 Silence (2 seconds)...")
            time.sleep(2)

        print(f"✓ Attack complete: {total_count} burst packets sent")
        print("→ IDS should detect burst patterns!")

    def interactive_menu(self):
        """Interactive attack selection menu"""
        print("\n" + "=" * 70)
        print("     IoT ATTACK INJECTOR - Medical Sensor Network")
        print("                  (IDS DETECTION MODE)")
        print("=" * 70)
        print("\n⚠️  IMPORTANT:")
        print("   • No attack labels sent (is_attack=0 always)")
        print("   • Packets look like normal sensor traffic")
        print("   • Only the IDS model can detect anomalies")
        print("   • Watch collector console for real-time IDS predictions")
        print("\n" + "=" * 70)
        print("\nSelect Attack Type:\n")
        print("  1. DoS Flooding               - Network flooding with noise")
        print("  2. Spoofing Attack            - Extreme out-of-range values")
        print("  3. MITM Data Manipulation     - Subtle value manipulation")
        print("  4. Jamming Attack             - Zeros/null values (signal loss)")
        print("  5. Replay Attack              - Repeated values (no variation)")
        print("  6. False Data Injection       - Random burst patterns")
        print("  7. Resource Exhaustion        - Rapid burst patterns")
        print("  8. Run ALL Attacks (Sequence) - Test full IDS capability")
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
                    print("   Watch collector console for IDS detections!\n")
                    for name, attack_func in attacks.values():
                        print(f"\n▶️  Starting: {name}")
                        attack_func(duration=10)
                        print("\n⏸️  Waiting 5 seconds before next attack...\n")
                        time.sleep(5)
                    print("\n✅ All attacks completed!")
                    print("\n📊 Check these for results:")
                    print("   • Collector console: Real-time IDS predictions")
                    print("   • Dashboard (localhost:8050): Visual detection graphs")
                    print("   • data/sensor_data.csv: Full log with IDS predictions")
                    continue

                if choice in attacks:
                    name, attack_func = attacks[choice]
                    duration = input(f"Duration in seconds (default 15): ").strip()
                    duration = int(duration) if duration.isdigit() else 15

                    print(f"\n⚡ Launching attack...")
                    print(f"   → Watch collector console for IDS detections")
                    print(f"   → Check dashboard at http://localhost:8050\n")

                    attack_func(duration=duration)

                    print(f"\n✓ Attack finished!")
                    print(f"   Check collector console to see how many were detected")
                else:
                    print("❌ Invalid choice. Please enter 1-9.")

            except KeyboardInterrupt:
                print("\n\n👋 Attack injector stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🔴 IoT ATTACK INJECTOR - IDS DETECTION MODE")
    print(f"Target Gateway: {TARGET_IP}:{GATEWAY_PORT}")
    print(f"\n✅ Prerequisites:")
    print(f"   1. ✓ Sensor nodes running (normal traffic)")
    print(f"   2. ✓ Gateway forwarding packets")
    print(f"   3. ✓ Collector with IDS active")
    print(f"   4. ✓ Dashboard at http://localhost:8050")
    print(f"\n💡 How this works:")
    print(f"   • All attack packets have is_attack=0 (no labels)")
    print(f"   • IDS must detect anomalies based on patterns")
    print(f"   • Watch collector console for 🔴 ATTACK detections")
    print(f"   • Dashboard shows real-time IDS predictions\n")

    injector = IoTAttackInjector()
    injector.interactive_menu()