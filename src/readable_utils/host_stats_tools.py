# %%
# Imports #

import colorsys
import re

# %%
# Variables #

# One machine-readable line of host stats appended to (or standing in for) a
# remote command. Reads only numbers the kernel already maintains - df for
# every mounted filesystem, rolled up to one figure per physical drive, the
# 1/5/15-minute CPU load averages top's header shows (so a 5-minute refresh
# reads the 5-minute column with nothing tracked on the host), and current
# memory (neither kernel keeps a memory average, so that one is a
# point-in-time reading). The caller strips this line off the output and
# renders it locally as meter bars, so the meters look identical everywhere
# they appear.
#
# Disks are physical drives, not mounts: a host with a boot ssd and an 8T
# data drive shows two meters, while the dozen partitions and volumes a
# modern OS mounts off one drive fold into that drive's single figure. On
# Linux every df row backed by a /dev block device is walked up
# lsblk's PKNAME chain (partition, lvm, md ...) to the whole disk, and only
# whole disks with a /sys/block/<name>/device (real hardware or a VM's
# virtual disk - never loop, zram or ram) count. On macOS the physical set
# is `diskutil list physical` (internal and external, never a disk image or
# synthesized container), each df row resolves through `diskutil info` from
# its APFS container to the physical store's whole disk, and the volumes
# macOS mounts under /System/Volumes plus the Recovery volume are skipped
# as they belong to the OS, not the user.
#
# Used is computed as total-minus-available, NOT df's own Used column. On
# macOS every volume of an APFS container reports the container's total and
# available, so a container is counted once (the first volume seen) and its
# volumes' Used columns are never summed - reading Used on the sealed system
# volume reports a 5%-full disk that is really 85% full; on Linux the
# subtraction additionally counts the root-reserved blocks df hides from
# Used, which belong in a "space you can't use" meter. Each drive is labeled
# with the shortest mount point it carries ("/" for the boot drive), and
# drives sort by that label so the boot drive leads.
#
# POSIX sh, and portable across Linux and macOS: df -Pk and getconf are the
# same on both, no `case` anywhere because the Mac's sh is bash 3.2 and it
# cannot parse a case pattern's `)` inside command substitution (grep does
# the matching instead), while disks, load and memory branch on whether the Linux
# source exists. On macOS the load and memory fallbacks are sysctl
# vm.loadavg ("{ 1.2 3.4 5.6 }") and vm_stat, whose used-memory figure is
# the Activity Monitor definition - active + wired + compressor-occupied
# pages, scaled by the page size vm_stat names in its own header (16K on
# Apple silicon, 4K on Intel) - against hw.memsize for the total. vm_stat
# prints page counts with a trailing period, hence the gsub scrubbing
# before the arithmetic. awk printf uses %.0f, not %d, because mawk (Ubuntu's
# default awk) clamps %d at 2^31 and a kilobyte count for an 8T drive is
# past that.
STATS_MARKER = "@@STATS@@"
# df rows for block devices as "device<TAB>total_kb<TAB>avail_kb<TAB>mount",
# the mount reassembled from field 6 onward so a mount point with spaces
# ("/Volumes/My Passport") survives.
_DF_SNIPPET = (
    "df -Pk | awk 'NR>1 && $1 ~ /^\\/dev\\//{m=$6; for(i=7;i<=NF;i++) m=m\" \"$i; "
    "printf \"%s\\t%s\\t%s\\t%s\\n\", $1, $2, $4, m}'"
)
# Per df row, emit "drive<TAB>fs<TAB>total<TAB>avail<TAB>mount" where drive is
# the physical whole disk and fs is the dedup key (the device on Linux, the
# APFS container on macOS).
_LINUX_DRIVES_SNIPPET = (
    "while IFS=\"$(printf '\\t')\" read -r dev total avail mnt; do "
    "name=$(readlink -f \"$dev\"); name=${name#/dev/}; "
    "while [ ! -d \"/sys/block/$name\" ]; do "
    "parent=$(lsblk -rno PKNAME \"/dev/$name\" 2>/dev/null | head -n 1); "
    "[ -n \"$parent\" ] || break; name=$parent; done; "
    "[ -e \"/sys/block/$name/device\" ] || continue; "
    "printf '%s\\t%s\\t%s\\t%s\\t%s\\n' \"$name\" \"$dev\" \"$total\" \"$avail\" \"$mnt\"; done"
)
_MAC_DRIVES_SNIPPET = (
    "physical=\" $(diskutil list physical | sed -n 's/^\\(\\/dev\\/disk[0-9]*\\) .*/\\1/p' | tr '\\n' ' ')\"; "
    "while IFS=\"$(printf '\\t')\" read -r dev total avail mnt; do "
    "printf '%s\\n' \"$mnt\" | grep -q '^/System/Volumes/\\|^/Volumes/Recovery$' && continue; "
    "info=$(diskutil info \"$dev\" 2>/dev/null) || continue; "
    "container=$(printf '%s\\n' \"$info\" | sed -n 's/.*Part of Whole: *//p' | head -n 1); "
    "store=$(printf '%s\\n' \"$info\" | sed -n 's/.*APFS Physical Store: *//p' | head -n 1); "
    "whole=/dev/$(printf '%s' \"${store:-$container}\" | sed 's/s[0-9]*$//'); "
    "printf '%s' \"$physical\" | grep -qF \" $whole \" || continue; "
    "printf '%s\\t%s\\t%s\\t%s\\t%s\\n' \"$whole\" \"$container\" \"$total\" \"$avail\" \"$mnt\"; done"
)
# Count each fs once, sum per drive, label each drive with its shortest mount,
# then "label:used/total|label:used/total" sorted by label.
_ROLLUP_SNIPPET = (
    "awk -F'\\t' '{ if (!($2 in seen)) { seen[$2]=1; u[$1]+=$3-$4; t[$1]+=$3 } "
    "if (!($1 in l) || length($5)<length(l[$1])) l[$1]=$5 } "
    "END { for (d in u) printf \"%s\\t%.0f\\t%.0f\\n\", l[d], u[d], t[d] }' | sort "
    "| awk -F'\\t' '{ printf \"%s%s:%s/%s\", (NR>1?\"|\":\"\"), $1, $2, $3 }'"
)
_DISK_SNIPPET = (
    f"{_DF_SNIPPET} | if [ -d /sys/block ]; then {_LINUX_DRIVES_SNIPPET}; else {_MAC_DRIVES_SNIPPET}; fi "
    f"| {_ROLLUP_SNIPPET}"
)
_LOAD_SNIPPET = (
    "if [ -r /proc/loadavg ]; then cut -d' ' -f1-3 /proc/loadavg | tr ' ' ','; "
    "else sysctl -n vm.loadavg | awk '{print $2\",\"$3\",\"$4}'; fi"
)
_MEM_SNIPPET = (
    "if command -v free >/dev/null 2>&1; then free -m | awk 'NR==2{print $3\"/\"$2}'; "
    "else vm_stat | awk -v t=\"$(sysctl -n hw.memsize)\" "
    "'/page size of/{gsub(/[^0-9]/,\"\",$8);ps=$8} "
    "/Pages active/{gsub(/\\./,\"\",$3);a=$3} "
    "/Pages wired down/{gsub(/\\./,\"\",$4);w=$4} "
    "/occupied by compressor/{gsub(/\\./,\"\",$5);c=$5} "
    "END{printf \"%d/%d\",(a+w+c)*ps/1048576,t/1048576}'; fi"
)
# disk goes last: its labels are mount points that may hold spaces, and the
# parser splits fields on " name=" so a label never ends a field early.
HOST_STATS_COMMAND = (
    f"printf '{STATS_MARKER} load=%s cpu=%s mem=%s disk=%s\\n' "
    f"\"$({_LOAD_SNIPPET})\" "
    "\"$(getconf _NPROCESSORS_ONLN)\" "
    f"\"$({_MEM_SNIPPET})\" "
    f"\"$({_DISK_SNIPPET})\""
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
    ``@@STATS@@ load=1m,5m,15m cpu=n mem=used_mb/total_mb disk=label:used_kb/total_kb|...``
    -> structured dict, or None when any field is missing/garbled (a partial
    stats line renders as "unavailable" rather than taking the caller down).
    ``disks`` is one entry per physical drive in the collector's order (boot
    drive first); an empty ``disk=`` (a host where no drive resolved) is a
    valid, empty list.
    """
    try:
        fields = dict(re.findall(r"(\w+)=(.*?)(?= \w+=|$)", line[len(STATS_MARKER):].strip()))
        disks = []
        for entry in filter(None, fields["disk"].split("|")):
            label, _, figures = entry.rpartition(":")
            used, total = (int(value) for value in figures.split("/"))
            disks.append({"label": label, "used_kb": used, "total_kb": total})
        mem_used, mem_total = (int(value) for value in fields["mem"].split("/"))
        load_1m, load_5m, load_15m = (float(value) for value in fields["load"].split(","))
        return {
            "disks": disks,
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
    htop-style meters for a parsed host-stats dict as a rich Text: one line
    per physical drive (labels padded so the bars align), then a line with
    CPU (5-minute load average over core count - the kernel's own average
    for a 5-minute refresh) and current memory. Rendered identically wherever
    host stats appear.
    """
    from rich.text import Text

    if not stats:
        return Text("host stats unavailable", style="dim italic")
    text = Text()
    labels = [f"disk {disk['label']}" for disk in stats["disks"]]
    width = max((len(label) for label in labels), default=0)
    for label, disk in zip(labels, stats["disks"]):
        fraction = disk["used_kb"] / (disk["total_kb"] or 1)
        append_meter(
            text, label.ljust(width), fraction,
            f"{fraction:>4.0%} {disk['used_kb'] / 1048576:.0f}G of {disk['total_kb'] / 1048576:.0f}G",
        )
        text.append("\n")
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
