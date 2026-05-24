from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot yoniq!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Render oʻchirib qoʻymasligi uchun orqa fonda port ochish
threading.Thread(target=run).start()

# =========================================================
# ASOSIY BOT KODI SHU YERDAN DAVOM ETADI:
# =========================================================
import telebot
import sqlite3
import time
from telebot import types

# ✅ Tokeningiz va Kanal ID-ngiz
BOT_TOKEN = "8941945580:AAHstPw8wqnxrWTjD8-PMP7a_k9ATlndS_U"

KANAL_ID = "-1003824716595" 

bot = telebot.TeleBot(BOT_TOKEN)

def baza_yarat():
    conn = sqlite3.connect("musiqalar.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qoshiqlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            file_id TEXT
        )
    ''')
    conn.commit()
    conn.close()

baza_yarat()

def obunani_tekshir(user_id):
    try:
        azo_holati = bot.get_chat_member(KANAL_ID, user_id).status
        if azo_holati in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Obunani tekshirishda xatolik: {e}")
        return True

def obuna_oynasi_yubor(chat_id):
    try:
        kanal_info = bot.get_chat(KANAL_ID)
        kanal_link = kanal_info.invite_link if kanal_info.invite_link else "https://t.me/" + kanal_info.username
    except:
        kanal_link = "https://t.me/"
    
    markup = types.InlineKeyboardMarkup()
    button_kanal = types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=kanal_link)
    button_tekshir = types.InlineKeyboardButton(text="✅ A'zo bo'ldim / Tekshirish", callback_data="tekshir_obuna")
    
    markup.add(button_kanal)
    markup.add(button_tekshir)
    
    bot.send_message(
        chat_id, 
        "⚠️ Botdan foydalanish uchun loyihamiz kanaliga a'zo bo'lishingiz shart. "
        "A'zo bo'lib, keyin 'Tekshirish' tugmasini bosing:", 
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def salom_ber(message):
    user_id = message.from_user.id
    if obunani_tekshir(user_id):
        ism = message.from_user.first_name
        bot.send_message(message.chat.id, f"Salom, {ism}! 🎧 AuraMusicBot xizmatingizda.\nMusiqa ijrochi yoki qo'shiq nomini yozing:")
    else:
        obuna_oynasi_yubor(message.chat.id)

@bot.channel_post_handler(content_types=['audio'])
def kanaldan_musiqa_ol(message):
    if str(message.chat.id) == str(KANAL_ID):
        audio = message.audio
        file_id = audio.file_id
        performer = audio.performer if audio.performer else ""
        title = audio.title if audio.title else ""
        fayl_nomi = audio.file_name if audio.file_name else ""
        fayl_nomi = fayl_nomi.replace(".mp3", "").replace("_", " ")
        
        if performer or title:
            toliq_nom = f"{performer} {title}".strip().lower()
        else:
            toliq_nom = fayl_nomi.strip().lower()
            
        if not toliq_nom:
            toliq_nom = "nomsiz tarona"

        conn = sqlite3.connect("musiqalar.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO qoshiqlar (nom, file_id) VALUES (?, ?)", (toliq_nom, file_id))
        conn.commit()
        conn.close()
        print(f"💾 Bazaga saqlandi: {toliq_nom}")

@bot.callback_query_handler(func=lambda call: call.data == "tekshir_obuna")
def callback_tekshir(call):
    if obunani_tekshir(call.from_user.id):
        bot.answer_callback_query(call.id, "Rahmat! Obuna tasdiqlandi. 🎉")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🎧 AuraMusicBot faollashdi! Endi bemalol musiqa nomini yozib qidirishingiz mumkin:")
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def musiqani_qidir(message):
    user_id = message.from_user.id
    if not obunani_tekshir(user_id):
        obuna_oynasi_yubor(message.chat.id)
        return

    qidiruv_matni = message.text.lower()
    conn = sqlite3.connect("musiqalar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nom, file_id FROM qoshiqlar WHERE nom LIKE ?", ('%' + qidiruv_matni + '%',))
    natijalar = cursor.fetchall()
    conn.close()
    
    if natijalar:
        bot.send_message(message.chat.id, f"🔍 {len(natijalar)} ta musiqa topildi! Yuklanmoqda...")
        for nom, file_id in natijalar[:5]:
            try:
                bot.send_audio(message.chat.id, file_id)
            except Exception as e:
                print(f"Xatolik: {e}")
    else:
        bot.send_message(message.chat.id, "😔 Kechirasiz, AuraMusic bazasidan bunday musiqa topilmadi. Boshqa nom yozib ko'ring.")

print("Bot OP (Majburiy obuna) bilan ishga tushdi...")
while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Xatolik: {e}")
        time.sleep(5)
            
