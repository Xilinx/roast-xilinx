#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


import logging
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.mtd import MtdLinux
from roast.testlibs.linux.kconfig import Kconfig
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.fileops import FileOps

log = logging.getLogger(__name__)


class NandLinux(MtdLinux, Kconfig, DtsLinux, BaseLinux, FileOps):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, peripheral):
        self.capture_dmesg()
        return self.is_mtd_exist(peripheral)
