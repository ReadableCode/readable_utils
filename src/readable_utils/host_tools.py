# %%
# Imports #

import os
import platform
import socket

# %%
# Functions #


def get_uppercase_hostname():
    """
    The local machine's uppercase hostname: the HOSTNAME env var when set,
    else COMPUTERNAME on Windows, else socket.gethostname(). Callers that
    compare against inventory names use the short pre-dot name, so only that
    part needs to be stable.
    """
    hostname = os.getenv("HOSTNAME")
    if hostname is None and platform.system().upper() == "WINDOWS":
        hostname = os.environ.get("COMPUTERNAME")
    if hostname is None:
        hostname = socket.gethostname()
    return hostname.upper() if hostname else ""


# %%
