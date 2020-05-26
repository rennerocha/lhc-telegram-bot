import logging

from dynaconf import settings
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from bot_commands import generic, money, pizza, schedule, status
from models import Status, db

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("joker")


def init_bot():
    logger.info("Joker bot started.")
    updater = Updater(settings.TELEGRAM_API_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    db.create_tables([Status])

    updater.job_queue.run_repeating(status.status_check, interval=60, first=0)
    dispatcher.add_handler(CommandHandler("quem", status.quem))
    dispatcher.add_handler(CommandHandler("status", status.status))

    updater.job_queue.run_repeating(
        schedule.generate_ics, interval=60 * 60 * 24, first=0
    )
    updater.job_queue.run_repeating(
        schedule.pin_today_event, interval=60 * 60 * 24, first=datetime.time(5, 0)
    )
    dispatcher.add_handler(CommandHandler("quando", schedule.quando))
    dispatcher.add_handler(CommandHandler("grana", money.grana))

    dispatcher.add_handler(pizza.pizza_conversation_handler)

    dispatcher.add_handler(CommandHandler("quemsou", generic.quemsou))
    dispatcher.add_handler(CommandHandler("batima", generic.batima))
    dispatcher.add_handler(CommandHandler("boom", generic.boom))

    # This dispatcher must be the last included
    dispatcher.add_handler(MessageHandler(Filters.text, generic.non_commands))

    logger.info("Command handlers set. Start pooling.")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    init_bot()
