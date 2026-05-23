import requests
import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import os
import pandas as pd

TOKEN_FILE = "token.txt"
URL = "https://www.waze.com/live-map/api/georss"
def get_params():
    """
    Load map coordinates from settings.txt
    """

    settings = {}

    try:

        with open(
            "settings.txt",
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if "=" in line:

                    key, value = line.split("=")

                    settings[key.strip()] = value.strip()

    except Exception as e:

        print(f"Error loading settings: {e}")

    return {
        "top": float(settings.get("top", 31.695213052630276)),
        "bottom": float(settings.get("bottom", 31.578935830814277)),
        "left": float(settings.get("left", -8.0548152923584)),
        "right": float(settings.get("right", -7.900938034057618)),
        "env": "row",
        "types": "alerts,traffic"
    }

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer":        "https://www.waze.com/live-map",
    "Origin":         "https://www.waze.com",
    "Accept":         "application/json, text/plain, */*",
    "Accept-Language":"fr-FR,fr;q=0.9",
    "Accept-Encoding":"gzip, deflate, br",
    "Connection":     "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}
# ─── Helpers ──────────────────────────────────────────────────────────────

 #-------------------------- read  file and tocken ---------------

def read_token():
    """
        Read token from token.txt
        """

    try:
            # Check file exists
        if not os.path.exists(TOKEN_FILE):
            print("Token file not found.")
            return None

            # Read token
        with open(TOKEN_FILE, "r") as file:
            token = file.read().strip()

            # Check empty token
        if not token:
            print("Token file is empty.")
            return None

        return token

    except Exception as e:
        print(f"Error reading token: {e}")
        return None

    #------------------------------ get tocken from waze website ---------
def intercept_request(request):
    token = request.headers.get("x-recaptcha-token")

    if token:
        print(f"Found token: {token}")

        with open("token.txt", "w") as file:
            file.write(token)


def collect_waze_token():
    """
        Open Waze and intercept requests
        to get x-recaptcha-token.
        """

    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(
                    headless=False
                )

            page = browser.new_page()

            # Listen to all requests
            page.on(
                    "request",
                    intercept_request
                )

                # Open Waze
            page.goto(
                    "https://www.waze.com",
                    wait_until="networkidle"
                )

                # Wait for requests
            page.wait_for_timeout(10000)

            browser.close()

            return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    
def ms_to_datetime(ms):
    """Convert milliseconds timestamp to readable datetime."""
    if not ms:
        return None, None

    dt = datetime.fromtimestamp(
        ms / 1000,
        tz=timezone.utc
    ).astimezone()

    return (
        dt.strftime("%Y-%m-%d"),
        dt.strftime("%H:%M:%S")
    )


def calc_age_minutes(pub_ms):
    """Calculate age in minutes."""
    if not pub_ms:
        return None

    now_ms = datetime.now().timestamp() * 1000

    return round(
        (now_ms - pub_ms) / 60000,
        2
    )

def fetch(retry=True):
    session = requests.Session()
    token = read_token()
    # Add token only if exists
    if token:
        HEADERS["x-recaptcha-token"] = token

    try:
        # Load Waze page first
        session.get(
            "https://www.waze.com/live-map",
            headers=HEADERS,
            timeout=15
        )

        # Call API
        resp = session.get(
            URL,
            params=get_params(),
            headers=HEADERS,
            timeout=15
        )

        # Check forbidden error
        if resp.status_code == 403:

            print("403 Forbidden → Token expired or invalid.")
            
            # Avoid infinite loop
            if retry:
                print("Collecting new token...")

                collect_waze_token()

                print("Retrying request...")

                return fetch(retry=False)

            else:
                raise Exception(
                    "403 Forbidden even after refreshing token."
                )

        resp.raise_for_status()

        return resp.json()

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

# --------------------------------------------------------
# Extract Alerts
# --------------------------------------------------------

def extract_alerts_table(data):
    """
    Extract alerts from Waze JSON
    into a pandas DataFrame.
    """

    rows = []

    alerts = data.get("alerts", [])

    for alert in alerts:

        pub_ms = alert.get("pubMillis")

        date, time = ms_to_datetime(pub_ms)

        row = {
            "id": alert.get("id"),
            "type": alert.get("type"),
            "subtype": alert.get("subtype"),
            "street": alert.get("street"),

            "latitude":
                alert.get("location", {}).get("y"),

            "longitude":
                alert.get("location", {}).get("x"),

            "n_comments":
                alert.get("nComments", 0),

            "n_thumbs_up":
                alert.get("nThumbsUp", 0),

            "report_by":
                alert.get("reportBy"),

            "report_description":
                alert.get("reportDescription"),

            "pub_millis":
                pub_ms,

            "date":
                date,

            "time":
                time,

            "age_minutes":
                calc_age_minutes(pub_ms)
        }

        rows.append(row)

    return pd.DataFrame(rows)


# --------------------------------------------------------
# Extract Jams
# --------------------------------------------------------

def extract_jams_table(data):
    """
    Extract jams from Waze JSON
    into a pandas DataFrame.
    """

    rows = []

    jams = data.get("jams", [])

    for jam in jams:

        update_ms = jam.get("updateMillis")

        date, time = ms_to_datetime(update_ms)

        cause = jam.get("causeAlert", {})

        start_location = None

        if jam.get("line"):
            start_location = jam["line"][0]

        row = {
            "id": jam.get("id"),

            "street":
                jam.get("street"),

            "city":
                jam.get("city"),

            "level":
                jam.get("level"),

            "length_m":
                jam.get("length"),

            "speed":
                jam.get("speed"),

            "end_node":
                jam.get("endNode"),

            "latitude":
                start_location.get("y")
                if start_location else None,

            "longitude":
                start_location.get("x")
                if start_location else None,

            # Cause alert info
            "cause_type":
                cause.get("type"),

            "cause_subtype":
                cause.get("subtype"),

            "report_by":
                cause.get("reportBy"),

            "country":
                cause.get("country"),

            "confidence":
                cause.get("confidence"),

            "reliability":
                cause.get("reliability"),

            "update_millis":
                update_ms,

            "date":
                date,

            "time":
                time
        }

        rows.append(row)

    return pd.DataFrame(rows)

