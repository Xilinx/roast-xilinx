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


class Swdt(MtdLinux, Kconfig, DtsLinux, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, swdt_interface):
        self.console.runcmd(
            f'find /dev -name "{swdt_interface}" | wc -l', expected="\r\n"
        )
        if not self.console.output():
            assert False, f"no watchdog node found"
        else:
            found_node = self.console.output().split("\n")
            log.info(f"watchdog node found {found_node}")

        return True

    def is_swdt(self, swdt_interface):
        self.console.runcmd("ps -Af | grep 'watch'", expected="\r\n")
        self.console.runcmd("killall watchdog 2>/dev/null", expected="\r\n")
        self.console.runcmd("ps -Af | grep 'watch'", expected="\r\n")
        self.console.runcmd(f'echo "echo s > /dev/{swdt_interface}"', expected="\r\n")
        self.console.runcmd(f"echo s > /dev/{swdt_interface}", expected="\r\n")
        time.sleep(12)
