#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import time
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.sysdevices import SysDevices
from roast.testlibs.linux.fileops import FileOps
from typing import Optional, List

log = logging.getLogger(__name__)


class Wdt(DtsLinux, SysDevices, BaseLinux, FileOps):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, Ip, nodes_path="amba/watchdog*"):
        # ------------------------------------------
        # Checking wdt driver is enabled or not
        # ------------------------------------------
        self.capture_dmesg()
        self.dts_list = self.list_dts_parameters(nodes_path, parameter="compatible")
        self.dts_nodes = self.get_dts_nodes(self.dts_list, Ip)
        self.is_bin_exist("watchdog-test", silent_discard=False)
        return self.get_channels(self.dts_nodes, "watchdog")

    def wdt_info(self, wdt_channel):
        # Checking wdt driver info.
        self.console.runcmd(
            f"watchdog-test /dev/{wdt_channel} -i",
            expected_failures=["device open failed", "not found"],
        )
