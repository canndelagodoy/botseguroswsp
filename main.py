import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Configuración leída desde variables de entorno de Render
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "mi_token_secreto_seguros_123")

def respuesta_ia_seguros(mensaje_usuario: str) -> str:
    texto = mensaje_usuario.lower().strip()
    if any(p in texto for p in ["siniestro", "choque", "choqué", "accidente"]):
        return "Para denunciar un siniestro dispones de hasta 72 hs hábiles. Envíanos fotos de los daños, datos del tercero (licencia, póliza, patente) y comisaría interviniente si hubo lesionados."
    elif any(p in texto for p in ["grua", "grúa", "remolque", "auxilio"]):
        return "El servicio de auxilio mecánico y grúa funciona 24 hs. Llama al 0800-XXX-SEGURO o comparte tu ubicación exacta para coordinar el remolque."
    elif any(p in texto for p in ["cotizar", "precio", "cuanto sale", "cuánto sale"]):
        return "Con gusto te cotizamos. Por favor indícanos: marca, modelo, año y tipo de cobertura que buscas (Terceros Completo o Todo Riesgo)."
    elif any(p in texto for p in ["hola", "buenas"]):
        return "¡Hola! Bienvenido a la oficina de seguros. ¿En qué podemos ayudarte? (Cotizaciones, siniestros, grúa o pagos)."
    else:
        return "Gracias por comunicarte con la oficina de seguros. Un asesor revisará tu mensaje en breve."

def enviar_mensaje_whatsapp(telefono_destino: str, texto_respuesta: str):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("Faltan las credenciales de WhatsApp.")
        return
    
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefono_destino,
        "type": "text",
        "text": {"body": texto_respuesta}
    }
    r = requests.post(url, json=payload, headers=headers)
    print("Respuesta de Meta:", r.status_code, r.text)

@app.route("/", methods=["GET"])
def home():
    return "Servidor activo en Render", 200

@app.route("/webhook", methods=["GET"])
def verificar():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado!")
        return challenge, 200
    return "Token inválido", 403

@app.route("/webhook", methods=["POST"])
def recibir():
    data = request.get_json(silent=True) or {}
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            mensaje = entry["messages"][0]["text"]["body"]
            remitente = entry["messages"][0]["from"]
            
            print(f"Mensaje de {remitente}: {mensaje}")
            respuesta = respuesta_ia_seguros(mensaje)
            enviar_mensaje_whatsapp(remitente, respuesta)
    except Exception as e:
        print("Evento no procesado:", e)

    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
