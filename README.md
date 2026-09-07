# usb-speeds
List every non-hub USB device with its negotiated link speed, presenting all the data in a simple tabular format

```
Usage:
    usb-speeds.py [-s|--include-storage]
```

Ever got frustrated by how cumbersome it could be to find out at what speed your new USB gizmo connected to your Linux Desktop / Server? 

Ever got frustrated when copying a thousand NEF pictures from your CFexpress reader by how slow the transfer is? 

My reader, when connected with the wrong cable or to the wrong port, connects at USB2/480Mbps speed even if it supports 10Gbps. Hilariously, when connected to a USB4 40000Mbps port, it downgrades to USB2 as well. 

Well, now you can very quickly check your setup/usb topology in your terminal before starting your transfer / backup / etc.

```
> usb-speeds

USB DEVICES  (hubs omitted)
PORT       LINK                  CLASS          PRODUCT                 VENDOR
------------------------------------------------------------------------------
1-6        USB2.0 (480Mb/s)      Audio/HID      USB Audio               Generic
1-7.4.1    USB1.1 (12Mb/s)       Audio/HID      Poly Voyager Base-M CD  Plantronics
1-7.4.2    USB1.1 (12Mb/s)       HID            USB Receiver            Logitech
1-7.4.3    USB2.0 (480Mb/s)      Video/Audio    HD Pro Webcam C920      -
1-7.4.4.1  USB1.1 (12Mb/s)       HID/SmartCard  YubiKey OTP+FIDO+CCID   Yubico
1-7.4.4.5  USB2.0 (480Mb/s)      Vendor         USB2 Controller Hub     Microchip Tech
1-7.4.5    USB2.0 (480Mb/s)      Vendor/HID     USB2 Controller Hub     Microchip Tech
1-8        USB1.1 (12Mb/s)       HID            8BitDo UM 2 Receiver    8BitDo
1-13       USB1.1 (12Mb/s)       HID            LED Controller          ASRock
1-14       USB1.1 (12Mb/s)       Wireless       8087:0033               -
2-4.4.3    USB3.2 Gen1 (5Gb/s)   Vendor         USB 10/100/1000 LAN     Realtek
2-7.1      USB3.2 Gen1 (5Gb/s)   Storage        SD PG05.5               ProGrade
2-7.2      USB3.2 Gen2 (10Gb/s)  Storage        CFexpress PG05.5        ProGrade
2-9        USB3.2 Gen1 (5Gb/s)   Storage        My Passport 2627        Western Digital

```

If you include the -s command line switch, it also lists Storage device details

```
STORAGE
DEV      LINK                  MODEL                                   SIZE    MOUNT
------------------------------------------------------------------------------------
nvme0n1  NVMe                  Samsung SSD 9100 PRO with Heatsink 8TB  7.3T    /boot/efi  /boot  /  /media/myfolders  /media/mediafast
sda      SATA                  ATA Samsung SSD 870                     3.6T    /media/mediastore3
sdb      SATA                  ATA Samsung SSD 860                     3.6T    /media/mediastore2
sdc      SATA                  ATA Samsung SSD 860                     3.6T    /media/bkpartition  /media/mediastore1
sdd      USB3.2 Gen1 (5Gb/s)   My Passport 2627                        4.5T    /media/backupdisk
sde      USB3.2 Gen2 (10Gb/s)  CFexpress PG05.5                        745.2G  /run/media/ariel/NIKON Z6_3
sdf      USB3.2 Gen1 (5Gb/s)   SD PG05.5                               0B
```

Tested on Ubuntu Linux 26.04LTS/Desktop and 26.10/Server.

Written with some help from Claude
