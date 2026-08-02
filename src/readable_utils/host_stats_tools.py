# %%
# Imports #

import colorsys

# %%
# Variables #

# One machine-readable line of host stats appended to (or standing in for) a
# remote command. Reads only numbers the kernel already maintains - df for
# the root filesystem, /proc/loadavg (the same 1/5/15-minute CPU averages
# top's header shows, so a 5-minute refresh reads the 5-minute column with
# nothing tracked on the host), and free for current memory (Linux keeps no
# memory average, so that one is a point-in-time reading). Linux hosts only.
# The caller strips this line off the output and renders it locally as meter
# bars, so the meters look identical everywhere they appear.
STATS_MARKER = "@@STATS@@"
HOST_STATS_COMMAND = (
    f"printf '{STATS_MARKER} disk=%s load=%s cpu=%s mem=%s\\n' "
    "\"$(df -Pk / | awk 'NR==2{print $3\"/\"$2}')\" "
    "\"$(cut -d' ' -f1-3 /proc/loadavg | tr ' ' ',')\" "
    "\"$(nproc)\" "
    "\"$(free -m | awk 'NR==2{print $3\"/\"$2}')\""
)

METER_WIDTH = 22
METER_FILLED, METER_EMPTY = "█", "░"


# %%
# Parsing #


def split_host_stats(output):
    """
    Split the trailing STATS_MARKER line off a command's output and parse it,
    returning (body, stats_dict_or_None). When the last line isn't the marker
    - the remote command somehow swallowed it - the output is returned
    untouched with no stats.
    """
    body, _, last = output.rpartition("\n")
    if not last.startswith(STATS_MARKER):
        return output, None
    return body.rstrip(), parse_host_stats(last)


def parse_host_stats(line):
    """
    ``@@STATS@@ disk=used_kb/total_kb load=1m,5m,15m cpu=n mem=used_mb/total_mb``
    -> structured dict, or None when any field is missing/garbled (a partial
    stats line renders as "unavailable" rather than taking the caller down).
    """
    try:
        fields = dict(item.split("=", 1) for item in line.split()[1:])
        disk_used, disk_total = (int(value) for value in fields["disk"].split("/"))
        mem_used, mem_total = (int(value) for value in fields["mem"].split("/"))
        load_1m, load_5m, load_15m = (float(value) for value in fields["load"].split(","))
        return {
            "disk_used_kb": disk_used,
            "disk_total_kb": disk_total,
            "load": (load_1m, load_5m, load_15m),
            "cpus": int(fields["cpu"]),
            "mem_used_mb": mem_used,
            "mem_total_mb": mem_total,
        }
    except (KeyError, ValueError):
        return None


# %%
# Meter rendering (rich imported lazily - only callers that render need it) #


def ramp_style(fraction):
    """
    Hex color for a 0..1 fullness fraction: a smooth green -> yellow -> red
    HSV ramp (hue 120° down to 0°), the same scale htop paints its meters
    with - calm at empty, alarming at full.
    """
    fraction = min(max(fraction, 0.0), 1.0)
    hue = (1.0 - fraction) * 120.0 / 360.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.75, 0.95)
    return f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"


def append_meter(text, label, fraction, value):
    """
    Append one htop-style meter to a rich Text: dim label, bracketed gradient
    bar (each filled cell colored by its own position on the ramp, so the bar
    visibly "heats up" as it fills), and the value readout colored by the
    overall fullness.
    """
    fraction = min(max(fraction, 0.0), 1.0)
    text.append(f"{label} ", style="bold")
    text.append("▕", style="grey35")
    filled = round(fraction * METER_WIDTH)
    for cell in range(METER_WIDTH):
        if cell < filled:
            text.append(METER_FILLED, style=ramp_style((cell + 0.5) / METER_WIDTH))
        else:
            text.append(METER_EMPTY, style="grey30")
    text.append("▏", style="grey35")
    text.append(f" {value}", style=ramp_style(fraction))


def stats_renderable(stats):
    """
    One rich-Text line of htop-style meters for a parsed host-stats dict:
    disk on /, CPU (5-minute load average over core count - the kernel's own
    average for a 5-minute refresh), and current memory. Rendered identically
    wherever host stats appear.
    """
    from rich.text import Text

    if not stats:
        return Text("host stats unavailable", style="dim italic")
    text = Text()
    disk_fraction = stats["disk_used_kb"] / (stats["disk_total_kb"] or 1)
    append_meter(
        text, "disk /", disk_fraction,
        f"{disk_fraction:>4.0%} {stats['disk_used_kb'] / 1048576:.0f}G of {stats['disk_total_kb'] / 1048576:.0f}G",
    )
    text.append("    ")
    load_1m, load_5m, load_15m = stats["load"]
    cpus = stats["cpus"] or 1
    append_meter(
        text, "cpu", load_5m / cpus,
        f"{load_5m / cpus:>4.0%} load {load_1m:.2f} {load_5m:.2f} {load_15m:.2f} · {cpus} cores",
    )
    text.append("    ")
    mem_fraction = stats["mem_used_mb"] / (stats["mem_total_mb"] or 1)
    append_meter(
        text, "mem", mem_fraction,
        f"{mem_fraction:>4.0%} {stats['mem_used_mb'] / 1024:.1f}G of {stats['mem_total_mb'] / 1024:.1f}G",
    )
    return text


# %%
