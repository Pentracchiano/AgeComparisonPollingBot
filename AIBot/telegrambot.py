from telegram.ext import CommandHandler, MessageHandler, Filters
from django_telegrambot.apps import DjangoTelegramBot
import logging.handlers

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.handlers.RotatingFileHandler('bot.log', maxBytes=1e6, backupCount=5),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger(__name__)


def start(update, context):
    context.bot.send_message(update.effective_chat.id, text='Hi!')


def help(update, context):
    context.bot.send_message(update.effective_chat.id, text='Help!')


def error(update, context):
    logger.warning('Update "{}" caused error "{}"'.format(update, context.error))


def main():
    logger.info("Loading handlers for AIBot.")

    # Default dispatcher (this is related to the first bot in settings.TELEGRAM_BOT_TOKENS)
    dp = DjangoTelegramBot.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    # log all errors
    dp.add_error_handler(error)