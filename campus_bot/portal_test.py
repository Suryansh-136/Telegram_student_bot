import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()


# =========================================
# Custom Exceptions
# =========================================

class PortalError(Exception):
    """Base exception for portal errors."""


class PortalTimeoutError(PortalError):
    """Raised when the portal request times out."""


class PortalConnectionError(PortalError):
    """Raised when connection to the portal fails."""


class PortalHTTPError(PortalError):
    """Raised when the portal returns an HTTP error."""


# =========================================
# Get Portal Attendance
# =========================================

def get_portal_attendance(username, password, month):

    session = requests.Session()

    try:

        # -----------------------------
        # Open Login Page
        # -----------------------------

        login_page_url = (
            "https://cportal.siet.in/indexLogin.php"
        )

        login_page_response = session.get(
            login_page_url,
            timeout=(5, 30)
        )

        login_page_response.raise_for_status()


        # -----------------------------
        # Login
        # -----------------------------

        login_url = (
            "https://cportal.siet.in/getdata/execute.php"
        )

        login_payload = {
            "login_id": username,
            "pass_wd": password,
            "isCaptcha": "false"
        }

        login_response = session.post(
            login_url,
            data=login_payload,
            timeout=(5, 30)
        )

        login_response.raise_for_status()


        # -----------------------------
        # Get Attendance
        # -----------------------------

        attendance_url = (
            "https://cportal.siet.in/"
            "studentnew/students/attendance_class_step1"
        )

        attendance_payload = {
            "months_01": month
        }

        attendance_response = session.post(
            attendance_url,
            data=attendance_payload,
            timeout=(5, 30)
        )

        attendance_response.raise_for_status()


        # -----------------------------
        # Parse HTML
        # -----------------------------

        soup = BeautifulSoup(
            attendance_response.text,
            "html.parser"
        )


        # -----------------------------
        # Extract Attendance
        # -----------------------------

        tables = soup.find_all("table")

        attendance_data = []

        if tables:

            table = tables[0]

            rows = table.find_all("tr")

            for row in rows[1:]:

                cells = row.find_all(
                    ["th", "td"]
                )

                data = [
                    cell.get_text(
                        " ",
                        strip=True
                    )
                    for cell in cells
                ]

                if not data:
                    continue

                subject_code = data[0]

                if subject_code == "GRAND TOTAL":
                    continue

                if len(data) < 5:
                    continue

                attendance_data.append({
                    "subject": subject_code,
                    "present": data[-4],
                    "leave": data[-3],
                    "absent": data[-2],
                    "percentage": data[-1]
                })


        # -----------------------------
        # Extract Subject Mapping
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
        # Combine Data
        # -----------------------------

        for record in attendance_data:

            code = record["subject"]

            record["subject_name"] = (
                subject_mapping.get(
                    code,
                    code
                )
            )


        return attendance_data


    # =================================
    # Timeout
    # =================================

    except requests.Timeout as exc:

        raise PortalTimeoutError(
            "Portal request timed out."
        ) from exc


    # =================================
    # Connection Error
    # =================================

    except requests.ConnectionError as exc:

        raise PortalConnectionError(
            "Could not connect to the portal."
        ) from exc


    # =================================
    # HTTP Error
    # =================================

    except requests.HTTPError as exc:

        raise PortalHTTPError(
            f"Portal returned HTTP "
            f"{exc.response.status_code}."
        ) from exc


    # =================================
    # Unexpected Error
    # =================================

    except Exception as exc:

        raise PortalError(
            "Unexpected portal error."
        ) from exc


    # =================================
    # Always Close Session
    # =================================

    finally:

        session.close()


# =========================================
# Testing
# =========================================

if __name__ == "__main__":

    username = os.getenv(
        "PORTAL_USERNAME"
    )

    password = os.getenv(
        "PORTAL_PASSWORD"
    )

    print(
        "Testing portal attendance..."
    )

    try:

        attendance = get_portal_attendance(
            username,
            password,
            "07"
        )

        print("\nAttendance:\n")

        for record in attendance:

            print(
                f"📘 {record['subject_name']}"
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


    except PortalTimeoutError as error:

        print(
            "⚠️ Timeout Error:",
            error
        )


    except PortalConnectionError as error:

        print(
            "⚠️ Connection Error:",
            error
        )


    except PortalHTTPError as error:

        print(
            "⚠️ HTTP Error:",
            error
        )


    except PortalError as error:

        print(
            "❌ Portal Error:",
            error
        )