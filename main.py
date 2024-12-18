import csv
from datetime import datetime, timezone
import json
import math
from os import environ
from random import choice
import requests


def build_totaliser(amount_raised, target):
    with open("icons.csv") as fh:
        icon_pairs = list(csv.reader(fh))[1:]
    done_icon, todo_icon = choice(icon_pairs)

    totaliser_size = 10
    done_total = min(
        totaliser_size,
        math.floor(totaliser_size * amount_raised / target))
    todo_total = totaliser_size - done_total
    return "{done}{todo}".format(
        done=(done_total * f":{done_icon}: "),
        todo=(todo_total * f":{todo_icon}: "),
    ).strip()


def run():
    url = (
        "https://sf-api-production.thebiggive.org.uk"
        "/campaigns/services/apexrest/v1.0/campaigns/a056900002TPVWCAA5"
    )
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    end_dt = datetime.fromisoformat(data["endDate"])
    now_dt = datetime.now(tz=timezone.utc)

    finished = False
    hours_to_go = int((end_dt - now_dt).total_seconds() / 60 / 60)
    if now_dt > end_dt:
        # it’s finished
        finished = True
        time_to_go = "Time’s up! The Big Give™ is over :heart: :wave: :smiling_face_with_tear: (For this year, anyway.)\n\n"
    elif hours_to_go < 2:
        minutes_to_go = int((end_dt - now_dt).total_seconds() / 60)
        time_to_go = f":drum_with_drumsticks: Just {minutes_to_go} minutes to go! :drum_with_drumsticks:\n\n"
    elif hours_to_go < 24:
        emoji = ":clock" + now_dt.strftime("%-I") + "30" * (now_dt.minute // 30) + ":"
        time_to_go = f"{emoji} {hours_to_go} hours to go! {emoji}\n\n"
    else:
        time_to_go = ""

    amount_raised = int(data["amountRaised"])
    target = int(data["target"])
    donation_count = int(data["donationCount"])

    totaliser = build_totaliser(amount_raised, target)
    average_donation = amount_raised / donation_count / 2 if donation_count else 0
    # round down to 1dp
    total_percent = math.floor(1000 * amount_raised / target) / 10

    with open("data/output.json") as fh:
        prev_data = json.load(fh)

    message = (
        f"{time_to_go}"
        f"£{amount_raised:,} raised{' so far' if not finished else ''}, "
        f"from {donation_count:,} donation{'' if donation_count == 1 else 's'}. "
        f"That’s an average donation of £{average_donation:.2f}.\n\n"
        "Progress to target:\n"
        f"{totaliser}\n"
        f"(i.e. {total_percent}%)"
    )
    print(message)

    slack_trigger_url = environ.get("SLACK_TRIGGER_URL")
    if slack_trigger_url and prev_data["donationCount"] != data["donationCount"]:
        requests.post(
            slack_trigger_url,
            json={
                "message": message,
            })

    with open("data/output.json", "w") as fh:
        json.dump(data, fh, indent=4)


if __name__ == "__main__":
    run()
