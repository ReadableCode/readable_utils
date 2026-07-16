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
# package that trick no longer works, so the root is the current working
# directory (run your scripts from the repo root, as before) or an explicit
# READABLE_UTILS_BASE_DIR override.
base_dir = os.path.abspath(os.environ.get("READABLE_UTILS_BASE_DIR", os.getcwd()))

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
for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == "__main__":
    print(f"home_dir: {home_dir}")
    print(f"file_dir: {file_dir}")
    print(f"base_dir: {base_dir}")
    print(f"data_dir: {data_dir}")


# %%
