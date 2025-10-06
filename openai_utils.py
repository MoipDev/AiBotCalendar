import os
from datetime import datetime
import requests
import json
import re

def parse_user_message(text):
    prompt = (
        f"Analiza este mensaje y extrae los datos de la cita en formato JSON. "
        f"Interpreta expresiones de tiempo como 'mañana', 'el próximo jueves', 'el 17 de mayo', etc. "
        f"Convierte horas como 'cinco y media', 'diez de la mañana', '17:30', etc. "
        f"Si no es una cita, devuelve SOLO la palabra NONE. "
        f"Reglas:"
        f"- La fecha debe convertirse a formato YYYY-MM-DD\n"
        f"- La hora debe convertirse a formato HH:MM (24 horas)\n"
        f"- Si dice 'mañana', calcula la fecha correcta\n"
        f"- Si solo menciona el día, usa el mes actual o siguiente según corresponda\n"
        f"- Si no especifica el año, usa el actual\n"
        f"Formato esperado: {{\"title\": \"...\", \"date\": \"2025-05-13\", \"time\": \"10:30\", \"notes\": \"...\"}}\n\n"
        f"Fecha actual: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"Mensaje: {text}"
    )

    API = os.getenv("API_KEY")
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "prompt": prompt,
                "stream": False
            }
        )
    except Exception as e:
        print(f"❌ Error al consultar Ollama: {e}")
        return "Lo siento, hubo un error al procesar tu mensaje."

    result = response.json()
    respuesta = result.get("response", "")

    # Si el modelo dice explícitamente que no es cita
    if "NONE" in respuesta:
        return None

    match = re.search(r'\{.*?\}', respuesta, re.DOTALL)
    if not match:
        return None  # 👈 Antes devolvías {}, ahora None

    try:
        json_data = json.loads(match.group(0))
        datetime.strptime(f"{json_data['date']}T{json_data['time']}:00", "%Y-%m-%dT%H:%M:%S")
        return json_data
    except (json.JSONDecodeError, ValueError, KeyError):
        return None  # 👈 Antes devolvías {}, ahora None

