#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ariel
# SPDX-License-Identifier: GPL-3.0-or-later
"""List every non-hub USB device with its negotiated link speed.

Reads sysfs and /proc directly - no lsblk or lsusb parsing. Link speeds
are shown as the negotiated generation plus its raw bitrate, which makes
a silent USB 2.0 fallback obvious at a glance.

With -s / --include-storage, also lists block devices with their link
speed, size and mountpoints, resolving stacked devices (partitions, LUKS,
LVM, md) back to the underlying disk.

Usage:
    usb-speeds.py [-s|--include-storage]
"""

import os
import re
import sys

SYS_BLOCK = "/sys/block"
SYS_USB = "/sys/bus/usb/devices"

USB_SPEEDS = {
    "1.5": "USB1.0 (1.5Mb/s)",
    "12": "USB1.1 (12Mb/s)",
    "480": "USB2.0 (480Mb/s)",
    "5000": "USB3.2 Gen1 (5Gb/s)",
    "10000": "USB3.2 Gen2 (10Gb/s)",
    "20000": "USB3.2 Gen2x2 (20Gb/s)",
    "40000": "USB4 (40Gb/s)",
}

USB_CLASSES = {
    "01": "Audio", "02": "Comm", "03": "HID", "05": "Physical",
    "06": "Image", "07": "Printer", "08": "Storage", "09": "Hub",
    "0a": "CDCData", "0b": "SmartCard", "0d": "Security", "0e": "Video",
    "0f": "Health", "10": "AV", "dc": "Diag", "e0": "Wireless",
    "ef": "Misc", "fe": "AppSpec", "ff": "Vendor",
}


def read(*parts):
    """Read a sysfs attribute, returning '' if it doesn't exist."""
    try:
        with open(os.path.join(*parts)) as fh:
            return fh.read().strip()
    except OSError:
        return ""


def human(sectors):
    size = int(sectors) * 512
    for unit in ("B", "K", "M", "G", "T", "P"):
        if size < 1024 or unit == "P":
            return f"{size:.1f}{unit}".replace(".0", "")
        size /= 1024


def speed_label(raw):
    return USB_SPEEDS.get(raw, f"{raw}M")


def usb_parent(device_path):
    """Walk up the sysfs chain looking for a USB device node."""
    path = os.path.realpath(device_path)
    while path and path != "/":
        if os.path.exists(os.path.join(path, "speed")):
            return path
        path = os.path.dirname(path)
    return None


def mountpoints_by_devno():
    """Map 'major:minor' -> [mountpoint, ...] from mountinfo."""
    table = {}
    with open("/proc/self/mountinfo") as fh:
        for line in fh:
            fields = line.split()
            devno, mnt = fields[2], fields[4]
            table.setdefault(devno, []).append(
                mnt.encode().decode("unicode_escape")
            )
    return table


def descendants(block_dir):
    """Yield devno for a disk and everything stacked on it -
    partitions, then dm/md holders, recursively."""
    devno = read(block_dir, "dev")
    if devno:
        yield devno
    for entry in sorted(os.listdir(block_dir)):
        child = os.path.join(block_dir, entry)
        if os.path.exists(os.path.join(child, "partition")):
            yield from descendants(child)
    holders = os.path.join(block_dir, "holders")
    if os.path.isdir(holders):
        for holder in sorted(os.listdir(holders)):
            yield from descendants(os.path.join(SYS_BLOCK, holder))


def disks():
    pattern = re.compile(r"^(sd[a-z]+|nvme\d+n\d+|mmcblk\d+|vd[a-z]+)$")
    return sorted(d for d in os.listdir(SYS_BLOCK) if pattern.match(d))


def collect_storage():
    mounts = mountpoints_by_devno()
    rows = []
    for name in disks():
        block_dir = os.path.join(SYS_BLOCK, name)
        dev_link = os.path.join(block_dir, "device")

        parent = usb_parent(dev_link)
        if parent:
            link = speed_label(read(parent, "speed"))
            model = read(parent, "product") or read(dev_link, "model")
        else:
            real = os.path.realpath(dev_link)
            link = ("NVMe" if "/nvme" in real
                    else "SATA" if "/ata" in real
                    else "-")
            model = " ".join(filter(None, [read(dev_link, "vendor"),
                                           read(dev_link, "model")]))

        where = []
        for devno in descendants(block_dir):
            where.extend(mounts.get(devno, []))

        rows.append([name, link, model or "-",
                     human(read(block_dir, "size")),
                     "  ".join(dict.fromkeys(where))])
    return rows


def usb_sort_key(name):
    bus, _, ports = name.partition("-")
    return (int(bus), [int(p) for p in ports.split(".") if p.isdigit()])


def collect_usb():
    rows = []
    if not os.path.isdir(SYS_USB):
        return rows
    names = [n for n in os.listdir(SYS_USB)
             if ":" not in n and not n.startswith("usb")]
    for name in sorted(names, key=usb_sort_key):
        path = os.path.join(SYS_USB, name)
        if read(path, "bDeviceClass") == "09":   # skip hubs
            continue

        classes = []
        for entry in sorted(os.listdir(path)):
            if entry.startswith(name + ":"):
                code = read(path, entry, "bInterfaceClass")
                label = USB_CLASSES.get(code, code)
                if label and label not in classes:
                    classes.append(label)
        if not classes:
            classes = [USB_CLASSES.get(read(path, "bDeviceClass"), "-")]

        product = read(path, "product") or "{}:{}".format(
            read(path, "idVendor"), read(path, "idProduct"))

        rows.append([name, speed_label(read(path, "speed")),
                     "/".join(classes), product,
                     read(path, "manufacturer") or "-"])
    return rows


def table(title, headers, rows, note=""):
    bold, plain = ("\033[1m", "\033[0m") if sys.stdout.isatty() else ("", "")
    print(f"\n{bold}{title}{plain}{note}")
    if not rows:
        print("  (none)")
        return
    widths = [max(len(str(r[i])) for r in [headers] + rows)
              for i in range(len(headers))]
    line = "  ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    print(line.rstrip())
    print("-" * len(line.rstrip()))
    for row in rows:
        out = "  ".join(f"{c:<{w}}" for c, w in zip(row, widths))
        print(out.rstrip())


def main():
    flags = sys.argv[1:]
    unknown = [f for f in flags
               if f not in ("-s", "--include-storage", "-h", "--help")]
    if unknown or "-h" in flags or "--help" in flags:
        if unknown:
            print(f"unknown option: {unknown[0]}\n", file=sys.stderr)
        print(f"usage: {os.path.basename(sys.argv[0])} [-s|--include-storage]")
        print("  -s, --include-storage   also list block devices and mounts")
        sys.exit(2 if unknown else 0)

    table("USB DEVICES",
          ["PORT", "LINK", "CLASS", "PRODUCT", "VENDOR"],
          collect_usb(),
          note="  (hubs omitted)")
    if "-s" in flags or "--include-storage" in flags:
        table("STORAGE",
              ["DEV", "LINK", "MODEL", "SIZE", "MOUNT"],
              collect_storage())
    print()


if __name__ == "__main__":
    main()
