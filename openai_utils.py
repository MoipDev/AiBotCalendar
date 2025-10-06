import os
from datetime import datetime, timedelta
import requests
import json
import re

def parse_user_message(text):
    prompt = (
        f"Analiza este mensaje y extrae los datos de una cita en formato JSON. "
        f"Interpreta expresiones de tiempo como 'mañana', 'el próximo jueves', 'el 17 de mayo', etc. "
        f"Convierte horas como 'cinco y media', 'diez de la mañana', '17:30', etc. "
        f"Si no es una cita, responde SOLO con la palabra NONE. "
        f"Reglas:\n"
        f"- La fecha debe ser YYYY-MM-DD\n"
        f"- La hora debe ser HH:MM (24 horas)\n"
        f"- Si dice 'mañana', calcula la fecha correcta\n"
        f"- Si solo menciona el día, usa el mes actual o el siguiente según corresponda\n"
        f"- Si no especifica el año, usa el actual\n"
        f"- Incluye un campo opcional 'notes' si hay información adicional\n\n"
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
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "Eres un asistente que extrae información estructurada de texto."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
        )
    except Exception as e:
        print(f"❌ Error al consultar Groq: {e}")
        return None

    result = response.json()
    print("📦 Respuesta Groq:", result)  # 👈 DEBUG opcional

    try:
        respuesta = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print("⚠️ Error al extraer contenido del modelo.")
        return None

    # Si el modelo dice explícitamente que no es una cita
    if "NONE" in respuesta:
        return None

    # Buscar el JSON dentro del texto devuelto
    match = re.search(r'\{.*?\}', respuesta, re.DOTALL)
    if not match:
        return None

    try:
        json_data = json.loads(match.group(0))

        # Validar formato de fecha y hora
        datetime.strptime(f"{json_data['date']}T{json_data['time']}:00", "%Y-%m-%dT%H:%M:%S")
        return json_data

    except (json.JSONDecodeError, ValueError, KeyError):
        print("⚠️ No se pudo parsear correctamente el JSON devuelto.")
        return None
