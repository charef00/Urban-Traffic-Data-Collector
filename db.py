import mysql.connector
import json
from datetime import datetime, timezone


# ----------------------------------------------------
# Database connection
# ----------------------------------------------------

def connect_db():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="waze_db"
    )


# ----------------------------------------------------
# Helpers
# ----------------------------------------------------

def ms_to_datetime(ms):
    """Convert milliseconds to MySQL datetime."""

    if not ms:
        return None

    return datetime.fromtimestamp(
        ms / 1000,
        tz=timezone.utc
    ).astimezone()


def calc_age_minutes(ms):
    """Calculate age in minutes."""

    if not ms:
        return None

    now_ms = datetime.now().timestamp() * 1000

    return round(
        (now_ms - ms) / 60000,
        2
    )


# ----------------------------------------------------
# SAVE ALERTS
# ----------------------------------------------------

def save_alerts(data):

    conn = connect_db()
    cursor = conn.cursor()

    query = """
    INSERT INTO alerts (

        id,
        type,
        subtype,
        street,

        latitude,
        longitude,

        n_comments,
        n_thumbs_up,

        comments,

        report_description,
        report_by,

        pub_millis,
        pub_datetime,
        age_minutes,

        raw_json

    )

    VALUES (
        %s,%s,%s,%s,
        %s,%s,
        %s,%s,
        %s,
        %s,%s,
        %s,%s,%s,
        %s
    )

    ON DUPLICATE KEY UPDATE

        -- dynamic fields only
        n_comments = VALUES(n_comments),
        n_thumbs_up = VALUES(n_thumbs_up),

        comments = VALUES(comments),

        pub_millis = VALUES(pub_millis),
        pub_datetime = VALUES(pub_datetime),

        age_minutes = VALUES(age_minutes),

        raw_json = VALUES(raw_json)
    """

    alerts = data.get("alerts", [])

    for alert in alerts:

        location = alert.get("location", {})

        pub_ms = alert.get("pubMillis")

        values = (

            alert.get("id"),
            alert.get("type"),
            alert.get("subtype"),
            alert.get("street"),

            location.get("y"),
            location.get("x"),

            alert.get("nComments", 0),
            alert.get("nThumbsUp", 0),

            json.dumps(
                alert.get("comments", []),
                ensure_ascii=False
            ),

            alert.get("reportDescription"),
            alert.get("reportBy"),

            pub_ms,
            ms_to_datetime(pub_ms),
            calc_age_minutes(pub_ms),

            json.dumps(
                alert,
                ensure_ascii=False
            )
        )

        cursor.execute(query, values)

    conn.commit()

    cursor.close()
    conn.close()


# ----------------------------------------------------
# SAVE JAMS
# ----------------------------------------------------

def save_jams(data):

    conn = connect_db()
    cursor = conn.cursor()

    query = """
    INSERT INTO jams (

        id,

        street,
        city,

        level,
        length,
        speed,

        end_node,

        latitude,
        longitude,

        update_millis,
        update_datetime,
        age_minutes,

        line,
        segments,

        cause_alert,

        cause_type,
        cause_subtype,
        report_by,

        confidence,
        reliability,

        raw_json

    )

    VALUES (
        %s,
        %s,%s,
        %s,%s,%s,
        %s,
        %s,%s,
        %s,%s,%s,
        %s,%s,
        %s,
        %s,%s,%s,
        %s,%s,
        %s
    )

    ON DUPLICATE KEY UPDATE

        -- dynamic fields only
        level = VALUES(level),
        length = VALUES(length),
        speed = VALUES(speed),

        update_millis = VALUES(update_millis),
        update_datetime = VALUES(update_datetime),

        age_minutes = VALUES(age_minutes),

        line = VALUES(line),
        segments = VALUES(segments),

        cause_alert = VALUES(cause_alert),

        confidence = VALUES(confidence),
        reliability = VALUES(reliability),

        raw_json = VALUES(raw_json)
    """

    jams = data.get("jams", [])

    for jam in jams:

        update_ms = jam.get("updateMillis")

        first_point = None

        if jam.get("line"):
            first_point = jam["line"][0]

        cause = jam.get("causeAlert", {})

        values = (

            jam.get("id"),

            jam.get("street"),
            jam.get("city"),

            jam.get("level"),
            jam.get("length"),
            jam.get("speed"),

            jam.get("endNode"),

            first_point.get("y")
            if first_point else None,

            first_point.get("x")
            if first_point else None,

            update_ms,
            ms_to_datetime(update_ms),
            calc_age_minutes(update_ms),

            json.dumps(
                jam.get("line", []),
                ensure_ascii=False
            ),

            json.dumps(
                jam.get("segments", []),
                ensure_ascii=False
            ),

            json.dumps(
                cause,
                ensure_ascii=False
            ),

            cause.get("type"),
            cause.get("subtype"),
            cause.get("reportBy"),

            cause.get("confidence"),
            cause.get("reliability"),

            json.dumps(
                jam,
                ensure_ascii=False
            )
        )

        cursor.execute(query, values)

    conn.commit()

    cursor.close()
    conn.close()


