from telegram.ext import CommandHandler, MessageHandler, Filters
import telegram
from django_telegrambot.apps import DjangoTelegramBot
import logging.handlers
from AIBot.models import *
from django.db.models import F
from django.db import IntegrityError

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('bot.log'),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

WELCOME_MESSAGE = "Benvenuto!\n" \
                  "Sto valutando le prestazioni di voi debol... *meravigliosi e teneri* umani su un insieme di " \
                  "immagini " \
                  "rispetto alle mie!\n" \
                  "Il problema è questo: date due immagini di persone, proviamo entrambi a dire chi è il più giovane, " \
                  "" \
                  "o se hanno più o meno la stessa età.\n" \
                  "Quando sei pronto, inizia la gara premendo su /challenge!"

POLICY = "Utilizza /challenge per iniziare la gara.\n\n" \
         "Informazioni sui dati: i tuoi dati non verranno salvati: associo l'ID di questa chat alle tue risposte, " \
         "ma solo per assicurarmi " \
         "che non ci siano risposte duplicate dallo stesso utente. Se vuoi eliminare questo dato, in qualunque " \
         "momento " \
         "puoi cliccare su 'Arresta Bot' e il dato viene invalidato. Puoi inoltre controllare il mio codice su " \
         "[questa pagina](https://github.com/Pentracchiano/AgeComparisonPollingBot): sono open-source!\n\n"

first_image_pair = ImagePair.objects.get(pk=0)


def send_image_group_with_buttons(bot, chat_id, image0, image1, text):
    buttons = telegram.InlineKeyboardMarkup(inline_keyboard=[
        [telegram.InlineKeyboardButton(text='Prima foto', callback_data='-1')],
        [telegram.InlineKeyboardButton(text='Stessa età', callback_data='0')],
        [telegram.InlineKeyboardButton(text='Seconda foto', callback_data='1')],
    ])

    # this is based on the fact that a media group has the caption of the first inputmedia photo.
    # In this way, I can delete one message and continue: otherwise, a user could click on buttons of the old photos
    # by mistake, and this input would be considered for the current photo pair.

    image0_media = telegram.InputMediaPhoto(image0, caption=text, parse_mode=telegram.ParseMode.MARKDOWN)
    image1_media = telegram.InputMediaPhoto(image1)

    bot.send_media_group(chat_id=chat_id, media=[image0_media, image1_media])
    bot.send_message(chat_id=chat_id, text="Fai la tua scelta:", reply_markup=buttons)  # non riesco a trovare un modo per posizionare un reply markup ad un media group...


def start(update, context):
    context.bot.send_message(update.effective_chat.id, text=WELCOME_MESSAGE, parse_mode=telegram.ParseMode.MARKDOWN)
    User.objects.create(chat_id=update.effective_chat.id)


def help(update, context):
    context.bot.send_message(update.effective_chat.id, text=POLICY, parse_mode=telegram.ParseMode.MARKDOWN)


def challenge(update, context):
    user = User.objects.get(pk=update.effective_chat.id)
    try:
        current_challenge = Challenge.objects.create(pair_to_analyze=first_image_pair, user=user)
        message = "Cominciamo!\nDevi dirmi in quale foto si trova la persona *più giovane*."
    except IntegrityError:
        # i could just present the current photo in this way, but i'm worried
        # because in this way i would present another set of buttons to the user... which will not be deleted
        # current_challenge = Challenge.objects.get(user=user)
        # message = ""
        context.bot.send_message(chat_id=user.chat_id, text="Hai già una challenge in corso!")
        return

    send_image_group_with_buttons(context.bot,
                                  user.chat_id,
                                  current_challenge.pair_to_analyze.image0.file,
                                  current_challenge.pair_to_analyze.image1.file,
                                  message
                                  )


def challenge_answer(update, context):
    query = update.callback_query
    user = User.objects.get(pk=query.message.chat.id)
    correct_answer = user.challenge.pair_to_analyze.correct_answer
    current_pair = user.challenge.pair_to_analyze
    user_answer = int(query.data)
    Answer.objects.create(value=user_answer, challenge=user.challenge, image_pair=current_pair)

    try:
        user.challenge.pair_to_analyze = ImagePair.objects.get(pk=current_pair.pair_index + 1)
    except ImagePair.DoesNotExist:
        user.challenge.pair_to_analyze = None
        user.challenge.completed = True

    user.challenge.save()

    if correct_answer == user_answer:
        message = "Complimenti! Risposta corretta!"
    else:
        message = "Oh no... la risposta corretta era \"{}\"".format(AnswerType.readable(correct_answer))

    context.bot.answer_callback_query(callback_query_id=query.id, text=message)  # necessary even if no text is sent
    context.bot.delete_message(chat_id=user.chat_id, message_id=query.message.message_id)  # removing old buttons
    context.bot.send_message(chat_id=user.chat_id, text=message)

    if not user.challenge.completed:
        send_image_group_with_buttons(context.bot,
                                      user.chat_id,
                                      user.challenge.pair_to_analyze.image0.file,
                                      user.challenge.pair_to_analyze.image1.file,
                                      "Prossimo paio! In quale foto si trova la persona *più giovane*?")
    else:
        total_correct_answers = user.challenge.answer_set.filter(image_pair__correct_answer=F('value')).count()
        total_answers = user.challenge.answer_set.count()

        context.bot.send_message(chat_id=user.chat_id, text="Grazie di aver partecipato alla sfida!\n"
                                                            "Hai totalizzato un punteggio di *{:.2f}%*!\n\n"
                                                            "Per preservare la tua anonimità, eliminerò i tuoi dati.\n\n"
                                                            "[Addio, e grazie per tutto il pesce!](https://it.wikipedia.org/wiki/Addio,_e_grazie_per_tutto_il_pesce)".format(
            total_correct_answers / total_answers * 100),
                                 parse_mode=telegram.ParseMode.MARKDOWN)
        user.delete()


def error(update, context):
    logger.warning('Update "{}" caused error "{}"'.format(update, context.error))


def main():
    logger.info("Loading handlers for AIBot.")

    # Default dispatcher (this is related to the first bot in settings.TELEGRAM_BOT_TOKENS)
    dp = DjangoTelegramBot.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("challenge", challenge))

    # register for the inline query
    dp.add_handler(telegram.ext.CallbackQueryHandler(challenge_answer))

    # log all errors
    dp.add_error_handler(error)
