from gettext import gettext as _
import os
import logging
import configparser
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import TelegramError

CONFIGFILE_PATH = "data/config.cfg"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot_log")

OPEN = "([{（"
CLOSE = ")]}）"
MATCH = dict(zip(OPEN, CLOSE))


def balance_parens(text):
    stack = []
    for c in text:
        if c in OPEN:
            stack.append(c)
        elif len(stack) > 0 and c in CLOSE and MATCH[stack[len(stack) -
                                                           1]] == c:
            stack.pop()
    stack.reverse()
    reply = "".join(map(lambda x: MATCH[x], stack))
    return reply


class Bot(object):
    translations = {}
    bot = None

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIGFILE_PATH)

        self.updater = Updater(token=self.get_env_conf("TOKEN"))
        print(self.get_env_conf("WEBHOOK_URL"))
        self.dispatcher = self.updater.dispatcher
        self.add_handlers()

    def get_env_conf(self, value, default_value=None):
        if default_value:
            return os.environ.get(value, default_value)
        else:
            return os.environ.get(value)

    def start_polling_loop(self):
        self.disable_webhook()
        self.update_queue = self.updater.start_polling()
        self.updater.idle()
        self.cleaning()

    def start_webhook_server(self):
        self.set_webhook()
        self.update_queue = self.updater.start_webhook(
            self.get_env_conf("IP", "0.0.0.0"),
            int(self.get_env_conf("PORT", "5000")), self.get_env_conf("TOKEN"))
        self.updater.idle()
        self.cleaning()

    def cleaning(self):
        logger.info("Finished program.")

    def set_webhook(self):
        s = self.updater.bot.setWebhook(
            self.get_env_conf("WEBHOOK_URL") + "/" +
            self.get_env_conf("TOKEN"))
        if s:
            logger.info("webhook setup worked")
        else:
            logger.warning("webhook setup failed")
        return s

    def disable_webhook(self):
        s = self.updater.bot.setWebhook("")
        if s:
            logger.info("webhook was disabled")
        else:
            logger.warning("webhook couldn't be disabled")
        return s

    def add_handlers(self):
        self.dispatcher.add_handler(
            CommandHandler("start", self.command_start))
        self.dispatcher.add_handler(CommandHandler("help", self.command_help))
        self.dispatcher.add_handler(
            CommandHandler("enable", self.command_enable))
        self.dispatcher.add_handler(
            CommandHandler("disable", self.command_disable))
        self.dispatcher.add_handler(
            MessageHandler(Filters.text, self.command_balance_parens))
        # self.dispatcher.addUnknownTelegramCommandHandler(self.command_unknown)
        # self.dispatcher.addErrorHandler(self.error_handle)

    def command_start(self, bot, update):
        self.send_message(bot, update.message.chat,
                          _("Hey man, I'm ParensBot."))

    def command_help(self, bot, update):
        self.send_message(bot, update.message.chat,
                          _("""Available Commands:
            /start - Iniciciate or Restart the bot
            /help - Show the command list."""))

    def command_balance_parens(self, bot, update):
        reply = balance_parens(update.message.text)
        if reply != "":
            self.send_message(bot, update.message.chat, reply)

    def command_enable(self, bot, update):
        self.enabled = True
        self.send_message(bot, update.message.chat, "人一輩子的左括號是有限的，誰先用完誰先走（（（（")

    def command_disable(self, bot, update):
        self.enabled = False
        self.send_message(bot, update.message.chat, "咁我收聲咯。")

    def send_message(self, bot, chat, text):
        try:
            bot.sendMessage(chat_id=chat.id, text=text)
            return True
        except TelegramError as e:
            logger.warning(
                "Message sending error to %s [%d] [%s] (TelegramError: %s)" %
                (chat.name, chat.id, chat.type, e))
            return False
        except:
            logger.warning("Message sending error to %s [%d] [%s]" %
                           (chat.name, chat.id, chat.type))
            return False
