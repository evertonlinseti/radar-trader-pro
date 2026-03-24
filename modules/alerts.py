# Isolamos a comunicação externa. Configuração do TELEGRAM

import requests

# Suas credenciais atuais - Identificadores do seu robô e da sua conta no Telegram.
TOKEN = "8064310862:AAF-KtdkSsgC0i1rMUTMk0sNs0RH8cC10e4"
CHAT_ID = "1051226386"

def enviar_alerta(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        # Adicionado o parse_mode para permitir negrito e emojis
        payload = {
            "chat_id": CHAT_ID, 
            "text": msg, 
            "parse_mode": "Markdown" # Linha crucial que permite que o Telegram entenda os asteriscos (*) como comando para deixar o texto em negrito.
        }
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        # Opcional: print(f"Erro ao enviar Telegram: {e}") 
        pass
