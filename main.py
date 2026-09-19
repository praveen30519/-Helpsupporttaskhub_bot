import os
import json
import threading
from flask import Flask
import telebot
from telebot import types

# 1. Fake Web Server Render ko active rakhne ke liye
app = Flask(__name__)

@app.route('/')
def home():
    return "TaskHub Support Bot is Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# 2. Bot Configuration
BOT_TOKEN = "8817287623:AAFro2dm2CYFLnBvvhRRwaOFpX8jGshQP5I"
ADMIN_ID = 2016851713

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "taskhub_users.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_data()

def init_user(uid, username):
    s_uid = str(uid)
    if s_uid not in db:
        db[s_uid] = {
            "username": f"@{username}" if username else "User",
            "points": 0,
            "status": "pending_verification",
            "slot": "Not Set",
            "voucher": None
        }
        save_data(db)

def get_main_menu(uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📸 Upload Verification", callback_data="btn_verify")
    btn2 = types.InlineKeyboardButton("⏰ Change Slot", callback_data="btn_slot")
    btn3 = types.InlineKeyboardButton("💰 My Points & Rewards", callback_data="btn_points")
    btn4 = types.InlineKeyboardButton("🏆 Leaderboard", callback_data="btn_leaderboard")
    btn5 = types.InlineKeyboardButton("🎁 Claim Amazon Voucher", callback_data="btn_claim")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    uid = message.from_user.id
    init_user(uid, message.from_user.username)
    bot.send_message(
        uid,
        "👋 *TaskHub Member Portal me aapka swagat hai!*\n\nNiche diye gaye options ka upayog karein:",
        parse_mode="Markdown",
        reply_markup=get_main_menu(uid)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("btn_"))
def handle_user_menu(call):
    uid = str(call.from_user.id)
    bot.answer_callback_query(call.id)
    init_user(uid, call.from_user.username)

    if call.data == "btn_verify":
        db[uid]["status"] = "awaiting_photo"
        save_data(db)
        bot.send_message(
            call.message.chat.id,
            "📸 *Mandatory Verification Step:*\n\nApni selfie/verification photo bhejein.\n⚠️ *Dhyan dein: Jab tak photo approve nahi hogi, rewards unlock nahi honge.*",
            parse_mode="Markdown"
        )
    elif call.data == "btn_slot":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🌅 10:00 AM - 01:00 PM", callback_data="set_slot_10-1"),
            types.InlineKeyboardButton("☀️ 02:00 PM - 05:00 PM", callback_data="set_slot_2-5"),
            types.InlineKeyboardButton("🌙 06:00 PM - 09:00 PM", callback_data="set_slot_6-9")
        )
        bot.send_message(call.message.chat.id, "⏰ *Apna time slot chunein:*", parse_mode="Markdown", reply_markup=markup)
    elif call.data == "btn_points":
        pts = db[uid].get("points", 0)
        v_status = "✅ Approved" if db[uid].get("status") == "approved" else "⏳ Pending"
        slot = db[uid].get("slot", "Not Set")
        bot.send_message(
            call.message.chat.id,
            f"👤 *Aapki Profile Details:*\n\n• **Reward Points:** `{pts}` / 100\n• **Account Status:** {v_status}\n• **Allotted Slot:** {slot}\n\n_(100 points hone par aap Amazon Voucher claim kar sakte hain)_",
            parse_mode="Markdown"
        )
    elif call.data == "btn_leaderboard":
        sorted_users = sorted(db.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
        text = "🏆 *Top Member Leaderboard:*\n\n"
        for i, (k, v) in enumerate(sorted_users, 1):
            text += f"{i}. {v.get('username', 'User')} — `{v.get('points', 0)} Pts`\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    elif call.data == "btn_claim":
        pts = db[uid].get("points", 0)
        if pts < 100:
            bot.send_message(
                call.message.chat.id,
                f"❌ *Claim Failed!*\n\nAapke pass abhi sirf *{pts} points* hain. Minimum *100 points* hona zaroori hai.",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(call.message.chat.id, "✅ *Redeem Request Sent!*\n\nAdmin review ke baad Amazon Gift Voucher bhejenge.", parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"🎁 *New Claim Request!*\n👤 User: {db[uid].get('username')} (`{uid}`)\n💰 Total Points: {pts}\n\n`/sendvoucher {uid} CODE`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_slot_"))
def handle_slot(call):
    uid = str(call.from_user.id)
    slot_val = call.data.replace("set_slot_", "")
    db[uid]["slot"] = slot_val
    save_data(db)
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"✅ Aapka Slot *{slot_val}* set ho chuka hai!", parse_mode="Markdown")
    bot.send_message(ADMIN_ID, f"⏰ User {db[uid].get('username')} (`{uid}`) ne slot `{slot_val}` chuna.", parse_mode="Markdown")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = str(message.from_user.id)
    init_user(uid, message.from_user.username)
    photo_id = message.photo[-1].file_id

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_{uid}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{uid}")
    )
    bot.send_photo(ADMIN_ID, photo_id, caption=f"📸 *New Verification Photo*\n👤 User: {db[uid].get('username')} (`{uid}`)", parse_mode="Markdown", reply_markup=markup)
    bot.reply_to(message, "✅ Photo admin review ke liye bhej di gayi hai.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    action, target_uid = call.data.split("_")[1], call.data.split("_")[2]

    if action == "app":
        db[target_uid]["status"] = "approved"
        save_data(db)
        bot.send_message(int(target_uid), "🎉 *Mubarak ho! Aapki verification APPROVE ho gayi hai.*", parse_mode="Markdown")
        bot.edit_message_caption("✅ *Approved*", chat_id=ADMIN_ID, message_id=call.message.message_id)
    elif action == "rej":
        db[target_uid]["status"] = "rejected"
        save_data(db)
        bot.send_message(int(target_uid), "❌ *Aapki verification REJECT ho gayi hai. Dobara saaf selfie upload karein.*", parse_mode="Markdown")
        bot.edit_message_caption("❌ *Rejected*", chat_id=ADMIN_ID, message_id=call.message.message_id)

@bot.message_handler(commands=['addpoints'])
def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, target_uid, pts = message.text.split()
        target_uid = str(target_uid)
        pts = int(pts)
        if target_uid in db:
            db[target_uid]["points"] = db[target_uid].get("points", 0) + pts
            save_data(db)
            bot.reply_to(message, f"✅ User `{target_uid}` ko {pts} points de diye gaye. (Total: {db[target_uid]['points']})")
            bot.send_message(int(target_uid), f"🎁 *Update:* Aapke account me *{pts} Points* add kiye gaye hain!\nTotal: `{db[target_uid]['points']}` Pts", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Format: `/addpoints <user_id> <points>`")

@bot.message_handler(commands=['sendvoucher'])
def send_voucher_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(maxsplit=2)
        target_uid = str(parts[1])
        v_code = parts[2]
        if target_uid in db:
            db[target_uid]["points"] = max(0, db[target_uid].get("points", 0) - 100)
            db[target_uid]["voucher"] = v_code
            save_data(db)
            bot.send_message(int(target_uid), f"🎉 *Aapka Amazon Voucher:*\n\n`{v_code}`\n\nIse Amazon Gift Card me add karein.", parse_mode="Markdown")
            bot.reply_to(message, f"✅ Voucher `{target_uid}` ko bhej diya gaya.")
    except:
        bot.reply_to(message, "Format: `/sendvoucher <user_id> <AMAZON_CODE>`")

@bot.message_handler(func=lambda msg: True, content_types=['text'])
def relay_chat(message):
    if message.from_user.id == ADMIN_ID:
        if message.reply_to_message and "ID: `" in (message.reply_to_message.text or ""):
            try:
                raw = message.reply_to_message.text
                target_id = int(raw.split("ID: `")[1].split("`")[0])
                bot.send_message(target_id, f"💬 *Support Team Reply:*\n\n{message.text}", parse_mode="Markdown")
                bot.reply_to(message, "✅ Reply bhej diya gaya.")
            except Exception as e:
                bot.reply_to(message, f"Error: {e}")
        return

    uid = str(message.from_user.id)
    init_user(uid, message.from_user.username)
    if db[uid].get("status") == "awaiting_photo":
        bot.reply_to(message, "🚫 Pehle apni verification *PHOTO* upload karein.")
        return

    admin_box = f"📩 *New Support Chat*\n👤 From: {db[uid].get('username')}\n🆔 ID: `{uid}`\n\n💬 {message.text}"
    bot.send_message(ADMIN_ID, admin_box, parse_mode="Markdown")
    bot.reply_to(message, "✅ Message bhej diya gaya hai.")

# Background thread me web server chalu karein
threading.Thread(target=run_web).start()

# Bot start
print("Bot Polling Running...")
bot.infinity_polling(timeout=20, long_polling_timeout=10)
      
