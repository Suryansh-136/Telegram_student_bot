from bs4 import BeautifulSoup
import os
import requests
from dotenv import load_dotenv

print("portal_test.py started")

load_dotenv()

username = os.getenv("PORTAL_USERNAME")
password = os.getenv("PORTAL_PASSWORD")

print("Environment loaded")
print("Username:", username)
print("Password loaded:", password is not None)


# 1. Session create
session = requests.Session()


# 2. Login page open
login_page_url = "https://cportal.siet.in/indexLogin.php"

response = session.get(login_page_url)

print("Login page status:", response.status_code)


# 3. Portal login
login_url = "https://cportal.siet.in/getdata/execute.php"

payload = {
    "login_id": username,
    "pass_wd": password,
    "isCaptcha": "false"
}

response = session.post(
    login_url,
    data=payload
)

print("Login status:", response.status_code)
print("Current URL:", response.url)


# 4. Check cookies
print("\nSession cookies:")

for cookie in session.cookies:
    print(cookie.name, "=", cookie.value)


# 5. Response preview
print("\nResponse preview:")
print(response.text[:500])


# -----------------------------
# Step 3: Get Attendance
# -----------------------------

attendance_url = (
    "https://cportal.siet.in/"
    "studentnew/students/attendance_class_step1"
)

attendance_payload = {
    "months_01": "07"
}

attendance_response = session.post(
    attendance_url,
    data=attendance_payload
)

print("\nAttendance status:", attendance_response.status_code)
print("Attendance URL:", attendance_response.url)

print("\nAttendance response preview:")
print(attendance_response.text[:1000])


# -----------------------------
# Step 4: Parse Attendance HTML
# -----------------------------

soup = BeautifulSoup(
    attendance_response.text,
    "html.parser"
)

tables = soup.find_all("table")

print("\nNumber of tables found:", len(tables))

for index, table in enumerate(tables, start=1):

    print(f"\n--- TABLE {index} ---")

    rows = table.find_all("tr")

    for row in rows:
        cells = row.find_all(["th", "td"])

        data = [
            cell.get_text(" ", strip=True)
            for cell in cells
        ]

        print(data)


# -----------------------------
# Step 5: Extract Attendance
# -----------------------------

table = tables[0]

rows = table.find_all("tr")

attendance_data = []

for row in rows[1:]:
    cells = row.find_all(["th", "td"])

    data = [
        cell.get_text(" ", strip=True)
        for cell in cells
    ]

    if not data:
        continue

    subject = data[0]

    # Skip grand total
    if subject == "GRAND TOTAL":
        continue

    attendance_data.append({
        "subject": subject,
        "present": data[-4],
        "leave": data[-3],
        "absent": data[-2],
        "percentage": data[-1]
    })


print("\nStructured Attendance:")

for record in attendance_data:
    print(record)