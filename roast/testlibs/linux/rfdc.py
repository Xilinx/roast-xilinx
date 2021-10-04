#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps


class Rfdc(BaseLinux, FileOps):
    def __init__(self, console, config):
        super().__init__(console, config)

    def rfdc_test(self, cmd, expected, error_data, timeout=60):
        self.is_bin_exist(cmd, silent_discard=False)
        if cmd == "rfdc-data-write-example":
            self.console.runcmd(
                cmd,
                expected="Please enter DAC tile ID",
                wait_for_prompt=False,
                timeout=timeout,
            )
            self.console.runcmd(
                cmd="0",
                expected="Please enter DAC block ID",
                wait_for_prompt=False,
                timeout=timeout,
            )
            self.console.runcmd(
                cmd="0",
                expected="Press Enter for Interpolation",
                wait_for_prompt=False,
                timeout=timeout,
            )
            self.console.runcmd(cmd="\r\n")
        else:
            self.console.runcmd(cmd, expected=expected, timeout=timeout)
        test_failures = self.get_error_data(self.config.logfile, error_data)
        if test_failures:
            assert False, test_failures
