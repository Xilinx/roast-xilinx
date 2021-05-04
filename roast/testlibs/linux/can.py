#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import time
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.mtd import MtdLinux
from roast.testlibs.linux.kconfig import Kconfig
from roast.testlibs.linux.dts import DtsLinux

log = logging.getLogger(__name__)


class Can(MtdLinux, Kconfig, DtsLinux, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self):
        self.console.runcmd(f"dmesg | grep -c can:", expected="\r\n")
        if not self.console.output():
            assert False, f"No can channel found!"
        else:
            found_canps = self.console.output().split("\n")
            log.info(f"The can device found: {found_canps}")
        return True

    def can_loopback(self, dbitrate, fd, can_send_str, search_list):
        loopbacks = 15
        j = 1
        ip_link_cmd = "ip link set can0 type can bitrate 100000 loopback on"
        if dbitrate:
            ip_link_cmd += f" {dbitrate}"
        if fd:
            ip_link_cmd += f" {fd}"
        self.console.runcmd(ip_link_cmd, expected="\r\n")

        time.sleep(2)
        self.console.runcmd("ip link set can0 up", expected="\r\n")

        while j <= loopbacks:
            self.console.runcmd(f"cansend can0 {can_send_str}", expected="\r\n")
            j += 1

        self.console.runcmd("ip -d -s link show can0", expected="\r\n")
        canps_data = self.console.output()
        self.console.runcmd("ip link set can0 down", expected="\r\n")

        if any(entry in canps_data for entry in search_list):
            log.info("TEST PASS: can_loopback")

        else:
            assert False, "TEST FAIL: Cannot find canps device"
