#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class StressNg:
    def stress_ng_test(self, cmd_options, time_out=900):
        self.is_bin_exist("stress-ng", silent_discard=False)
        cmd = f"stress-ng {cmd_options}"
        self.console.runcmd(cmd, timeout=time_out)
