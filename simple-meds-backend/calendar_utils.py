# calendar_utils.py
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import url_for
from datetime import datetime, timedelta
import pytz

SCOPES = ["https://www.googleapis.com/auth/calendar.events", "openid", "email", "profile"]

CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

if not CLIENT_SECRETS_FILE:
    raise RuntimeError("Set GOOGLE_CLIENT_SECRETS_FILE environment variable to your downloaded client_secret.json")


def start_oauth_flow(state: str = None):
    """
    Return (auth_url, state) where state is a string.
    """
    redirect_uri = f"{BASE_URL}/oauth2callback"
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    auth_url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent", state=state)
    return auth_url, state


def fetch_credentials_from_authorization_response(full_request_url: str):
    redirect_uri = f"{BASE_URL}/oauth2callback"
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    flow.fetch_token(authorization_response=full_request_url)
    creds = flow.credentials
    return creds


def insert_event_to_calendar(creds: Credentials, summary: str, description: str, start_dt: datetime, end_dt: datetime, reminders_minutes: int = 30):
    """
    Insert event into user's primary calendar. start_dt and end_dt must be timezone-aware.
    Returns the created event dict.
    """
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": reminders_minutes}
            ],
        }
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return created


def get_user_info(creds: Credentials):
    """
    Return user's basic info (email, name) using the OAuth2 API.
    """
    service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
    info = service.userinfo().get().execute()
    # info includes 'email', 'name', etc.
    return info