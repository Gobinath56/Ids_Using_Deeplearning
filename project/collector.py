import socket
import json
import time
import numpy as np
import joblib
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from collections import deque
from flask import Flask, render_template_string, send_file, jsonify
from tensorflow.keras.models import load_model
from config import HOST_IP, COLLECTOR_PORT, SENSOR_RANGES, DASHBOARD_PORT
from email_config import (
    SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD,
    AUTHORIZED_RECIPIENTS, ENABLE_EMAIL_ALERTS, EMAIL_COOLDOWN,
    ATTACK_EMAIL_TEMPLATE, ATTACK_SUBJECT, ATTACK_DESCRIPTIONS
)
from datetime import datetime
import os

# ======================================================
# CONFIG
# ======================================================
WINDOW_SIZE = 60
FEATURE_IDS = ["S1", "S2", "S3", "S4", "S5"]

FEATURE_NAMES = {
    "S1": "FHR",
    "S2": "TOCO",
    "S3": "SpO2",
    "S4": "RespRate",
    "S5": "Temp"
}

EXPECTED_SENSOR_TYPE = FEATURE_NAMES.copy()

MODEL_PATH = "../medical_iot_ids/model/lstm_autoencoder.h5"
SCALER_PATH = "../medical_iot_ids/model/scaler.pkl"

CALIBRATION_WINDOWS = 20
K_SIGMA = 2.5

ATTACK_CONFIRMATION = 3
RECOVERY_CONFIRMATION = 8
MIN_ATTACK_DURATION = 1.2

# CSV Export Configuration
CSV_FOLDER = "data_exports"
CSV_FILENAME = f"{CSV_FOLDER}/sensor_data_{datetime.now().strftime('%Y%m%d')}.csv"

# ======================================================
# LOAD MODEL
# ======================================================
model = load_model(MODEL_PATH, compile=False)
scaler = joblib.load(SCALER_PATH)
print("✅ IDS Model Loaded")

# ======================================================
# STATE
# ======================================================
sensor_windows = {sid: deque(maxlen=WINDOW_SIZE) for sid in FEATURE_IDS}
last_value = {sid: None for sid in FEATURE_IDS}

recent_packets = deque(maxlen=400)
error_history = deque(maxlen=CALIBRATION_WINDOWS)

# CSV Storage - stores ALL packets received
all_packets_log = []

CALIBRATION_DONE = False
THRESHOLD = None

ATTACK_ACTIVE = False
ATTACK_START_TIME = None
FIRST_ANOMALY_TIME = None

CONSECUTIVE_ANOMALIES = 0
NORMAL_STREAK = 0
LAST_DECISION = "CALIBRATING"

# Counters
TOTAL = 0
NORMAL = 0
INJECTED_ATTACKS = 0
DETECTED_ATTACKS = 0
PENDING_INJECTED = 0

ATTACK_CONFIRMED_IN_SESSION = False

# Attack tracking
current_attack = {
    "sensors": set(),
    "packets": 0,
    "type_counts": {}
}

last_attack_summary = {
    "type": "-",
    "sensors": "-",
    "duration": "-",
    "packets": 0
}

attack_history = deque(maxlen=6)

# Email tracking
last_email_time = 0


# ======================================================
# CSV FUNCTIONS
# ======================================================
def initialize_csv():
    """Create CSV folder and file with headers"""
    os.makedirs(CSV_FOLDER, exist_ok=True)

    if not os.path.exists(CSV_FILENAME):
        with open(CSV_FILENAME, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'epoch', 'sensor_id', 'sensor_type',
                'value', 'ids_status', 'attack_type', 'ids_error'
            ])
        print(f"✅ CSV file created: {CSV_FILENAME}")


def append_to_csv(packet):
    """Append packet data to CSV file"""
    try:
        with open(CSV_FILENAME, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                packet.get('timestamp', ''),
                packet.get('epoch', ''),
                packet.get('sensor_id', ''),
                packet.get('sensor_type', ''),
                packet.get('value', ''),
                packet.get('ids_status', ''),
                packet.get('attack_type', ''),
                packet.get('ids_error', '')
            ])
    except Exception as e:
        print(f"⚠️ CSV write error: {e}")


# ======================================================
# EMAIL FUNCTIONS
# ======================================================
def send_email_alert(attack_data):
    """Send email notification about detected attack"""
    print("📧 EMAIL FUNCTION TRIGGERED")

    global last_email_time

    if not ENABLE_EMAIL_ALERTS:
        return

    # Check cooldown period
    current_time = time.time()
    if current_time - last_email_time < EMAIL_COOLDOWN:
        print(f"⏳ Email cooldown active, skipping alert")
        return

    try:
        # Prepare email content
        attack_type = attack_data['type']
        description = ATTACK_DESCRIPTIONS.get(attack_type, "<li>Unknown attack pattern</li>")

        html_content = ATTACK_EMAIL_TEMPLATE.format(
            attack_type=attack_type,
            detection_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            duration=attack_data['duration'],
            sensors=attack_data['sensors'],
            packets=attack_data['packets'],
            attack_description=description
        )

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = ATTACK_SUBJECT
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(AUTHORIZED_RECIPIENTS)

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        last_email_time = current_time
        print(f"✅ Email alert sent to {len(AUTHORIZED_RECIPIENTS)} recipients")

    except Exception as e:
        print(f"❌ Email send error: {e}")
        print("   Check email_config.py settings and ensure:")
        print("   - SENDER_EMAIL and SENDER_PASSWORD are correct")
        print("   - Gmail App Password is used (not regular password)")
        print("   - SMTP settings are correct")


# ======================================================
# HELPERS
# ======================================================
def compute_threshold():
    global THRESHOLD
    THRESHOLD = float(np.mean(error_history) + K_SIGMA * np.std(error_history))


def security_violation(sensor, value, prev, sid):
    lo, hi = SENSOR_RANGES[sensor]

    # Identity spoofing
    if EXPECTED_SENSOR_TYPE[sid] != sensor:
        return "Spoofing"

    # Jamming
    if value in [0, -1]:
        return "Jamming"

    # Value spoofing
    if value < lo or value > hi:
        return "Spoofing"

    # MITM manipulation
    if prev is not None and abs(value - prev) > 0.4 * (hi - lo):
        return "MITM / Manipulation"

    return None


def sensors_all_normal():
    for sid in FEATURE_IDS:
        if not sensor_windows[sid]:
            return False
        v = sensor_windows[sid][-1]
        lo, hi = SENSOR_RANGES[FEATURE_NAMES[sid]]
        if v < lo or v > hi or v in [0, -1]:
            return False
    return True


# ======================================================
# UDP RECEIVER
# ======================================================
def udp_receiver():
    global TOTAL, NORMAL, CALIBRATION_DONE, ATTACK_ACTIVE
    global ATTACK_START_TIME, FIRST_ANOMALY_TIME
    global CONSECUTIVE_ANOMALIES, NORMAL_STREAK
    global LAST_DECISION, INJECTED_ATTACKS, DETECTED_ATTACKS
    global ATTACK_CONFIRMED_IN_SESSION, PENDING_INJECTED, last_attack_summary

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST_IP, COLLECTOR_PORT))
    print("🛡️ IDS Listening...")
    print(f"📧 Email alerts: {'ENABLED' if ENABLE_EMAIL_ALERTS else 'DISABLED'}")
    print(f"📊 CSV logging: {CSV_FILENAME}\n")

    while True:
        try:
            pkt = json.loads(sock.recvfrom(4096)[0].decode())
            pkt["epoch"] = time.time()
            pkt["timestamp"] = time.strftime("%H:%M:%S")

            # ---------- ATTACK META ----------
            if pkt.get("type") == "ATTACK_META":
                INJECTED_ATTACKS += 1
                PENDING_INJECTED += 1
                continue

            sid = pkt["sensor_id"]
            stype = pkt["sensor_type"]
            value = pkt["value"]

            if sid not in FEATURE_IDS:
                continue

            TOTAL += 1
            prev = last_value[sid]
            sensor_windows[sid].append(value)

            # ---------- CALIBRATION ----------
            if not all(len(w) == WINDOW_SIZE for w in sensor_windows.values()):
                pkt.update({"ids_status": "CALIBRATING", "attack_type": "-", "ids_error": "-"})
                recent_packets.appendleft(pkt)
                all_packets_log.append(pkt.copy())
                append_to_csv(pkt)
                LAST_DECISION = "CALIBRATING"
                last_value[sid] = value
                continue

            # ---------- LSTM ----------
            window = scaler.transform(
                np.array([list(sensor_windows[s]) for s in FEATURE_IDS]).T
            )
            x = window.reshape(1, WINDOW_SIZE, len(FEATURE_IDS))
            recon = model.predict(x, verbose=0)
            error = float(np.mean((x - recon) ** 2))

            if not CALIBRATION_DONE:
                if security_violation(stype, value, prev, sid) is None:
                    error_history.append(error)

                if len(error_history) == CALIBRATION_WINDOWS:
                    compute_threshold()
                    CALIBRATION_DONE = True
                    print(f"✅ Calibration complete | Threshold={THRESHOLD:.6f}")

                pkt.update({"ids_status": "CALIBRATING", "attack_type": "-", "ids_error": "-"})
                recent_packets.appendleft(pkt)
                all_packets_log.append(pkt.copy())
                append_to_csv(pkt)
                last_value[sid] = value
                continue

            # ---------- DETECTION ----------
            violation = security_violation(stype, value, prev, sid)
            is_anomaly = (error > THRESHOLD) and violation is not None

            if is_anomaly:
                if CONSECUTIVE_ANOMALIES == 0:
                    FIRST_ANOMALY_TIME = pkt["epoch"]
                CONSECUTIVE_ANOMALIES += 1
                NORMAL_STREAK = 0
            else:
                NORMAL_STREAK += 1
                CONSECUTIVE_ANOMALIES = 0

            if CONSECUTIVE_ANOMALIES >= ATTACK_CONFIRMATION and not ATTACK_ACTIVE:
                ATTACK_ACTIVE = True
                ATTACK_START_TIME = FIRST_ANOMALY_TIME
                current_attack["sensors"].clear()
                current_attack["packets"] = 0
                current_attack["type_counts"].clear()

            if ATTACK_ACTIVE and not ATTACK_CONFIRMED_IN_SESSION:
                if pkt["epoch"] - ATTACK_START_TIME >= MIN_ATTACK_DURATION:
                    ATTACK_CONFIRMED_IN_SESSION = True

            if is_anomaly:
                pkt["ids_status"] = "ATTACK"
                pkt["attack_type"] = violation
                current_attack["packets"] += 1
                current_attack["sensors"].add(stype)
                current_attack["type_counts"][violation] = \
                    current_attack["type_counts"].get(violation, 0) + 1
            else:
                pkt["ids_status"] = "NORMAL"
                pkt["attack_type"] = "-"
                NORMAL += 1

            pkt["ids_error"] = round(error, 6)
            recent_packets.appendleft(pkt)
            all_packets_log.append(pkt.copy())
            append_to_csv(pkt)
            LAST_DECISION = "ATTACK" if ATTACK_ACTIVE else "NORMAL"

            # ---------- ATTACK END ----------

            if ATTACK_ACTIVE and NORMAL_STREAK >= RECOVERY_CONFIRMATION and sensors_all_normal():
                duration = round(pkt["epoch"] - ATTACK_START_TIME, 1)

                attack_type = max(
                    current_attack["type_counts"],
                    key=current_attack["type_counts"].get
                )

                last_attack_summary = {
                    "type": attack_type,
                    "sensors": ", ".join(sorted(current_attack["sensors"])),
                    "duration": duration,
                    "packets": current_attack["packets"]
                }

                attack_history.appendleft({
                    "time": time.strftime("%H:%M:%S"),
                    **last_attack_summary
                })

                # ✅ FINAL FIXED COUNTER LOGIC
                DETECTED_ATTACKS += 1

                if PENDING_INJECTED > 0:
                    PENDING_INJECTED -= 1

                # ✅ EMAIL TRIGGER (NOW WILL WORK)
                send_email_alert(last_attack_summary)

                ATTACK_ACTIVE = False
                ATTACK_CONFIRMED_IN_SESSION = False
                CONSECUTIVE_ANOMALIES = 0
                NORMAL_STREAK = 0
                FIRST_ANOMALY_TIME = None
            last_value[sid] = value

        except Exception as e:
            print("❌ Collector error:", e)


# ======================================================
# DASHBOARD WITH CSV DOWNLOAD
# ======================================================
app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html>
<head>
<title>Medical IoT IDS</title>
<meta http-equiv="refresh" content="2">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0e1117;color:#e6edf3;font-family:Segoe UI;padding:20px}
.section{background:#161b22;border-radius:14px;padding:16px;margin-bottom:20px}
.header{display:flex;justify-content:space-between;align-items:center}
.status{padding:10px 24px;border-radius:24px;font-weight:bold}
.status.NORMAL{background:#2ea043;color:black}
.status.ATTACK{background:#f85149;color:black}
.status.CALIBRATING{background:#d29922;color:black}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:15px}
.kpi span{color:#8b949e;font-size:12px}
.kpi p{font-size:22px;font-weight:bold}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.history{max-height:180px;overflow-y:auto}
.graph-grid{display:grid;grid-template-columns:repeat(3,1fr);grid-template-areas:"g1 g2 g3" "g4 g5 .";gap:20px}
.graph{background:#0e1117;padding:12px;border-radius:12px}
.g1{grid-area:g1}.g2{grid-area:g2}.g3{grid-area:g3}.g4{grid-area:g4}.g5{grid-area:g5}
table{width:100%;border-collapse:collapse}
th,td{padding:8px;border-bottom:1px solid #30363d;text-align:center;font-size:13px}
th{color:#8b949e}
tr.NORMAL{color:#2ea043}
tr.ATTACK{color:#f85149;background:#2d0f14}
tr.CALIBRATING{color:#d29922;background:#2d210f}
.csv-btn{
    background: linear-gradient(135deg,#2ea043,#1f6feb);
    color:white;
    padding:10px 18px;
    border-radius:10px;
    font-weight:600;
    text-decoration:none;
    font-size:13px;
    box-shadow:0 0 12px rgba(46,160,67,0.35);
    transition:0.25s;
}
.csv-btn:hover{
    transform:translateY(-1px);
    box-shadow:0 0 18px rgba(31,111,235,0.55);
}

.btn-container{display:flex;gap:10px;align-items:center}
</style>
</head>
<body>

<div class="section header">
<h2>🛡️ Medical IoT IDS</h2>
<div class="btn-container">
<div class="status {{ decision }}">{{ decision }}</div>
</div>
</div>

<div class="section kpis">
<div class="kpi"><span>Total Packets</span><p>{{ total }}</p></div>
<div class="kpi"><span>Normal</span><p>{{ normal }}</p></div>
<div class="kpi"><span>Injected</span><p>{{ injected }}</p></div>
<div class="kpi"><span>Detected</span><p>{{ detected }}</p></div>
<div class="kpi"><span>Rate</span><p>{{ rate }}%</p></div>
</div>

<div class="two-col">
<div class="section">
<h4>Attack Summary</h4>
<p><b>Type:</b> {{ summary.type }}</p>
<p><b>Sensors:</b> {{ summary.sensors }}</p>
<p><b>Duration:</b> {{ summary.duration }} s</p>
<p><b>Packets:</b> {{ summary.packets }}</p>
</div>

<div class="section">
<h4>Attack History</h4>
<div class="history">
{% for a in history %}
<p>{{ a.time }} | {{ a.type }} | {{ a.sensors }} | {{ a.duration }} s | {{ a.packets }} packets</p>
{% endfor %}
</div>
</div>
</div>

<div class="section graph-grid">
<div class="graph g1"><h4>FHR</h4><canvas id="S1"></canvas></div>
<div class="graph g2"><h4>TOCO</h4><canvas id="S2"></canvas></div>
<div class="graph g3"><h4>SpO₂</h4><canvas id="S3"></canvas></div>
<div class="graph g4"><h4>RespRate</h4><canvas id="S4"></canvas></div>
<div class="graph g5"><h4>Temp</h4><canvas id="S5"></canvas></div>
</div>

<div class="section">

<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
    <h4 style="margin:0">Live Sensor Table</h4>
    <a href="/download_csv" class="csv-btn">⬇ Export CSV</a>
</div>

<div style="max-height:260px;overflow-y:auto">

<table>
<tr><th>Time</th><th>Sensor</th><th>Value</th><th>Status</th></tr>
{% for p in packets %}
<tr class="{{ p.ids_status }}">
<td>{{ p.timestamp }}</td>
<td>{{ p.sensor_type }}</td>
<td>{{ p.value }}</td>
<td>{{ p.ids_status }}</td>
</tr>
{% endfor %}
</table>
</div>
</div>

<div class="section" style="text-align:center;padding:12px">
<p style="color:#8b949e;font-size:13px">
📧 Email Alerts: {{ email_status }} | 📊 CSV File: {{ csv_file }} | 📦 Total Records: {{ total_records }}
</p>
</div>

<script>
const packets={{ packets|tojson }};
["S1","S2","S3","S4","S5"].forEach(id=>{
 const rows=packets.filter(p=>p.sensor_id===id).reverse();
 const ctx=document.getElementById(id);
 if(!ctx)return;
 new Chart(ctx,{type:"line",
 data:{labels:rows.map(p=>p.timestamp),
 datasets:[{data:rows.map(p=>p.value),
 borderColor:"#2ea043",
 pointBackgroundColor:rows.map(p=>p.ids_status==="ATTACK"?"#f85149":p.ids_status==="CALIBRATING"?"#d29922":"#2ea043"),
 pointRadius:4,tension:0.3}]},
 options:{plugins:{legend:{display:false}},scales:{x:{display:false}}}});
});
</script>

</body>
</html>
"""


@app.route("/")
def dashboard():
    rate = round((DETECTED_ATTACKS / INJECTED_ATTACKS) * 100, 2) if INJECTED_ATTACKS else 0
    return render_template_string(
        HTML,
        total=TOTAL,
        normal=NORMAL,
        injected=INJECTED_ATTACKS,
        detected=DETECTED_ATTACKS,
        rate=rate,
        decision=LAST_DECISION,
        packets=list(recent_packets),
        summary=last_attack_summary,
        history=list(attack_history),
        email_status="ENABLED" if ENABLE_EMAIL_ALERTS else "DISABLED",
        csv_file=CSV_FILENAME,
        total_records=len(all_packets_log)
    )


@app.route("/download_csv")
def download_csv():
    """Download current CSV file"""
    try:
        return send_file(
            CSV_FILENAME,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sensor_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return f"Error downloading CSV: {e}", 500


@app.route("/api/stats")
def api_stats():
    """API endpoint for statistics"""
    return jsonify({
        "total_packets": TOTAL,
        "normal_packets": NORMAL,
        "injected_attacks": INJECTED_ATTACKS,
        "detected_attacks": DETECTED_ATTACKS,
        "detection_rate": round((DETECTED_ATTACKS / INJECTED_ATTACKS) * 100, 2) if INJECTED_ATTACKS else 0,
        "current_status": LAST_DECISION,
        "csv_records": len(all_packets_log)
    })


if __name__ == "__main__":
    # Initialize CSV on startup
    initialize_csv()

    Thread(target=udp_receiver, daemon=True).start()
    print("\n" + "=" * 70)
    print("📊 Dashboard: http://localhost:8050")
    print("📥 CSV Download: http://localhost:8050/download_csv")
    print("📡 API Stats: http://localhost:8050/api/stats")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False)