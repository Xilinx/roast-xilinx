#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class IoZone:
    def iozone_perf_test(self, cmd_options, mnt_path, timeout=300):
        self.is_bin_exist("iozone", silent_discard=False)
        self.console.runcmd(f"pushd {mnt_path}")
        cmd = f"iozone {cmd_options}"
        self.console.runcmd(cmd, timeout=timeout, expected="iozone test complete")
        self.console.runcmd("popd")
