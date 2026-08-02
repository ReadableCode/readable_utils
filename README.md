# readable_utils

The shared utility belt that was previously vendored as `src/utils/` in each
consuming repo, packaged so consumers depend on a pinned version instead of
carrying drifting copies.

## Installing in a consumer repo

Depend on it straight from git (no PyPI involved), pinned to a tag, with only
the extras that repo needs:

```bash
uv add "readable-utils[s3] @ git+ssh://git@github.com/ReadableCode/readable_utils.git" --tag v0.1.0
```

That records the tag in `pyproject.toml` (`[tool.uv.sources]`) and the exact
commit SHA in `uv.lock` — the consumer never moves until you bump its tag and
`uv lock`, no matter what happens on master here.

| Extra | Enables | Pulls in |
|-------|---------|----------|
| (base) | `display_tools`, `date_tools`, `config_utils`, `host_tools`, `math_tools`, `number_tools`, `pandas_tools`, `doc_tools`, `android_tools`, `json_tools`, `inventory_tools`, `ssh_tools`, `host_stats_tools`, `design_tokens` | pandas, python-dotenv, pytz, tabulate |
| `google` | `google_tools`, `google_drive_tools`, `google_doc_tools`, `gmail_tools` | pygsheets, google api/auth clients, dateutil, pyyaml |
| `postgres` | `postgres_tools` | psycopg2-binary |
| `s3` | `s3_tools` | boto3 |
| `ntfy` | `ntfy_tools` | requests |
| `all` | everything | all of the above |

## Herd-infrastructure modules (v0.3.0)

Four stdlib-only modules shared by the herdstone and status_board repos so
inventory/SSH behavior can't drift between them:

- `inventory_tools` — `*_credentials` sibling-repo discovery
  (`find_credentials_dirs`, `credentials_context`, `overlay_context`,
  `find_inventory_paths`) and hosts.json record resolution
  (`load_inventory_hosts`, `find_host_record` — name/alias,
  case-insensitive).
- `ssh_tools` — one `build_ssh_argv` for every unattended connection:
  BatchMode/accept-new base options, `-J` jump-hop injection (skipped when
  this machine IS the jump host), `identity_file`/`port` support, and a
  local-execution short-circuit that returns a plain shell argv when the
  target is this machine.
- `host_stats_tools` — the `@@STATS@@` disk/cpu/mem one-liner probe
  (`HOST_STATS_COMMAND`, `split_host_stats`, `parse_host_stats`) and the
  htop-style green→yellow→red meter rendering (`stats_renderable`; rich is
  imported lazily, only by callers that render).
- `design_tokens` — the "terminal navy" palette constants plus
  `terminal_navy_textual_theme()` (textual imported lazily).

## Migrating a repo off its vendored copy

1. `uv add` as above with the extras the repo's imports need.
2. Rewrite imports: `from utils.x import y` → `from readable_utils.x import y`.
3. Delete the repo's `src/utils/` directory.
4. Run the app; commit.

## Path semantics (changed from the vendored copies)

Vendored copies derived the repo root from their own location
(`<repo>/src/utils/` → grandparent). Installed in a venv that is meaningless,
so `config_utils` now finds the project root (`base_dir`) by **walking up
from the current working directory** until it hits a repo-root marker
(`pyproject.toml`, `uv.lock`, `.git`, or `.env`). Scripts, code cells, and
notebooks therefore resolve the same root from anywhere inside the repo —
including cells run from `src/`. Set `READABLE_UTILS_BASE_DIR` to override;
if no marker is found the current working directory is used as-is. The old names (`parent_dir`,
`grandparent_dir`, `data_dir`, `log_dir`, ...) still exist as aliases off
`base_dir`, so vendored-era code keeps working. `file_dir` now points at the
installed package (where `date_tools`' `df_*.csv` tables ship as package
data).

## Versioning workflow

- Change whatever you want on `master` — consumers are pinned and unaffected.
- When ready: bump `version` in `pyproject.toml`, `git tag vX.Y.Z`,
  `git push --tags`.
- In a consumer, bump the tag in `[tool.uv.sources]` and run
  `uv lock && uv sync`.
- Never delete or move old tags; old consumers resolve against them forever.
