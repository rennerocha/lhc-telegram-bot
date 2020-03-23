import logging
import random
from datetime import datetime
from pytz import timezone

import requests
from dynaconf import settings

from models import Status

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("joker")

TIMEZONE = timezone(settings.TIMEZONE)


def quem(update, context):
    notify_msg = []
    last_status = Status.select().order_by(Status.date.desc()).first()

    no_connected = len(last_status.who or [])
    if no_connected == 0:
        notify_msg.append("Não tem nenhuma pessoa conhecida lá...")
    else:
        space_emoji = random.choice(
            ["\U0001F30C", "\U0001F6F0", "\U0001F680", "\U0001F6F8"]
        )
        notify_msg.append(
            f"Pessoas conhecidas no espaço {space_emoji}: {last_status.who}."
        )

    if last_status.n_unknown_macs is not None and last_status.n_unknown_macs > 0:
        if last_status.n_unknown_macs == 1:
            unknown_text = random.choice(
                [
                    "Mais um gato \U0001F408, provavelmente.",
                    "Mais uma pessoa desconhecida.",
                    "Mais um pingüim \U0001F427, provavelmente.",
                    "Mais um bando de maritacas \U0001F99C, provavelmente.",
                ]
            )
        else:
            unknown_text = "Mais {no_unknown_macs} pessoas desconhecidas."
        notify_msg.append(unknown_text)

    context.bot.send_message(update.message.chat_id, text=" ".join(notify_msg))


def status_check(context):
    logger.info("Checking status of LHC.")
    last_status = Status.select().order_by(Status.date.desc()).first()

    response = requests.get("https://lhc.net.br/spacenet.json")
    spacenet = response.json()
    state = spacenet.get("state", {})

    is_open = state.get("open")
    last_change_timestamp = state.get("lastchange")
    last_change = datetime.fromtimestamp(last_change_timestamp).astimezone(TIMEZONE)
    current_time = datetime.now().astimezone(TIMEZONE)

    current_status = Status(
        is_open=is_open, last_change=last_change, date=current_time,
    )

    if is_open:
        response = requests.get("https://lhc.net.br/spacenet.json?whois")
        whois = response.json()
        n_unknown_macs = whois.get("n_unknown_macs", 0)
        current_status.n_unknown_macs = n_unknown_macs
        who = whois.get("who", [])
        current_status.who = ", ".join(who)

    status = "OPEN" if is_open else "CLOSED"
    logger.info(f"LHC is {status} since {current_status.last_change}.")

    status_changed = (
        last_status is None or current_status.is_open != last_status.is_open
    )
    if status_changed:
        if is_open:
            notify_msg = f"O LHC foi aberto \U0001F513 por {current_status.who} às {current_status.last_change}."
        else:
            notify_msg = (
                f"O LHC está fechado \U0001F512 desde {current_status.last_change}."
            )

        logger.info(f"LHC status changed. Sending notification to LHC channel.")
        context.bot.send_message(chat_id="@lhc_campinas", text=notify_msg)

    current_status.save()


def status(update, context):
    logger.info("Command /status received.")

    last_status = Status.select().order_by(Status.date.desc()).first()

    if last_status is None:
        context.bot.send_message(
            update.message.chat_id,
            text="O LHC pode estar aberto \U0001F513 ou fechado \U0001F512. Eu não consegui descobrir.",
        )
    else:
        status = "aberto \U0001F513" if last_status.is_open else "fechado \U0001F512"
        msg = f"O LHC está {status} desde {last_status.last_change}."
        context.bot.send_message(update.message.chat_id, text=msg)
