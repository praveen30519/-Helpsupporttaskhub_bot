import time
import telebot
from telebot import types

BOT_TOKEN = "8817287623:AAFro2dm2CYFLnBvvhRRwaOFpX8jGshQP5I"
ADMIN_ID = 2016851713

bot = telebot.TeleBot(BOT_TOKEN)


def get_main_keyboard():
  markup = types.InlineKeyboardMarkup(row_width=2)
  btn1 = types.InlineKeyboardButton(
      "📸 Verification", callback_data="verification"
  )
  btn2 = types.InlineKeyboardButton("🗑️ Data Delete", callback_data="delete")
  btn3 = types.InlineKeyboardButton(
      "⏰ Slot Change", callback_data="slot_change"
  )
  btn4 = types.InlineKeyboardButton("💰 Rewards Query", callback_data="rewards")
  markup.add(btn1, btn2, btn3, btn4)
  return markup


def get_back_keyboard():
  markup = types.InlineKeyboardMarkup()
  btn_back = types.InlineKeyboardButton(
      "🔙 Back to Menu", callback_data="main_menu"
  )
  markup.add(btn_back)
  return markup


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.send_message(
      message.chat.id,
      "👋 *TaskHub Support Bot me aapka swagat hai!*\n\n"
      "Aapko kis cheez me help chahiye? Niche option chunein:",
      parse_mode="Markdown",
      reply_markup=get_main_keyboard(),
  )


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
  try:
    bot.answer_callback_query(call.id)

    if call.data == "main_menu":
      bot.edit_message_text(
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          text="👋 *TaskHub Support Bot*\n\nNiche diye gaye option me se chunein:",
          parse_mode="Markdown",
          reply_markup=get_main_keyboard(),
      )
      return

    topic_names = {
        "verification": "📸 Verification Help",
        "delete": "🗑️ Data Delete Request",
        "slot_change": "⏰ Time Slot Change",
        "rewards": "💰 Rewards Query",
    }
    topic = topic_names.get(call.data, "Help")

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            f"✅ *Aapne chuna:* {topic}\n\n"
            "✍️ *Ab apni problem yahan type karke bhejein.*\n"
            "Hamari admin team turant check karegi.\n\n"
            "_(Dusra option chunne ke liye niche click karein)_"
        ),
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(),
    )
  except Exception as e:
    print(f"Callback error: {e}")


@bot.message_handler(func=lambda message: True)
def forward_to_admin(message):
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else "No Username"
  )
  user_info = (
      f"📩 *New Support Request*\n"
      f"👤 User: {username}\n"
      f"🆔 ID: `{message.from_user.id}`\n"
      f"💬 Message: {message.text}"
  )
  bot.send_message(ADMIN_ID, user_info, parse_mode="Markdown")
  bot.reply_to(
      message,
      "✅ Aapka message admin team ko mil gaya hai. Kripya thoda intezar karein.",
  )


print("Support Bot Running...")

while True:
  try:
    bot.polling(none_stop=True, interval=1, timeout=30)
  except Exception as e:
    print(f"Server reconnecting... ({e})")
    time.sleep(3)
    
