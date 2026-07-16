# %%
# Imports #

import os
from os.path import expanduser

# %%
# Paths #

home_dir = expanduser("~")

# Directory of this installed package — used for packaged data files
# (e.g. date_tools' df_*.csv). NOT the consumer project's directory.
file_dir = os.path.dirname(os.path.realpath(__file__))

# The consumer project's root. When this code was vendored at
# <repo>/src/utils/, "grandparent_dir" meant the repo root; installed as a
# package that trick no longer works. Instead, walk up from the current
# working directory until a repo-root marker is found — this makes code
# cells / notebooks run from anywhere inside the repo (src/, tests/, ...)
# resolve the same root as a script run from the repo root. An explicit
# READABLE_UTILS_BASE_DIR always wins; if no marker is found, fall back to
# the current working directory.
_ROOT_MARKERS = ("pyproject.toml", "uv.lock", ".git", ".env")


def find_base_dir(start_dir=None):
    env_override = os.environ.get("READABLE_UTILS_BASE_DIR")
    if env_override:
        return os.path.abspath(env_override)
    current = os.path.abspath(start_dir or os.getcwd())
    while True:
        if any(os.path.exists(os.path.join(current, m)) for m in _ROOT_MARKERS):
            return current
        parent = os.path.dirname(current)
        if parent == current:  # filesystem root, no marker found
            return os.path.abspath(start_dir or os.getcwd())
        current = parent


base_dir = find_base_dir()

# Compatibility aliases: vendored callers imported these expecting repo root.
parent_dir = base_dir
grandparent_dir = base_dir
great_grandparent_dir = os.path.dirname(base_dir)

data_dir = os.path.join(base_dir, "data")
templates_dir = os.path.join(base_dir, "templates")
log_dir = os.path.join(base_dir, "logs")
src_dir = os.path.join(base_dir, "src")
src_utils_dir = os.path.join(src_dir, "utils")
drive_download_cache_dir = os.path.join(data_dir, "drive_download_cache")
s3_download_cache = os.path.join(data_dir, "s3_download_cache")
temp_upload_dir = os.path.join(data_dir, "temp_upload")

directories = [
    data_dir,
    templates_dir,
    log_dir,
    drive_download_cache_dir,
    s3_download_cache,
    temp_upload_dir,
]


def ensure_dirs():
    """Create the standard project directories. Called by modules at the point
    they actually write — importing this package never touches the disk."""
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    print(f"home_dir: {home_dir}")
    print(f"file_dir: {file_dir}")
    print(f"base_dir: {base_dir}")
    print(f"data_dir: {data_dir}")


# %%
