import requests
import json

url = "http://127.0.0.1:8000/api/v1/auth/guest-login"
payload = {"device_id": "debug_device_001"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
