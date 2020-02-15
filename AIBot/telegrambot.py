from telegram.ext import CommandHandler, MessageHandler, Filters
import telegram
from django_telegrambot.apps import DjangoTelegramBot
import logging.handlers
from AIBot.models import *


rotating_handler = logging.handlers.RotatingFileHandler('bot.log')
stream_handler = logging.StreamHandler()

formatting = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatting)
stream_handler.setFormatter(formatting)

logger = logging.getLogger(__name__)
logger.addHandler(rotating_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


WELCOME_MESSAGE = "Benvenuto!\n" \
                  "Sto valutando le prestazioni di voi debol... *meravigliosi e teneri* umani su un insieme di immagini " \
                  "rispetto alle mie!\n" \
                  "Il problema è questo: date due immagini di persone, proviamo entrambi a dire chi è il più giovane, " \
                  "o se hanno più o meno la stessa età.\n" \
                  "Quando sei pronto, inizia la gara premendo su /challenge!"


POLICY = "Utilizza /challenge per iniziare la gara.\n\n" \
         "Informazioni sui dati: i tuoi dati non verranno salvati: associo l'ID di questa chat alle tue risposte, ma solo per assicurarmi " \
                  "che non ci siano risposte duplicate dallo stesso utente. Se vuoi eliminare questo dato, in qualunque momento " \
                  "puoi cliccare su 'Arresta Bot' e il dato viene invalidato. Puoi inoltre controllare il mio codice su " \
                  "[questa pagina](https://github.com/Pentracchiano/AgeComparisonPollingBot): sono open-source!\n\n"


def start(update, context):
    context.bot.send_message(update.effective_chat.id, text=WELCOME_MESSAGE, parse_mode=telegram.ParseMode.MARKDOWN)


def help(update, context):
    context.bot.send_message(update.effective_chat.id, text=POLICY, parse_mode=telegram.ParseMode.MARKDOWN)


def challenge(update, context):
    User.objects.create(chat_id=update.effective_chat.id)


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