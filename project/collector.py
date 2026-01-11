import socket
import csv
import json
import os
from datetime import datetime
from threading import Thread
from collections import deque
from flask import Flask, render_template_string
from config import HOST_IP, COLLECTOR_PORT, DATA_FOLDER, CSV_FILENAME, DASHBOARD_PORT, DISPLAY_WINDOW, CHART_WINDOW
UDP_IP = HOST_IP

# Create data folder if not exists
os.makedirs(DATA_FOLDER, exist_ok=True)

# Store recent packets for dashboard (increased to 200 for better graphs)
recent_packets = deque(maxlen=200)
packet_count = {'normal': 0, 'attack': 0}

# Flask app for dashboard
app = Flask(__name__)

# HTML Template for Dashboard
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
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
        <h1>🏥 Gynecology Sensor Network - IDS</h1>
        <p class="subtitle">Real-time Intrusion Detection System Dashboard</p>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Packets</h3>
                <div class="number">{{ total_packets }}</div>
            </div>
            <div class="stat-card">
                <h3>Normal Traffic</h3>
                <div class="number">{{ normal_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Attack Detected</h3>
                <div class="number">{{ attack_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Active Sensors</h3>
                <div class="number">{{ active_sensors }}</div>
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
                    <td class="{{ 'status-attack' if packet.is_attack == 1 else 'status-normal' }}">
                        {{ 'ATTACK' if packet.is_attack == 1 else 'Normal' }}
                    </td>
                    <td>{{ packet.get('attack_type', '-') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <div class="footer">
            <p>Auto-refreshing every 2 seconds | Data saved to: {{ csv_file }}</p>
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
                                    },
                                    stepSize: sensorType === 'FHR' ? 50 : sensorType === 'TOCO' ? 30 : sensorType === 'SpO2' ? 10 : sensorType === 'Temp' ? 2 : 10
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


@app.route('/')
def dashboard():
    # Prepare chart data for each sensor type (last 100 values including attacks)
    chart_data = {}
    sensor_types = ['FHR', 'TOCO', 'SpO2', 'RespRate', 'Temp']

    # Define Y-axis ranges for each sensor (for better visibility)
    y_axis_ranges = {
        'FHR': {'min': 0, 'max': 250},
        'TOCO': {'min': 0, 'max': 150},
        'SpO2': {'min': 60, 'max': 105},
        'RespRate': {'min': 0, 'max': 40},
        'Temp': {'min': 35, 'max': 42}
    }

    for sensor_type in sensor_types:
        # Get last 100 values for this sensor type (including both normal and attack)
        sensor_packets = [p for p in recent_packets if p['sensor_type'] == sensor_type][-CHART_WINDOW:]

        chart_data[sensor_type] = {
            'labels': [i for i in range(len(sensor_packets))],
            'values': [p['value'] for p in sensor_packets],
            'colors': ['#ef4444' if p['is_attack'] == 1 else '#10b981' for p in sensor_packets],
            'yMin': y_axis_ranges[sensor_type]['min'],
            'yMax': y_axis_ranges[sensor_type]['max']
        }

    return render_template_string(
        DASHBOARD_HTML,
        packets=list(reversed(recent_packets)),
        total_packets=packet_count['normal'] + packet_count['attack'],
        normal_count=packet_count['normal'],
        attack_count=packet_count['attack'],
        active_sensors=5,
        packet_limit=DISPLAY_WINDOW,
        csv_file=f"{DATA_FOLDER}/{CSV_FILENAME}",
        chart_data=chart_data
    )


def udp_receiver():
    """Receive UDP packets from Gateway and save to CSV"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, COLLECTOR_PORT))

    csv_path = os.path.join(DATA_FOLDER, CSV_FILENAME)

    # Create CSV with headers if not exists
    file_exists = os.path.exists(csv_path)
    csvfile = open(csv_path, 'a', newline='')
    writer = csv.DictWriter(csvfile,
                            fieldnames=['timestamp', 'sensor_id', 'sensor_type', 'value', 'is_attack', 'attack_type'],
                            extrasaction='ignore')

    if not file_exists:
        writer.writeheader()

    print(f"✓ UDP Receiver started on {HOST_IP}:{COLLECTOR_PORT} (receiving from Gateway)")
    print(f"✓ Saving data to: {csv_path}")
    print(f"✓ Dashboard running at: http://localhost:{DASHBOARD_PORT}")
    print("\nWaiting for data from Gateway...\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            packet = json.loads(data.decode())

            # Save to CSV
            writer.writerow(packet)
            csvfile.flush()

            # Store for dashboard
            recent_packets.append(packet)

            # Update counters
            if packet['is_attack'] == 1:
                packet_count['attack'] += 1
            else:
                packet_count['normal'] += 1

            print(
                f"[{packet['timestamp']}] {packet['sensor_type']} (ID:{packet['sensor_id']}): {packet['value']} | Status: {'ATTACK' if packet['is_attack'] == 1 else 'Normal'}")

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