import requests

# email = input("Entre email : ")
# password = input("Entre password: ")
# data = {
#     "email": email,
#     "password": password
# }
# login_response = requests.post("http://127.0.0.1:5000/api/v1/auth/login", json=data).text
# print(login_response)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczNjk3NjgyNCwianRpIjoiZmQ1OTY4MDEtZGM2OC00ZTlkLWIzMDQtNDgzMTJkYzY3OTdiIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IkE4VFNRNEdBVTZHNTlPQUtJUklCIiwibmJmIjoxNzM2OTc2ODI0LCJjc3JmIjoiNGZmODJiNzctNDEzOS00Y2MyLWEyNjQtNDE4ZWQ4Nzk3ODUwIiwiZXhwIjoxNzM5NTY4ODI0fQ.4DTqBFa3KZXO0fIHdzD0IL5uvhLw7Ya987aLLLs5A1o"
headers = {
    "Authorization": f"Bearer {token}"
}
url = f"http://127.0.0.1:5000/api/v1/auth/myticket"

payload = {
    'doctor_id': 1
}
ticket_response = requests.get(url, headers=headers).text
print(ticket_response)
