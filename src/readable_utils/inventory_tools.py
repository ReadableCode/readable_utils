# %%
# Imports #

import glob
import json
import os

# %%
# Variables #

CREDENTIALS_SUFFIX = "_credentials"

# %%
# Credentials-repo discovery #


def find_credentials_dirs(credentials_root):
    """
    Return every sibling credentials repo under credentials_root: directories
    named ``<context>_credentials`` (e.g. ``personal_credentials``,
    ``acme_credentials``). Sorted for determinism.
    """
    pattern = os.path.join(glob.escape(credentials_root), f"*{CREDENTIALS_SUFFIX}")
    return [path for path in sorted(glob.glob(pattern)) if os.path.isdir(path)]


def credentials_context(credentials_dir):
    """Context token of a credentials repo: its directory name minus the ``_credentials`` suffix."""
    return os.path.basename(os.path.normpath(credentials_dir))[: -len(CREDENTIALS_SUFFIX)]


def overlay_context(overlay_dir):
    """
    Context token of any config-contributing repo: a ``*_credentials`` repo
    drops the suffix (``acme_credentials`` -> ``acme``), any other repo is its
    own directory name (``acme_dev`` -> ``acme_dev``).
    """
    name = os.path.basename(os.path.normpath(overlay_dir))
    return name[: -len(CREDENTIALS_SUFFIX)] if name.endswith(CREDENTIALS_SUFFIX) else name


def find_inventory_paths(credentials_root):
    """
    Locate the host inventory file of every ``*_credentials`` repo under
    credentials_root. Each repo may declare ``<context>_hosts.json``, falling
    back to legacy ``hosts.json`` when the prefixed file is absent; repos with
    neither contribute nothing.
    """
    paths = []
    for credentials_dir in find_credentials_dirs(credentials_root):
        context = credentials_context(credentials_dir)
        for filename in (f"{context}_hosts.json", "hosts.json"):
            path = os.path.join(credentials_dir, filename)
            if os.path.exists(path):
                paths.append(path)
                break
    return paths


# %%
# Host records #


def load_inventory_hosts(inventory_path):
    """Parse one hosts.json-style inventory and return its full host records (dicts)."""
    with open(inventory_path, "r", encoding="utf-8") as file_handle:
        inventory = json.load(file_handle)
    return inventory.get("hosts", [])


def host_names(host):
    """A host record's resolvable names: its ``name`` plus every alias (blanks dropped)."""
    return [name for name in [host.get("name", "")] + list(host.get("aliases", [])) if name]


def find_host_record(token, inventory_paths):
    """
    Resolve a host token (inventory ``name`` or one of its ``aliases``,
    case-insensitive) to its full inventory record, searching inventory_paths
    in order. Raises ValueError when no inventory knows the token.
    """
    wanted = token.strip().lower()
    for path in inventory_paths:
        for host in load_inventory_hosts(path):
            if any(name.lower() == wanted for name in host_names(host)):
                return host
    raise ValueError(
        f"Host '{token}' not found in any host inventory "
        f"({', '.join(inventory_paths) or 'no inventories found'})"
    )


# %%
