#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps


class Sdfec(BaseLinux, FileOps):
    def __init__(self, console, config):
        super().__init__(console, config)

    def sdfec_test(self, cmd, error_data, timeout=600):
        self.is_bin_exist(cmd, silent_discard=False)
        if cmd == "sdfec-demo":
            self.console.runcmd(
                cmd, expected="New config?", wait_for_prompt=False, timeout=timeout
            )
            self.console.sendcontrol("c")
            self.console.runcmd("\r\n")
        else:
            self.console.runcmd(cmd, expected="PASS", timeout=timeout)
        error_data = self.get_error_data(self.config.logfile, error_data)
        if error_data:
            assert False, error_data
