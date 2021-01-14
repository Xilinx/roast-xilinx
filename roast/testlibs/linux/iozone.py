#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class IoZone:
    def iozone_perf_test(self, cmd_options):
        self.is_bin_exist("iozone", silent_discard=False)
        cmd = f"iozone {cmd_options}"
        self.console.runcmd(cmd, timeout=300, expected="iozone test complete")
