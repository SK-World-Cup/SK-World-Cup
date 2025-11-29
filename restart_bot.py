import os
import requests

# Get the API key and service ID from environment variables
API_KEY = os.environ.get("API_KEY")  # your Render API key
SERVICE_ID = os.environ.get("SERVICE_ID")  # the ID of your Render service

if not API_KEY or not SERVICE_ID:
    print("❌ Missing API_KEY or SERVICE_ID environment variable.")
    exit(1)

# Render restart endpoint
url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Trigger a deploy/restart
resp = requests.post(url, headers=headers)
if resp.status_code == 201:
    print("✅ Service restart triggered successfully!")
else:
    print(f"❌ Failed to restart service: {resp.status_code} {resp.text}")
