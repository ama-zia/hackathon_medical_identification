# app.py
import os
import tempfile
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session, redirect
from dotenv import load_dotenv
load_dotenv()
import pytz

from gemini_client import generate_medication_summary
from ocr_utils import allowed_file, extract_text_from_image
from calendar_utils import start_oauth_flow, fetch_credentials_from_authorization_response, insert_event_to_calendar, get_user_info
from google.oauth2.credentials import Credentials


app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_me")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
DEFAULT_TZ = os.environ.get("TZ", "Europe/London")

# Simple in-memory demo store for user credentials (DO NOT use in production)
# key: session id (Flask session), value: credentials JSON
# For demo hackathon this is fine. In real app use DB and encrypt.
# We'll store credentials in Flask session (serialized).
# session cookie is signed using app.secret_key.
# session keys: session['credentials']
# NOTE: Flask session persists only for this browser.

@app.route("/")
def index():
    """
    Minimal health/info endpoint. Frontend will serve UI separately.
    """
    return jsonify({"app": "Simple Meds backend", "description": "Medication explanation + calendar reminders (demo)"})


@app.route("/api/explain", methods=["POST"])
def explain_medication():
    """
    Accepts:
    - JSON: { "text": "<typed prescription or medicine name>" }
    OR
    - multipart/form-data with file 'image'
    Returns structured JSON for frontend cards:
    { purpose, side_effects, warnings, usage, disclaimer, raw? }
    """
    raw_text = ""
    if "image" in request.files:
        f = request.files["image"]
        if f.filename == "" or not allowed_file(f.filename):
            return jsonify({"error": "invalid image file"}), 400
        tmpdir = tempfile.gettempdir()
        path = os.path.join(tmpdir, f.filename)
        f.save(path)
        raw_text = extract_text_from_image(path)
    else:
        data = request.get_json(silent=True) or request.form
        raw_text = (data.get("text") or "").strip()

    if not raw_text:
        return jsonify({"error": "no text or image provided"}), 400

    result = generate_medication_summary(raw_text)
    # Add a front-facing disclaimer key if needed
    result.setdefault("disclaimer", "This is not medical advice. Consult a clinician.")
    return jsonify(result)


@app.route("/api/start-calendar-auth", methods=["GET"])
def start_calendar_auth():
    """
    Frontend can request this to start OAuth.
    Optional query param 'state' should be JSON-encoded scheduling payload,
    e.g. {"med_name":"Metformin","times":["08:00","20:00"], "start_date":"2026-02-23","duration_days":30,"dose_note":"500mg"}
    """
    state = request.args.get("state")
    auth_url, state = start_oauth_flow(state=state)
    return jsonify({"auth_url": auth_url, "state": state})


@app.route("/oauth2callback", methods=["GET"])
def oauth2callback():
    """
    Google redirects here after consent. We fetch credentials, store them in session,
    and if 'state' was provided, we will schedule the events.
    """
    full_url = request.url
    creds = fetch_credentials_from_authorization_response(full_url)
    # serialize credentials into session
    session["credentials"] = creds.to_json()
    # optionally get email/name and return HTML response
    try:
        info = get_user_info(creds)
        email = info.get("email")
    except Exception:
        email = None

    # If state exists and is a JSON string, schedule events now
    state = request.args.get("state")
    if state:
        try:
            payload = json.loads(state)
            schedule_events_from_payload(creds, payload)
        except Exception:
            pass

    return f"""
<html><body>
<h3>Authentication successful.</h3>
<p>You can close this window and return to the app.</p>
<p>User email: {email or 'unknown'}</p>
</body></html>
"""


def schedule_events_from_payload(creds: Credentials, payload: dict):
    """
    Create calendar events for times and duration specified.
    payload example:
    {
      "med_name": "Metformin",
      "times": ["08:00","20:00"],
      "start_date": "2026-02-23",
      "duration_days": 30,
      "timezone": "Europe/London",
      "dose_note": "500mg with food"
    }
    """
    tz_name = payload.get("timezone", DEFAULT_TZ)
    tz = pytz.timezone(tz_name)
    start_date = datetime.fromisoformat(payload.get("start_date"))
    days = int(payload.get("duration_days", 7))
    med_name = payload.get("med_name", "Medication")
    times = payload.get("times", ["09:00"])

    for day_offset in range(days):
        day = start_date + timedelta(days=day_offset)
        for t in times:
            try:
                h, m = [int(x) for x in t.split(":")]
            except Exception:
                # skip bad time format
                continue
            start_dt = tz.localize(datetime(day.year, day.month, day.day, h, m))
            end_dt = start_dt + timedelta(minutes=10)
            summary = f"Take {med_name}"
            description = payload.get("dose_note", "")
            insert_event_to_calendar(creds, summary, description, start_dt, end_dt, reminders_minutes=30)


@app.route("/api/schedule", methods=["POST"])
def api_schedule():
    """
    Frontend posts scheduling payload:
    {
      "med_name":"Metformin",
      "times":["08:00","20:00"],
      "start_date":"2026-02-23",
      "duration_days":30,
      "dose_note":"500mg with food"
    }
    - If user already authorized (session has credentials), schedule immediately.
    - Else, return auth_url so frontend can open it, with the payload in 'state' to be processed after consent.
    """
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "missing payload"}), 400

    creds_json = session.get("credentials")
    if creds_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(creds_json))
            schedule_events_from_payload(creds, payload)
            return jsonify({"status": "scheduled_in_calendar"})
        except Exception as e:
            return jsonify({"error": "failed_to_schedule", "details": str(e)}), 500
    else:
        # Need auth: return auth_url. Put payload JSON into state.
        state = json.dumps(payload)
        auth_url, state_ret = start_oauth_flow(state=state)
        return jsonify({"need_auth": True, "auth_url": auth_url})


@app.route("/api/userinfo", methods=["GET"])
def api_userinfo():
    """
    Returns basic user email if authorized (from session credentials).
    Frontend can call this to show user email in the UI.
    """
    creds_json = session.get("credentials")
    if not creds_json:
        return jsonify({"authorized": False})
    try:
        creds = Credentials.from_authorized_user_info(json.loads(creds_json))
        info = get_user_info(creds)
        return jsonify({"authorized": True, "email": info.get("email"), "name": info.get("name")})
    except Exception as e:
        return jsonify({"authorized": False, "error": str(e)})


if __name__ == "__main__":
    # For hackathon local dev
    app.run(host="0.0.0.0", port=5000, debug=True)