#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps


class StressNg(BaseLinux, FileOps):
    def stress_ng_test(self, cmd_options, error_msg=None, time_out=900):
        self.is_bin_exist("stress-ng", silent_discard=False)
        cmd = f"stress-ng {cmd_options}"
        self.console.runcmd(cmd, timeout=time_out)
        self.console.runcmd(cmd, err_msg=error_msg, timeout=time_out)
