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
            response = ask_groq(text)
            if not response.strip():
                response = "Lo siento, no pude procesar tu mensaje."
            await bot.send_message(chat_id=chat_id, text=response)

    except Exception as e:
        print(f"❌ Error general al procesar mensaje: {e}")
        await bot.send_message(chat_id=chat_id,
                               text="❌ Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo.")
    return "ok"


def ask_groq(question):
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
                "messages": [
                    {"role": "system", "content": "Eres un asistente útil que responde en español."},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.7
            }
        )

        print("🌐 Status Groq:", response.status_code)
        result = response.json()
        print("📦 Respuesta cruda Groq:", result)

        if "error" in result:
            return f"⚠️ Error de Groq: {result['error']['message']}"

        return result["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"❌ Error al consultar Groq: {e}")
        return "Lo siento, hubo un error al procesar tu mensaje."


# ⬇️ Mantener servidor corriendo
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

