from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8736687534:AAHU6DrhmDGBKyJQMbDmmURpUlA6Ht-DaEE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اهلا")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, echo))
app.run_polling(drop_pending_updates=True)
