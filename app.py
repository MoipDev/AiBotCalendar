import os
import requests
import asyncio
from dotenv import load_dotenv
from quart import Quart, request
from telegram import Bot

from calendar_utils import create_event
from openai_utils import parse_user_message

load_dotenv()

app = Quart(__name__)
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))

@app.route("/", methods=["GET", "POST"])
async def home():
    return "Servidor funcionando. Esperando mensajes de Telegram en /webhook"

@app.route("/webhook", methods=["POST"])
async def webhook():
    data = await request.get_json()
    print("📩 Update recibido de Telegram:", data)  # 👈 DEBUG

    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]

    try:
        # Intentar extraer datos de cita
        event_data = None
        try:
            event_data = parse_user_message(text)
        except Exception:
            event_data = None

        if event_data and all(key in event_data for key in ["title", "date", "time"]):
            # Crear la cita en Google Calendar
            try:
                link = create_event(
                    event_data['title'],
                    event_data['date'],
                    event_data['time'],
                    event_data.get('notes', '')
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ Cita creada: {event_data['title']} en {event_data['date']} a las {event_data['time']}. [Ver en Google Calendar]({link})",
                    parse_mode="Markdown"
                )
            except Exception as cal_err:
                print("❌ Error al crear evento en Google Calendar:", cal_err)
                await bot.send_message(chat_id=chat_id,
                                       text="⚠️ No pude crear la cita en Google Calendar. Revisa tus credenciales.")
        else:
            # Responder con el asistente de IA
            response = ask_ollama(text)
            if not response.strip():
                response = "Lo siento, no pude procesar tu mensaje."
            await bot.send_message(chat_id=chat_id, text=response)

    except Exception as e:
        print(f"❌ Error general al procesar mensaje: {e}")
        await bot.send_message(chat_id=chat_id,
                               text="❌ Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo.")
    return "ok"


def ask_ollama(question):
    """
    Función que consulta Ollama usando la API REST
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",  # Ajusta al modelo que tengas disponible
                "prompt": f"Actúa como un asistente amigable y responde en español: {question}",
                "stream": False
            }
        )
        print("🌐 Status Ollama:", response.status_code)  # 👈 DEBUG
        print("📦 Respuesta cruda Ollama:", response.text[:500])  # 👈 DEBUG
        result = response.json()

        if "error" in result:
            return f"⚠️ Error de Ollama: {result['error']}"
        return result.get("response", "Lo siento, no pude generar una respuesta.")

    except Exception as e:
        print(f"❌ Error al consultar Ollama: {e}")
        return "Lo siento, hubo un error al procesar tu mensaje."


# ⬇️ Mantener servidor corriendo
if __name__ == "__main__":
    app.run(debug=True, port=5000)
