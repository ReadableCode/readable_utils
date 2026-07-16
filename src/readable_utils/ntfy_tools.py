# %%
# Imports #

import os
import sys

import requests
from dotenv import load_dotenv

# append grandparent
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from readable_utils.config_utils import data_dir, file_dir, grandparent_dir  # noqa: F401
from readable_utils.display_tools import pprint_df, pprint_ls, print_logger  # noqa: F401

# %%
# Load Environment #

# source .env file
dotenv_path = os.path.join(grandparent_dir, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

NTFY_URL = os.getenv("NTFY_URL")
NTFY_USERNAME = os.getenv("NTFY_USERNAME")
NTFY_PASSWORD = os.getenv("NTFY_PASSWORD")

# print both
# print("Ntfy Configuration:")
# print(f"NTFY_URL: {NTFY_URL}")
# print(f"NTFY_USERNAME: {NTFY_USERNAME}")
# print(f"NTFY_PASSWORD: {NTFY_PASSWORD}")

# %%
# Google Credentials #


# print("Sample curl command:")
# print(
#     f"curl -u {NTFY_USERNAME}:'{NTFY_PASSWORD}' -X POST -d \"message=Your notification message\" {NTFY_URL}/house_power"
# )

# %%
# Functions #


def check_for_notifications(topic):
    topic_url = f"{NTFY_URL}/{topic}/json?poll=1"
    response = requests.get(topic_url, auth=(NTFY_USERNAME, NTFY_PASSWORD), stream=True)
    for line in response.iter_lines():
        if line:
            print(line)


def send_notification(topic, message):
    """Send a notification using Ntfy with username and password."""
    topic_url = f"{NTFY_URL}/{topic}"
    response = requests.post(
        topic_url, auth=(NTFY_USERNAME, NTFY_PASSWORD), data={"message": message}
    )
    return response.status_code == 200


# %%
# Main #


if __name__ == "__main__":
    send_notification("house_power", "Time to do the dishes!")
    check_for_notifications("house_power")


# %%
