import requests

BASE_URL = "http://127.0.0.1:5000/api/v1/auth"

login_data = {
    "email": "0699999999",
    "password": "imadkm20062"
}
login_response = requests.post(f"{BASE_URL}/doctor/login", json=login_data)
access_token = login_response.json().get("access_token")

headers = {
    "Authorization": f"Bearer {access_token}"
}

feedback_response = requests.get(f"{BASE_URL}/doctor/3", headers=headers)
print(feedback_response.status_code)
print(feedback_response.json())
input()
