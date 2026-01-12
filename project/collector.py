import socket
import csv
import json
import os
import numpy as np
import joblib
from datetime import datetime
from threading import Thread
from collections import deque
from flask import Flask, render_template_string
from tensorflow.keras.models import load_model
from config import HOST_IP, COLLECTOR_PORT, DATA_FOLDER, CSV_FILENAME, DASHBOARD_PORT, DISPLAY_WINDOW, CHART_WINDOW

# ===========================
# IDS MODEL CONFIGURATION
# ===========================
WINDOW_SIZE = 60
THRESHOLD = 1.20  # Optimal threshold from evaluation
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "medical_iot_ids", "model", "lstm_autoencoder.h5")
SCALER_PATH = os.path.join(BASE_DIR, "..", "medical_iot_ids", "model", "scaler.pkl")

# Load IDS Model
print("=" * 70)
print("Loading IDS Model...")
try:
    model = load_model(MODEL_PATH, compile=False)
    scaler = joblib.load(SCALER_PATH)
    print("✓ LSTM Autoencoder loaded successfully")
    print(f"✓ Threshold: {THRESHOLD}")
    IDS_ENABLED = True
except Exception as e:
    print(f"⚠️  Could not load IDS model: {e}")
    print("⚠️  Running without IDS detection")
    IDS_ENABLED = False

print("=" * 70)

UDP_IP = HOST_IP

# Create data folder if not exists
os.makedirs(DATA_FOLDER, exist_ok=True)

# Store recent packets for dashboard
recent_packets = deque(maxlen=200)
packet_count = {'normal': 0, 'attack': 0}

# IDS: Sliding window for real-time detection
sensor_windows = {
    'S1': deque(maxlen=WINDOW_SIZE),  # FHR
    'S2': deque(maxlen=WINDOW_SIZE),  # TOCO
    'S3': deque(maxlen=WINDOW_SIZE),  # SpO2
    'S4': deque(maxlen=WINDOW_SIZE),  # RespRate
    'S5': deque(maxlen=WINDOW_SIZE),  # Temp
}

# Track IDS statistics
ids_stats = {
    'total_predictions': 0,
    'attacks_detected': 0,
    'normal_detected': 0,
    'last_error': 0.0
}

# Flask app for dashboard
app = Flask(__name__)

# HTML Template for Dashboard (with IDS integration)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Medical Sensor Network - IDS Dashboard</title>
    <meta http-equiv="refresh" content="2">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .ids-status {
            text-align: center;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 16px;
        }
        .ids-enabled {
            background: #d4edda;
            color: #155724;
            border: 2px solid #28a745;
        }
        .ids-disabled {
            background: #f8d7da;
            color: #721c24;
            border: 2px solid #dc3545;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #fff;
            border: 1px solid #ddd;
            color: #333;
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
            font-weight: normal;
        }
        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        .stat-card.attack {
            border-left: 4px solid #e74c3c;
        }
        .stat-card.normal {
            border-left: 4px solid #2ecc71;
        }
        .stat-card.ids {
            border-left: 4px solid #3498db;
        }
        .charts-section {
            margin-bottom: 30px;
        }
        .charts-section h2 {
            font-size: 20px;
            margin-bottom: 20px;
            color: #333;
        }
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        .chart-box {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            background: #fafafa;
        }
        .chart-box h3 {
            margin: 0 0 15px 0;
            color: #333;
            font-size: 16px;
        }
        canvas {
            width: 100% !important;
            height: 250px !important;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: normal;
            font-size: 14px;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 13px;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .status-normal {
            color: #10b981;
            font-weight: bold;
        }
        .status-attack {
            color: #ef4444;
            font-weight: bold;
        }
        .ids-prediction {
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        }
        .ids-normal {
            background: #d4edda;
            color: #155724;
        }
        .ids-attack {
            background: #f8d7da;
            color: #721c24;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #888;
            font-size: 12px;
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>🏥 Medical Sensor Network - Real-Time IDS</h1>
        <p class="subtitle">LSTM Autoencoder-based Intrusion Detection System</p>

        <div class="ids-status {{ 'ids-enabled' if ids_enabled else 'ids-disabled' }}">
            {% if ids_enabled %}
                🛡️ IDS ACTIVE - Real-time threat detection enabled (Threshold: {{ threshold }})
            {% else %}
                ⚠️ IDS DISABLED - Running without threat detection
            {% endif %}
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Packets</h3>
                <div class="number">{{ total_packets }}</div>
            </div>
            <div class="stat-card normal">
                <h3>Normal Traffic</h3>
                <div class="number">{{ normal_count }}</div>
            </div>
            <div class="stat-card attack">
                <h3>Attacks Detected</h3>
                <div class="number">{{ attack_count }}</div>
            </div>
            <div class="stat-card ids">
                <h3>IDS Predictions</h3>
                <div class="number">{{ ids_predictions }}</div>
            </div>
            <div class="stat-card">
                <h3>Detection Rate</h3>
                <div class="number">{{ detection_rate }}%</div>
            </div>
            <div class="stat-card">
                <h3>Last Error</h3>
                <div class="number" style="font-size: 24px;">{{ last_error }}</div>
            </div>
        </div>

        <div class="charts-section">
            <h2>Sensor Readings (Last 100 values - Red = Attack, Green = Normal)</h2>
            <div class="charts-grid">
                <div class="chart-box">
                    <h3>FHR (Fetal Heart Rate)</h3>
                    <canvas id="chart-FHR"></canvas>
                </div>
                <div class="chart-box">
                    <h3>TOCO (Uterine Contraction)</h3>
                    <canvas id="chart-TOCO"></canvas>
                </div>
                <div class="chart-box">
                    <h3>SpO2 (Blood Oxygen)</h3>
                    <canvas id="chart-SpO2"></canvas>
                </div>
                <div class="chart-box">
                    <h3>RespRate (Respiratory Rate)</h3>
                    <canvas id="chart-RespRate"></canvas>
                </div>
                <div class="chart-box">
                    <h3>Temp (Temperature)</h3>
                    <canvas id="chart-Temp"></canvas>
                </div>
            </div>
        </div>

        <h2>Recent Packet Stream (Last {{ packet_limit }})</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Sensor ID</th>
                    <th>Type</th>
                    <th>Value</th>
                    <th>IDS Prediction</th>
                    <th>Recon. Error</th>
                    <th>Status</th>
                    <th>Attack Type</th>
                </tr>
            </thead>
            <tbody>
                {% for packet in packets %}
                <tr>
                    <td>{{ packet.timestamp }}</td>
                    <td>{{ packet.sensor_id }}</td>
                    <td>{{ packet.sensor_type }}</td>
                    <td>{{ packet.value }}</td>
                    <td>
                        {% if packet.get('ids_prediction') is not none %}
                            <span class="ids-prediction {{ 'ids-attack' if packet.ids_prediction == 1 else 'ids-normal' }}">
                                {{ 'ATTACK' if packet.ids_prediction == 1 else 'Normal' }}
                            </span>
                        {% else %}
                            <span style="color: #999;">-</span>
                        {% endif %}
                    </td>
                    <td>{{ '%.4f'|format(packet.ids_error) if packet.get('ids_error') is not none else '-' }}</td>
                    <td class="{{ 'status-attack' if packet.is_attack == 1 else 'status-normal' }}">
                        {{ 'ATTACK' if packet.is_attack == 1 else 'Normal' }}
                    </td>
                    <td>{{ packet.get('attack_type', '-') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="footer">
            <p>Auto-refreshing every 2 seconds | Data saved to: {{ csv_file }} | Model: LSTM Autoencoder</p>
        </div>
    </div>

    <script>
        const chartData = {{ chart_data | tojson }};
        const chartColors = {
            'FHR': '#3b82f6',
            'TOCO': '#8b5cf6',
            'SpO2': '#10b981',
            'RespRate': '#f59e0b',
            'Temp': '#ef4444'
        };

        Object.keys(chartData).forEach(sensorType => {
            const ctx = document.getElementById('chart-' + sensorType);
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData[sensorType].labels,
                        datasets: [{
                            label: sensorType,
                            data: chartData[sensorType].values,
                            borderColor: chartColors[sensorType],
                            backgroundColor: chartColors[sensorType] + '20',
                            pointBackgroundColor: chartData[sensorType].colors,
                            pointBorderColor: chartData[sensorType].colors,
                            pointRadius: 3,
                            pointHoverRadius: 5,
                            borderWidth: 2,
                            tension: 0.1,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return 'Value: ' + context.parsed.y;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                min: chartData[sensorType].yMin,
                                max: chartData[sensorType].yMax,
                                grid: {
                                    color: '#e5e5e5'
                                },
                                ticks: {
                                    font: {
                                        size: 12
                                    }
                                }
                            },
                            x: {
                                display: false
                            }
                        }
                    }
                });
            }
        });
    </script>
</body>
</html>
"""


def predict_ids(sensor_values):
    """
    Real-time IDS prediction using LSTM Autoencoder

    Args:
        sensor_values: numpy array [FHR, TOCO, SpO2, RespRate, Temp]

    Returns:
        (is_attack, reconstruction_error)
    """
    if not IDS_ENABLED:
        return None, None

    try:
        # Reshape for model input: (1, 60, 5)
        window = sensor_values.reshape(1, WINDOW_SIZE, 5)

        # Get reconstruction
        reconstruction = model.predict(window, verbose=0)

        # Calculate reconstruction error
        error = np.mean((window - reconstruction) ** 2)

        # Classify
        is_attack = 1 if error > THRESHOLD else 0

        # Update stats
        ids_stats['total_predictions'] += 1
        ids_stats['last_error'] = error
        if is_attack:
            ids_stats['attacks_detected'] += 1
        else:
            ids_stats['normal_detected'] += 1

        return is_attack, float(error)

    except Exception as e:
        print(f"IDS Prediction Error: {e}")
        return None, None


@app.route('/')
def dashboard():
    # Prepare chart data
    chart_data = {}
    sensor_types = ['FHR', 'TOCO', 'SpO2', 'RespRate', 'Temp']

    y_axis_ranges = {
        'FHR': {'min': 0, 'max': 250},
        'TOCO': {'min': 0, 'max': 150},
        'SpO2': {'min': 60, 'max': 105},
        'RespRate': {'min': 0, 'max': 40},
        'Temp': {'min': 35, 'max': 42}
    }

    for sensor_type in sensor_types:
        sensor_packets = [p for p in recent_packets if p['sensor_type'] == sensor_type][-CHART_WINDOW:]

        chart_data[sensor_type] = {
            'labels': [i for i in range(len(sensor_packets))],
            'values': [p['value'] for p in sensor_packets],
            'colors': ['#ef4444' if p.get('ids_prediction', 0) == 1 else '#10b981' for p in sensor_packets],
            'yMin': y_axis_ranges[sensor_type]['min'],
            'yMax': y_axis_ranges[sensor_type]['max']
        }

    total = packet_count['normal'] + packet_count['attack']
    detection_rate = round((packet_count['attack'] / total * 100) if total > 0 else 0, 1)

    return render_template_string(
        DASHBOARD_HTML,
        packets=list(reversed(recent_packets)),
        total_packets=total,
        normal_count=packet_count['normal'],
        attack_count=packet_count['attack'],
        packet_limit=DISPLAY_WINDOW,
        csv_file=f"{DATA_FOLDER}/{CSV_FILENAME}",
        chart_data=chart_data,
        ids_enabled=IDS_ENABLED,
        threshold=THRESHOLD,
        ids_predictions=ids_stats['total_predictions'],
        detection_rate=detection_rate,
        last_error=f"{ids_stats['last_error']:.4f}"
    )


def udp_receiver():
    """Receive UDP packets from Gateway and process with IDS (FIXED)"""
    import time

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, COLLECTOR_PORT))

    csv_path = os.path.join(DATA_FOLDER, CSV_FILENAME)

    # Create CSV with headers
    file_exists = os.path.exists(csv_path)
    csvfile = open(csv_path, 'a', newline='')
    writer = csv.DictWriter(
        csvfile,
        fieldnames=[
            'timestamp', 'sensor_id', 'sensor_type', 'value',
            'is_attack', 'attack_type', 'ids_prediction', 'ids_error'
        ],
        extrasaction='ignore'
    )

    if not file_exists:
        writer.writeheader()

    print(f"✓ UDP Receiver started on {HOST_IP}:{COLLECTOR_PORT}")
    print(f"✓ Saving data to: {csv_path}")
    print(f"✓ Dashboard running at: http://localhost:{DASHBOARD_PORT}")
    if IDS_ENABLED:
        print(f"✓ IDS Model: LSTM Autoencoder (Threshold: {THRESHOLD})")
    print("\nWaiting for data from Gateway...\n")

    # 🔑 IDS cooldown handling
    COOLDOWN_SECONDS = 5
    last_attack_time = 0

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            packet = json.loads(data.decode())

            sensor_id = packet['sensor_id']
            sensor_type = packet['sensor_type']
            value = packet['value']

            # Add to sliding window
            if sensor_id in sensor_windows:
                sensor_windows[sensor_id].append(value)

            ids_prediction = None
            ids_error = None

            # IDS Prediction only if:
            # 1. Window is full
            # 2. Not in cooldown period
            if (
                IDS_ENABLED and
                all(len(sensor_windows[sid]) == WINDOW_SIZE for sid in sensor_windows) and
                (time.time() - last_attack_time) > COOLDOWN_SECONDS
            ):
                current_window = np.array([
                    list(sensor_windows['S1']),  # FHR
                    list(sensor_windows['S2']),  # TOCO
                    list(sensor_windows['S3']),  # SpO2
                    list(sensor_windows['S4']),  # RespRate
                    list(sensor_windows['S5'])   # Temp
                ]).T  # (60, 5)

                normalized_window = scaler.transform(current_window)
                ids_prediction, ids_error = predict_ids(normalized_window)

                # 🔴 ATTACK DETECTED → RESET WINDOWS
                if ids_prediction == 1:
                    last_attack_time = time.time()

                    # Clear contaminated windows
                    for sid in sensor_windows:
                        sensor_windows[sid].clear()

            # Attach IDS result
            packet['ids_prediction'] = ids_prediction
            packet['ids_error'] = ids_error

            # 🔥 IMPORTANT: IDS decides attack status
            if ids_prediction is not None:
                packet['is_attack'] = ids_prediction

            # Save to CSV
            writer.writerow(packet)
            csvfile.flush()

            # Store for dashboard
            recent_packets.append(packet)

            # Update counters
            if ids_prediction == 1:
                packet_count['attack'] += 1
            elif ids_prediction == 0:
                packet_count['normal'] += 1

            # Console output
            if ids_prediction is None:
                status_symbol = "⏳"
                ids_info = ""
            else:
                status_symbol = "🔴" if ids_prediction == 1 else "✅"
                ids_info = f" | IDS: {'ATTACK' if ids_prediction == 1 else 'Normal'} (err={ids_error:.4f})"

            print(f"{status_symbol} [{packet['timestamp']}] "
                  f"{sensor_type} (ID:{sensor_id}): {value}{ids_info}")

    except KeyboardInterrupt:
        print("\n\nCollector stopped")
        csvfile.close()
        sock.close()



if __name__ == "__main__":
    # Start UDP receiver in separate thread
    receiver_thread = Thread(target=udp_receiver, daemon=True)
    receiver_thread.start()

    # Start Flask dashboard
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False)