# %%
# Imports #

import os
import platform
import socket

from readable_utils.inventory_tools import host_names

# %%
# Variables #

# ssh options used for every unattended connection: never prompt, fail fast
# when a hop is unreachable, and accept-new host keys so a fresh machine with
# the credentials repos cloned works without hand-seeding known_hosts
# (changed keys still hard-fail).
SSH_BASE_OPTIONS = (
    "-T",
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=10",
    "-o", "StrictHostKeyChecking=accept-new",
)

# Lazily-resolved set of this machine's own IP addresses (see is_local_host).
_LOCAL_IPS = None


# %%
# Local-host detection #


def _local_ips():
    global _LOCAL_IPS
    if _LOCAL_IPS is None:
        ips = {"127.0.0.1", "::1"}
        try:
            ips |= {addr[4][0] for addr in socket.getaddrinfo(socket.gethostname(), None)}
        except socket.gaierror:
            pass
        _LOCAL_IPS = ips
    return _LOCAL_IPS


def is_local_host(hostname):
    """
    True when hostname refers to this machine (loopback, the local hostname,
    or a name/IP that resolves to one of this machine's addresses) - the
    ansible_connection=local idea, so callers can run the command directly
    instead of ssh-ing to themselves.
    """
    if not hostname:
        return False
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return True
    local_hostname = socket.gethostname().lower()
    if hostname.lower() == local_hostname:
        return True
    if hostname.lower().split(".")[0] == local_hostname.split(".")[0]:
        return True
    try:
        target_ips = {addr[4][0] for addr in socket.getaddrinfo(hostname, None)}
    except socket.gaierror:
        return False
    return bool(target_ips & _local_ips())


def host_matches_local(host, local_hostname):
    """
    True when a host record IS the machine named local_hostname, compared by
    inventory name/aliases (short pre-dot names, case-insensitive). This is
    the DNS-free check: an inventory name match needs no resolution, so it is
    safe to run on every fetch.
    """
    if not local_hostname:
        return False
    local_short = local_hostname.split(".")[0].lower()
    return local_short in [name.split(".")[0].lower() for name in host_names(host)]


# %%
# Argv construction #


def ssh_destination(host):
    """user@hostname for a host record (user optional in the record)."""
    user = host.get("user")
    return f"{user}@{host['hostname']}" if user else host["hostname"]


def local_shell_argv(command):
    """The argv that runs command in this machine's shell (no SSH)."""
    if platform.system().lower() == "windows":
        return ["cmd", "/c", command]
    return ["sh", "-c", command]


def build_ssh_argv(host, command, jump=None, local_hostname="", options=SSH_BASE_OPTIONS):
    """
    Build the full argv that runs ``command`` on ``host`` (an inventory
    record), through the optional ``jump`` record.

    - When the target IS this machine (inventory-name match against
      local_hostname, or a hostname that resolves locally), returns a plain
      local shell argv - no SSH to yourself.
    - The jump hop is injected as ``-J user@host:port`` so the chain lives
      entirely in config + inventory - deliberately NOT in any machine's
      ~/.ssh/config - and is skipped when this machine IS the jump host.
    - ``identity_file`` and non-default ``port`` on either record are honored
      (``-i`` / ``-p`` for the target, ``:port`` in the ``-J`` spec).
    """
    if host_matches_local(host, local_hostname) or is_local_host(host.get("hostname", "")):
        return local_shell_argv(command)
    argv = ["ssh", *options]
    if jump and not host_matches_local(jump, local_hostname) and not is_local_host(jump.get("hostname", "")):
        spec = ssh_destination(jump)
        if jump.get("port"):
            spec += f":{jump['port']}"
        argv += ["-J", spec]
    if host.get("identity_file"):
        argv += ["-i", os.path.expanduser(host["identity_file"])]
    if host.get("port"):
        argv += ["-p", str(host["port"])]
    argv += [ssh_destination(host), command]
    return argv


# %%
