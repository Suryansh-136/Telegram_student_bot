import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv


# -----------------------------
# Load Environment Variables
# -----------------------------

load_dotenv()

username = os.getenv("PORTAL_USERNAME")
password = os.getenv("PORTAL_PASSWORD")


# -----------------------------
# Create Session
# -----------------------------

session = requests.Session()


# -----------------------------
# Step 1: Open Login Page
# -----------------------------

login_page_url = "https://cportal.siet.in/indexLogin.php"

response = session.get(login_page_url)

print("Login page status:", response.status_code)


# -----------------------------
# Step 2: Login
# -----------------------------

login_url = "https://cportal.siet.in/getdata/execute.php"

login_payload = {
    "login_id": username,
    "pass_wd": password,
    "isCaptcha": "false"
}

response = session.post(
    login_url,
    data=login_payload
)

print("Login status:", response.status_code)


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

print("Attendance status:", attendance_response.status_code)


# -----------------------------
# Step 4: Parse HTML
# -----------------------------

soup = BeautifulSoup(
    attendance_response.text,
    "html.parser"
)


# -----------------------------
# Step 5: Extract Attendance
# -----------------------------

tables = soup.find_all("table")

attendance_data = []

if tables:

    table = tables[0]

    rows = table.find_all("tr")

    for row in rows[1:]:

        cells = row.find_all(["th", "td"])

        data = [
            cell.get_text(" ", strip=True)
            for cell in cells
        ]

        if not data:
            continue

        subject_code = data[0]

        # Skip grand total row
        if subject_code == "GRAND TOTAL":
            continue

        attendance_data.append({
            "subject": subject_code,
            "present": data[-4],
            "leave": data[-3],
            "absent": data[-2],
            "percentage": data[-1]
        })


# -----------------------------
# Step 6: Extract Subject Mapping
# -----------------------------

subject_mapping = {}

subject_breakdown = soup.find(
    string=lambda text:
        text and "Subject Breakdown" in text
)

if subject_breakdown:

    breakdown_container = (
        subject_breakdown.parent.parent
    )

    items = breakdown_container.find_all(
        "div",
        class_="flex"
    )

    for item in items:

        spans = item.find_all("span")

        if len(spans) >= 2:

            code = spans[0].get_text(
                strip=True
            )

            name = spans[1].get_text(
                strip=True
            )

            subject_mapping[code] = name


# -----------------------------
# Step 7: Combine Data
# -----------------------------

for record in attendance_data:

    code = record["subject"]

    record["subject_name"] = subject_mapping.get(
        code,
        code
    )


# -----------------------------
# Step 8: Display Result
# -----------------------------

print("\nAttendance:")

for record in attendance_data:

    print(
        f"{record['subject_name']} "
        f"({record['subject']})"
    )

    print(
        f"Present: {record['present']}"
    )

    print(
        f"Leave: {record['leave']}"
    )

    print(
        f"Absent: {record['absent']}"
    )

    print(
        f"Percentage: {record['percentage']}"
    )

    print()