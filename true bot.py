import telebot
import psycopg2
import requests
from telebot import types
from decouple import config
# === CONFIG ===

TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
OPENROUTER_API_KEY = config('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
id=int(config('TELGRAM_ID'))
AUTHORIZED_USERS = [id]  # Inserisci il tuo ID Telegram

# === MEMORIA DELLE CONVERSAZIONI ===

user_conversations = {}

# === FUNZIONI ===

def is_authorized(message):
    return message.chat.id in AUTHORIZED_USERS

def ask_openrouter(conversation):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/ilTuoBotTelegram",
            "X-Title": "TelegramBotAI"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": conversation,
            "temperature": 0.7,
            "max_tokens": 300
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"❌ Errore OpenRouter: {e}")
        return f"⚠️ Errore con OpenRouter: {e}"

# === COMANDI TELEGRAM ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_authorized(message):
        print(f"❌ Utente non autorizzato: {message.chat.id}")
        return
    bot.send_message(message.chat.id,f"Utente autorizzato: {message.chat.id}, utilizza pure i comandi disponibili")

@bot.message_handler(commands=['ai'])
def ai(message):
    if not is_authorized(message):
        print(f"❌ Utente non autorizzato: {message.chat.id}")
        return
    bot.reply_to(message, "Ciao! Puoi chattare direttamente con me. Scrivi pure. Usa /exit per terminare la conversazione.")

    try:
        bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=types.MenuButtonCommands(type="commands")
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Errore nel settaggio del menu: {e}")

@bot.message_handler(commands=['exit'])
def reset_conversation(message):
    if not is_authorized(message):
        print(f"❌ Utente non autorizzato: {message.chat.id}")
        return
    user_conversations.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "🗑️ Conversazione resettata. Puoi iniziare una nuova chat.")

@bot.message_handler(commands=['id'])
def return_id(message):
    bot.send_message(message.chat.id, message.chat.id)

# === GESTIONE CHAT ===

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    if not is_authorized(message):
        print(f"❌ Utente non autorizzato: {message.chat.id}")
        return

    print(f"📩 Messaggio ricevuto da {message.chat.id}: {message.text}")

    chat_id = message.chat.id
    question = message.text
    bot.send_chat_action(chat_id, 'typing')

    # Inizializza cronologia se non esiste
    if chat_id not in user_conversations:
        user_conversations[chat_id] = [
            {"role": "system", "content": "Sei un assistente utile, preciso e conciso."}
        ]

    # Aggiunge il messaggio dell'utente
    user_conversations[chat_id].append({"role": "user", "content": question})

    # Ottieni risposta dell'AI
    response = ask_openrouter(user_conversations[chat_id])

    # Aggiunge la risposta dell'AI alla cronologia
    user_conversations[chat_id].append({"role": "assistant", "content": response})

    # Invia la risposta
    try:
        bot.send_message(chat_id, response)
    except Exception as e:
        print(f"❌ Errore nell'invio del messaggio: {e}")

# === AVVIO ===

print("🤖 Bot Telegram AI attivo e in ascolto...")

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ Errore nel polling: {e}")
