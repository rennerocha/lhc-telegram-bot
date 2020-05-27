import datetime
import logging

from dynaconf import settings
from ics import Calendar

from utils.ics_calendar import lhc_ics

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("joker")


def get_events(when=""):
    with open(settings.ICS_LOCATION, "r") as ics_file:
        calendar = Calendar(ics_file.read())

    all_events = list({event for event in calendar.events})

    if when == "future":
        events = [
            event for event in all_events if event.begin.date() >= datetime.date.today()
        ]
    elif when == "today":
        events = [
            event for event in all_events if event.begin.date() == datetime.date.today()
        ]
    else:
        events = all_events

    return events


def quando(update, context):
    future_events = get_events("future")
    next_event = min(future_events, key=lambda e: e.begin)
    if next_event:
        event = {
            "title": next_event.name,
            "date": next_event.begin.strftime("%d/%m/%Y"),
            "url": next_event.url,
        }
        next_event_msg = f"Vai rolar \"{event['title']}\" em {event['date']}. Mais informações em {event['url']}."
        context.bot.send_message(update.message.chat_id, text=next_event_msg)
    else:
        context.bot.send_message(
            update.message.chat_id,
            text="Não existe nenhum evento agendado até o momento.",
        )


def generate_ics(context):
    logger.info("Generating new ICS file.")
    lhc_ics(settings.ICS_LOCATION)


def pin_today_event(context):
    today_events = get_events("today")
    today_event = min(today_events, key=lambda e: e.begin)
    if today_event:
        event = {
            "title": today_event.name,
            "date": today_event.begin.strftime("%d/%m/%Y"),
            "url": today_event.url,
        }
        today_event_msg = f"**Hoje** {event['date']} vai rolar \"{event['title']}\". Mais informações em {event['url']}."

        message = context.bot.send_message(
            settings.LHC_CHAT_ID, text=today_event_msg, parse_mode="Markdown"
        )

        context.bot.pin_chat_message(
            settings.LHC_CHAT_ID, message.message_id, disable_notification=False
        )
    else:
        chat = update.message.bot.get_chat(chat_id)
        pinned_message = chat.pinned_message
        if pinned_message.from_user.username == "lhc_joker_bot":
            context.bot.pin_chat_message(
                settings.LHC_CHAT_ID, pinned_message.message_id
            )
