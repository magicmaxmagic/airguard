import requests
from datetime import datetime
import random

API_URL = "http://127.0.0.1:8000/events/"

def send_fake_event():
    value = round(random.uniform(40, 90), 2)
    event = {
        "device_id": "TEST-PC",
        "type": "noise",
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    }
    r = requests.post(API_URL, json=event)
    print(f"Sent: {value} dB → Response {r.status_code}")

if __name__ == "__main__":
    print("=== AirGuard Backend Insert Test ===")
    for i in range(5):
        send_fake_event()