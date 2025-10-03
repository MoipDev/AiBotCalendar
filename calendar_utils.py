import os
import pickle

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request  # Añadir esta importación


SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]


def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)
def create_event(title, date, time, notes=""):
    service = get_calendar_service()

    start_datetime = f"{date}T{time}:00"
    end_datetime = (datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)).isoformat()

    event = {
        'summary': title,
        'description': notes,
        'start': {'dateTime': start_datetime, 'timeZone': 'Europe/Madrid'},
        'end': {'dateTime': end_datetime, 'timeZone': 'Europe/Madrid'},
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')
