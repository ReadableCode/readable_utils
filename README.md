# readable_utils

A Python package of small helpers shared by my own projects: logging and
pretty printing, date conversions, pandas cleanup, Google Sheets, Drive, Docs
and Gmail, Postgres, S3, ntfy notifications, Android file transfer over adb,
and the host inventory, SSH and host-stats plumbing used by my homelab tools.

It exists because these helpers used to be copied into each repo as
`src/utils/`, and the copies drifted apart. Now each project depends on a
pinned git tag of this package instead, so a fix lands once and every
consumer picks it up when it chooses to bump.

It is a library only. There is no app, CLI or service, apart from
`json_tools`, which can also be run as a script.

## What is in it

All modules live under `readable_utils.` (for example
`from readable_utils.display_tools import print_logger`).

| Module | What it does |
|--------|--------------|
| `display_tools` | Leveled `print_logger` (level from `LOG_LEVEL`), table printing of DataFrames, lists and dicts, progress bars, file-tree printing |
| `date_tools` | Date format shortcuts, mixed-format date parsing, Excel serial date conversion, week, quarter and month helpers, timezone-aware "now" |
| `config_utils` | Finds the consumer project's root (`base_dir`) and the standard directories under it (see Path semantics) |
| `host_tools` | Uppercase local hostname from `HOSTNAME`, `COMPUTERNAME` or the socket |
| `math_tools` | Arithmetic that passes an `"ERROR"` value through instead of raising |
| `number_tools` | Percent-string repair, forced numeric conversion, number and percent formatting |
| `pandas_tools` | Column comparison, merge that also returns unmatched rows, CSV reads that survive decode errors, string sanitizing, schema generation and application |
| `doc_tools` | Links and spreadsheet link formulas for git files, Sheets and Drive folders, markdown line builders |
| `android_tools` | List, copy to, copy from and delete files on an Android device through `adb` on `PATH` |
| `json_tools` | Sorts lists of objects by `id` or `name` so exported JSON diffs cleanly; `python -m readable_utils.json_tools <file-or-dir> ...` rewrites files in place |
| `inventory_tools` | Discovers sibling `*_credentials` repos and resolves host records from their `hosts.json` files |
| `ssh_tools` | Builds one ssh argv for unattended connections, or a local shell argv when the target is this machine |
| `host_stats_tools` | A one-line remote probe for disk, CPU and memory, its parser, and terminal meter rendering |
| `design_tokens` | The "terminal navy" color palette as constants, plus a Textual theme |
| `google_tools` | Google Sheets through pygsheets: open books and sheets by name or id, read to DataFrames, write DataFrames, clear and copy ranges |
| `google_drive_tools` | Drive: walk folder paths, list, download, upload, rename, share, report uploads (CSV, HTML, Excel), storage usage |
| `google_doc_tools` | Read and append to Google Docs |
| `gmail_tools` | Send mail with attachments, pull attachments, addresses and bodies from a search |
| `postgres_tools` | Connection pools, database creation, queries, a heartbeat table |
| `s3_tools` | Bucket creation, listing, upload and download against any S3 endpoint (for example MinIO) |
| `ntfy_tools` | Send to and read from an ntfy topic |

## Installing in a consumer repo

Depend on it straight from git (no PyPI involved), pinned to a tag, with only
the extras that repo needs:

```bash
uv add "readable-utils[s3] @ git+ssh://git@github.com/ReadableCode/readable_utils.git" --tag v0.1.0
```

That records the tag in `pyproject.toml` (`[tool.uv.sources]`) and the exact
commit SHA in `uv.lock`. The consumer never moves until you bump its tag and
`uv lock`, no matter what happens on master here. Python 3.10 or newer.

| Extra | Enables | Pulls in |
|-------|---------|----------|
| (base) | `display_tools`, `date_tools`, `config_utils`, `host_tools`, `math_tools`, `number_tools`, `pandas_tools`, `doc_tools`, `android_tools`, `json_tools`, `inventory_tools`, `ssh_tools`, `host_stats_tools`, `design_tokens` | pandas, python-dotenv, pytz, tabulate |
| `google` | `google_tools`, `google_drive_tools`, `google_doc_tools`, `gmail_tools` | pygsheets, google api/auth clients, dateutil, pyyaml |
| `postgres` | `postgres_tools` | psycopg2-binary |
| `s3` | `s3_tools` | boto3 |
| `ntfy` | `ntfy_tools` | requests |
| `all` | everything | all of the above |

`host_stats_tools` imports rich and `design_tokens` imports textual only
inside the functions that render, so neither is a dependency here; callers
that render bring their own.

## Configuration

The service modules read settings from the environment, loading the
consumer project's `.env` first if there is one:

| Module | Settings |
|--------|----------|
| `google_tools`, `google_drive_tools`, `google_doc_tools` | `GOOGLE_SERVICE_ACCOUNT` (service account JSON), or `service_account_credentials.json` in the project root |
| `gmail_tools` | `gmail_oauth_<account>.json` and `gmail_token_<account>.json` in the project root; `GMAIL_OAUTH_<ACCOUNT>` and `GMAIL_TOKEN_<ACCOUNT>` can supply them and are written to those files |
| `postgres_tools` | `POSTGRES_URL`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| `s3_tools` | `S3_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` |
| `ntfy_tools` | `NTFY_URL`, `NTFY_USERNAME`, `NTFY_PASSWORD` |
| `display_tools` | `LOG_LEVEL` (default `info`) |
| `config_utils` | `READABLE_UTILS_BASE_DIR` (optional root override) |

## Herd-infrastructure modules (v0.3.0)

Four stdlib-only modules shared by the herdstone and status_board repos so
inventory and SSH behavior can't drift between them:

- `inventory_tools`: `*_credentials` sibling-repo discovery
  (`find_credentials_dirs`, `credentials_context`, `overlay_context`,
  `find_inventory_paths`) and hosts.json record resolution
  (`load_inventory_hosts`, `find_host_record`, matching name or alias,
  case-insensitive).
- `ssh_tools`: one `build_ssh_argv` for every unattended connection:
  BatchMode/accept-new base options, `-J` jump-hop injection (skipped when
  this machine IS the jump host), `identity_file`/`port` support, and a
  local-execution short-circuit that returns a plain shell argv when the
  target is this machine.
- `host_stats_tools`: the `@@STATS@@` per-physical-drive disk/cpu/mem
  one-liner probe (`HOST_STATS_COMMAND`, `split_host_stats`,
  `parse_host_stats`) and the htop-style green to yellow to red meter
  rendering (`stats_renderable`; rich is imported lazily, only by callers
  that render).
- `design_tokens`: the "terminal navy" palette constants plus
  `terminal_navy_textual_theme()` (textual imported lazily).

## Migrating a repo off its vendored copy

1. `uv add` as above with the extras the repo's imports need.
2. Rewrite imports: `from utils.x import y` becomes
   `from readable_utils.x import y`.
3. Delete the repo's `src/utils/` directory.
4. Run the app; commit.

## Path semantics (changed from the vendored copies)

Vendored copies derived the repo root from their own location
(`<repo>/src/utils/`, so the grandparent). Installed in a venv that is
meaningless, so `config_utils` now finds the project root (`base_dir`) by
**walking up from the current working directory** until it hits a repo-root
marker (`pyproject.toml`, `uv.lock`, `.git`, or `.env`). Scripts, code cells
and notebooks therefore resolve the same root from anywhere inside the repo,
including cells run from `src/`. Set `READABLE_UTILS_BASE_DIR` to override;
if no marker is found the current working directory is used as-is. The old
names (`parent_dir`, `grandparent_dir`, `data_dir`, `log_dir`, ...) still
exist as aliases off `base_dir`, so vendored-era code keeps working.
`file_dir` now points at the installed package, for data files shipped
inside it (the vendored-era home of `date_tools`' `df_*.csv` tables).

## Versioning workflow

- Change whatever you want on `master`; consumers are pinned and unaffected.
- When ready: bump `version` in `pyproject.toml`, `git tag vX.Y.Z`,
  `git push --tags`.
- In a consumer, bump the tag in `[tool.uv.sources]` and run
  `uv lock && uv sync`.
- Never delete or move old tags; old consumers resolve against them forever.
