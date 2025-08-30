from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Your bot token here
TOKEN = 'YOUR_BOT_TOKEN_HERE'

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello, World!")

def main():
    # Create updater and pass your bot token
    updater = Updater(TOKEN, use_context=True)

    # Get dispatcher to register handlers
    dp = updater.dispatcher

    # Add command handler for /start
    dp.add_handler(CommandHandler('start', start))

    # Start polling
    updater.start_polling()

    # Run the bot until you press Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
