import json
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.readonly'
]

def get_calendar_service():
    creds = None

    # 🔹 Intentar cargar token guardado (si existe)
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 🔹 Si no hay token válido, crear desde variable de entorno
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_json = os.getenv("GOOGLE_CREDENTIALS")
            if not creds_json:
                raise Exception("❌ No se encontró GOOGLE_CREDENTIALS en las variables de entorno.")

            # Cargar credenciales desde el JSON en variable de entorno
            creds_data = json.loads(creds_json)

            # Si tus credenciales son de tipo "installed"
            flow = InstalledAppFlow.from_client_config(creds_data, SCOPES)
            creds = flow.run_console()  # ⚠️ Solo la primera vez, luego se guarda token.pickle

        # Guardar token.pickle para no volver a pedir autenticación
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
