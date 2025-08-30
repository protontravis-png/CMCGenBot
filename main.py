import os
import re
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Dictionary to keep track of users waiting for input
user_waiting_for_gen = {}

# Fetch BIN info for more details
def fetch_bin_info(bin_number):
    try:
        res = requests.get(f"https://bins-su-api.vercel.app/api/{bin_number}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "vendor": data.get("vendor", "Unknown").upper(),
                "type": data.get("type", "Unknown").upper(),
                "level": data.get("level", "Unknown"),
                "bank": data.get("bank", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "country_emoji": data.get("country_emoji", "🌐"),
            }
    except:
        pass
    return {
        "vendor": "Unknown",
        "type": "Unknown",
        "level": "",
        "bank": "Unknown",
        "country": "Unknown",
        "country_emoji": "🌐"
    }

# Generate a valid CC number using Luhn algorithm
def generate_luhn_number(bin_, length):
    number = bin_ + ''.join(str(random.randint(0, 9)) for _ in range(length - len(bin_) - 1))
    def luhn_calc(num):
        digits = [int(a) for a in num]
        for i in range(len(digits)-2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        return sum(digits)
    last_digit = (10 - luhn_calc(number + "0") % 10) % 10
    return number + str(last_digit)

# Handler for /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("GEN 💳", callback_data="gen")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome! Tap the button below to generate CCs.",
        reply_markup=reply_markup
    )

# Handler for /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Help*\n\n"
        "Use `/gen BIN|MM|YYYY|CVV AMOUNT` to generate cards.\n"
        "Use 'skip' or 'random' for random values.\n"
        "Range in quantity: e.g., `10-15`."
        , parse_mode="Markdown"
    )

# Handler for button presses
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_waiting_for_gen[user_id] = True
    await query.message.reply_text("Please send CC details in the format.")

# Main handler for CC details input
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_waiting_for_gen:
        return
    user_waiting_for_gen.pop(user_id)

    text = update.message.text.strip()

    pattern = r'/gen\s+(\d{6,8})\s*[\|\/]\s*(\d{2})\s*[\|\/]\s*(\d{2,4})\s*[\|\/]\s*([^\s\|\/]+)\s+([0-9\-]+)'
    match = re.match(pattern, text, re.IGNORECASE)
    if not match:
        await update.message.reply_text("Wrong format! Example: `/gen 414720|01|2025|450 10`")
        return

    bin_raw, mm_raw, yy_raw, cvv_raw, qty_raw = match.groups()

    yy = yy_raw if len(yy_raw) == 4 else f"20{yy_raw}"
    mm = mm_raw

    # Handle quantity (single or range)
    if "-" in qty_raw:
        start, end = map(int, qty_raw.split("-"))
        qty = random.randint(min(start, end), max(start, end))
    else:
        try:
            qty = int(qty_raw)
        except:
            qty = 10

    # Clamp qty between 10 and 100
    qty = max(10, min(qty, 100))

    # Fetch BIN info
    bin_info = fetch_bin_info(bin_raw)

    # Decide card length based on vendor
    vendor_len = {
        "VISA": 16, "MASTERCARD": 16, "AMEX": 15, "DISCOVER": 16, "JCB": 16
    }
    cc_len = vendor_len.get(bin_info["vendor"], 16)

    def get_random_cvv():
        return ''.join(str(random.randint(0, 9)) for _ in range(4 if bin_info["vendor"]=="AMEX" else 3))

    cards = []
    for _ in range(qty):
        mm_gen = mm if mm_raw.lower() not in ["skip", "random"] else f"{random.randint(1,12):02d}"
        yy_gen = yy if yy_raw.lower() not in ["skip", "random"] else str(random.randint(2025, 2036))
        cvv_gen = cvv_raw if cvv_raw.lower() not in ["skip", "random"] else get_random_cvv()
        cc_number = generate_luhn_number(bin_raw, cc_len)
        cards.append(f"{cc_number}|{mm_gen}|{yy_gen}|{cvv_gen}")

    # Prepare output
    message = (
        f"🎉 *Generated {qty} Cards* 🎉\n"
        f"\n🔢 BIN: `{bin_raw}`\n"
        f"🏦 Bank: {bin_info['bank']}\n"
        f"💳 Brand: {bin_info['vendor']}\n"
        f"⚡ Type: {bin_info['type']} ({bin_info['level']})\n"
        f"🌍 Country: {bin_info['country']} {bin_info['country_emoji']}\n\n"
        "```" + "\n".join(cards) + "```"
    )
    await update.message.reply_text(message, parse_mode="Markdown")
  
def main():
    TOKEN = os.getenv("TOKEN")  # Your bot token here
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
