import requests
import logging

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from portal_session import portal_session_manager


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


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


class PortalLoginError(PortalError):
    """Raised when portal login fails."""


# =========================================
# Portal URLs
# =========================================

PORTAL_LOGIN_PAGE = (
    "https://cportal.siet.in/indexLogin.php"
)

PORTAL_LOGIN_URL = (
    "https://cportal.siet.in/getdata/execute.php"
)

PORTAL_ATTENDANCE_URL = (
    "https://cportal.siet.in/"
    "studentnew/students/attendance_class_step1"
)


# =========================================
# Login To Portal
# =========================================

def login_to_portal(username, password):

    if not username or not username.strip():
        raise PortalError(
            "Portal username is required."
        )

    if not password:
        raise PortalError(
            "Portal password is required."
        )

    session = requests.Session()

    try:

        # -----------------------------
        # Open Login Page
        # -----------------------------

        logger.info(
            "Opening portal login page"
        )

        login_page_response = session.get(
            PORTAL_LOGIN_PAGE,
            timeout=(5, 30)
        )

        login_page_response.raise_for_status()

        # -----------------------------
        # Login
        # -----------------------------

        logger.info(
            "Sending portal login request"
        )

        login_payload = {
            "login_id": username,
            "pass_wd": password,
            "isCaptcha": "false"
        }

        login_response = session.post(
            PORTAL_LOGIN_URL,
            data=login_payload,
            timeout=(5, 30)
        )

        logger.info(
            "Login response received: HTTP %s",
            login_response.status_code
        )

        login_response.raise_for_status()

        # -----------------------------
        # Store authenticated session
        # -----------------------------

        logger.info(
            "Portal login successful"
        )

        return session

    except requests.Timeout as exc:

        session.close()

        logger.error(
            "Portal login request timed out"
        )

        raise PortalTimeoutError(
            "Portal login request timed out."
        ) from exc

    except requests.ConnectionError as exc:

        session.close()

        logger.error(
            "Could not connect to portal"
        )

        raise PortalConnectionError(
            "Could not connect to the portal."
        ) from exc

    except requests.HTTPError as exc:

        session.close()

        logger.error(
            "Portal login returned HTTP %s",
            exc.response.status_code
        )

        raise PortalHTTPError(
            f"Portal returned HTTP "
            f"{exc.response.status_code}."
        ) from exc

    except Exception as exc:

        session.close()

        logger.exception(
            "Unexpected portal login error"
        )

        raise PortalError(
            "Unexpected portal login error."
        ) from exc


# =========================================
# Login And Store Session
# =========================================

def login_user(
    telegram_id,
    username,
    password
):

    session = login_to_portal(
        username,
        password
    )

    portal_session_manager.create_session(
        telegram_id,
        session
    )

    logger.info(
        "Portal session created for Telegram user %s",
        telegram_id
    )


# =========================================
# Get Portal Attendance
# =========================================

def get_portal_attendance(
    telegram_id,
    month
):

    # -----------------------------
    # Validate Month
    # -----------------------------

    if not month:
        raise PortalError(
            "Attendance month is required."
        )

    month = str(month).zfill(2)

    valid_months = {
        "01", "02", "03", "04",
        "05", "06", "07", "08",
        "09", "10", "11", "12"
    }

    if month not in valid_months:
        raise PortalError(
            "Invalid attendance month."
        )

    # -----------------------------
    # Get Existing Session
    # -----------------------------

    session = portal_session_manager.get_session(
        telegram_id
    )

    if session is None:

        raise PortalLoginError(
            "Portal session expired. Please login again."
        )

    try:

        # -----------------------------
        # Get Attendance
        # -----------------------------

        logger.info(
            "Requesting attendance for Telegram user %s",
            telegram_id
        )

        attendance_response = session.post(
            PORTAL_ATTENDANCE_URL,
            data={
                "months_01": month
            },
            timeout=(5, 30)
        )

        attendance_response.raise_for_status()

        logger.info(
            "Attendance response received: HTTP %s",
            attendance_response.status_code
        )

        if not attendance_response.text.strip():

            raise PortalError(
                "Portal returned an empty response."
            )

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

        if not tables:

            raise PortalError(
                "Attendance table not found in portal."
            )

        table = tables[0]

        rows = table.find_all("tr")

        if len(rows) < 2:

            raise PortalError(
                "Attendance table is empty."
            )

        attendance_data = []

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

        logger.info(
            "Attendance parsed successfully: %d records",
            len(attendance_data)
        )

        return attendance_data

    except requests.Timeout as exc:

        logger.error(
            "Attendance request timed out"
        )

        raise PortalTimeoutError(
            "Portal attendance request timed out."
        ) from exc

    except requests.ConnectionError as exc:

        logger.error(
            "Could not connect to portal"
        )

        raise PortalConnectionError(
            "Could not connect to the portal."
        ) from exc

    except requests.HTTPError as exc:

        logger.error(
            "Attendance request returned HTTP %s",
            exc.response.status_code
        )

        raise PortalHTTPError(
            f"Portal returned HTTP "
            f"{exc.response.status_code}."
        ) from exc

    except PortalError:

        raise

    except Exception as exc:

        logger.exception(
            "Unexpected attendance error"
        )

        raise PortalError(
            "Unexpected portal error."
        ) from exc