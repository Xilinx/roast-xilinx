#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import time
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.sysdevices import SysDevices

log = logging.getLogger(__name__)


class Rtc(DtsLinux, SysDevices, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, Ip, nodes_path="amba/rtc*"):
        # ---------------------------------------------------
        # Checking rtc driver is enabled or not
        # ---------------------------------------------------
        self.capture_dmesg()
        self.dts_list = self.list_dts_parameters(nodes_path, parameter="compatible")
        self.dts_nodes = self.get_dts_nodes(self.dts_list, Ip)
        return self.get_channels(self.dts_nodes, "rtc")

    def set_get_current_time(self, settime="2021-01-01 13:00:00", gettime="13:01:00"):
        year = settime.split("-")[0]
        self.console.runcmd("hwclock -r")
        self.console.runcmd(f"date -s '{settime}'", expected=year)
        self.console.runcmd("hwclock -w")
        time.sleep(60)
        self.console.runcmd("hwclock -r", expected=gettime, timeout=30)

    def interrupt(self, cmd="rtc-test -A", expected="PASS", timeout=300):
        self.console.runcmd(cmd, expected=expected, timeout=timeout)

    def sleep_wakeup(self, channel):
        cmdlist = [
            f"echo 0 > /sys/module/printk/parameters/console_suspend",
            f"echo \"$((`date '+%s'` + 25))\" > {self.sys_class}/rtc/{channel}/wakealarm",
            f"echo mem > /sys/power/state",
        ]
        self.console.runcmd_list(cmdlist, timeout=60)
