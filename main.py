import yaml
import time
import threading
import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from pymodbus.client import ModbusTcpClient
import paho.mqtt.client as mqtt

# Load Config

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

parameters = config["parameters"]
email_config = config["email"]

# Email Sender

def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_config["username"]
    msg["To"] = ", ".join(email_config["recipients"])

    try:
        with smtplib.SMTP(email_config["smtp_server"], email_config["port"]) as server:
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.sendmail(email_config["username"], email_config["recipients"], msg.as_string())
        print(f"[{datetime.now()}] ✅ Email sent: {subject}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Email failed: {e}")

# Logger

def log_event(msg):
    line = f"[{datetime.now()}] {msg}"
    print(line)
    with open("alerts.log", "a") as f:
        f.write(line + "\n")

# Threshold Checker

def check_threshold(param, value, source="unknown"):
    name = param["name"]
    if value < param["min"]:
        alert_msg = f"{name}: {value} BELOW MIN {param['min']}"
        log_event(alert_msg)
        send_email(f"🔴 ALERT: {name} LOW [{value}] – threshold: {param['min']}", alert_msg)

    elif value > param["max"]:
        alert_msg = f"{name}: {value} ABOVE MAX {param['max']}"
        log_event(alert_msg)
        send_email(f"🔴 ALERT: {name} HIGH [{value}] – threshold: {param['max']}", alert_msg)

    else:
        log_event(f"{name}: {value} NORMAL")

# Modbus Handler

def slave_modbus(param):
    client = ModbusTcpClient("localhost", port=502)  # simulator/device must run here
    client.connect()

    while True:
        rr = client.read_holding_registers(param["register"] - 40001, count=1)
        if rr.isError():
            log_event(f"Error reading register {param['register']}")
        else:
            value = rr.registers[0]
            check_threshold(param, value, source=f"Modbus {param['register']}")
        time.sleep(param["interval"])

# MQTT Listener

def mqtt_listener(param):

    def on_connect(client, userdata, flags, rc,properties = None):
        print("Connected with result code: ",rc)
        client.subscribe(param["topic"])

    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            print(payload)
            try:
                data = json.loads(payload)   # JSON format
                value = float(data.get("value", 0))
            except json.JSONDecodeError:
                value = float(payload)       # plain number
            check_threshold(param, value, source=param["topic"])
        except Exception as e:
            log_event(f"MQTT Parsing error: {e}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("broker.hivemq.com", port=1883, keepalive=60)
    client.subscribe(param["topic"])

    log_event(f"Subscribed to MQTT topic: {param['topic']}")
    client.loop_forever()

# Thread Manager

threads = []
for param in parameters:
    if param["protocol"] == "modbus":
        t = threading.Thread(target=slave_modbus, args=(param,))
        t.start()
        threads.append(t)
    elif param["protocol"] == "mqtt":
        t = threading.Thread(target=mqtt_listener, args=(param,))
        t.start()
        threads.append(t)

for t in threads:
    t.join()
