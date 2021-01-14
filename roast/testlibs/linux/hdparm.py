#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class HdParm:
    def hdparm_perf_test(self, device):
        self.is_bin_exist("hdparm", silent_discard=False)
        cmd = f"hdparm -tT {device}"
        self.console.runcmd(cmd, expected="Timing buffered disk reads")
