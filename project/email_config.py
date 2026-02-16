# Email Configuration for Attack Notifications

# SMTP Configuration
SMTP_SERVER = "smtp.gmail.com"  # For Gmail
SMTP_PORT = 587  # TLS port
SENDER_EMAIL = "medical.iot.alert@gmail.com"  # ⚠️ CHANGE THIS to your email
SENDER_PASSWORD = "lqkuqjmttndaqdvt"  # ⚠️ CHANGE THIS to your Gmail App Password

# Authorization Recipients
# ⚠️ CHANGE THESE to actual recipient emails
AUTHORIZED_RECIPIENTS = [
    "gobinath.t67@gmail.com",
]

# Email Settings
ENABLE_EMAIL_ALERTS = True
EMAIL_COOLDOWN = 60  # Minimum seconds between emails (to avoid spam)

# Email Templates
ATTACK_SUBJECT = "🚨 CRITICAL: IoT Security Attack Detected - Medical System"

ATTACK_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
.header {{ background: #d32f2f; color: white; padding: 20px; text-align: center; }}
.content {{ padding: 20px; background: #f5f5f5; }}
.alert-box {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }}
.details {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
.footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background: #f0f0f0; font-weight: bold; }}
</style>
</head>
<body>
<div class="header">
<h1>🚨 SECURITY ALERT: IoT Attack Detected</h1>
<p>Medical IoT Intrusion Detection System</p>
</div>

<div class="content">
<div class="alert-box">
<strong>⚠️ IMMEDIATE ACTION REQUIRED</strong><br>
An attack has been detected on the Medical IoT Network.
</div>

<div class="details">
<h2>Attack Summary</h2>
<table>
<tr><th>Attack Type</th><td>{attack_type}</td></tr>
<tr><th>Detection Time</th><td>{detection_time}</td></tr>
<tr><th>Duration</th><td>{duration} seconds</td></tr>
<tr><th>Affected Sensors</th><td>{sensors}</td></tr>
<tr><th>Total Packets</th><td>{packets}</td></tr>
</table>
</div>

<div class="details">
<h2>Attack Details</h2>
<ul>
{attack_description}
</ul>
</div>

</div>

<div class="footer">
<p>This is an automated alert from Medical IoT IDS</p>
</div>
</body>
</html>
"""
ATTACK_DESCRIPTIONS = {
    "MITM / Manipulation": """
        <li>Man-in-the-Middle attack detected</li>
        <li>Sensor values were abnormally manipulated</li>
        <li>Possible intercepted and altered data transmission</li>
    """,

    "Spoofing": """
        <li>Sensor identity or data spoofing detected</li>
        <li>Invalid sensor type or out-of-range values</li>
        <li>Possible malicious device impersonation</li>
    """,

    "Jamming": """
        <li>Signal jamming or denial of service detected</li>
        <li>Zero or invalid sensor values received</li>
        <li>Possible sensor communication disruption</li>
    """
}
