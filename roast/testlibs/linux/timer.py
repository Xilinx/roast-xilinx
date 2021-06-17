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


class Timer(MtdLinux, Kconfig, DtsLinux, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def run_timer(self):
        self.console.runcmd("START_TIME=$SECONDS", expected="\r\n")
        time.sleep(60)
        self.console.runcmd(
            "echo $((SECONDS - START_TIME))", expected=["60", "61"], timeout=30
        )
