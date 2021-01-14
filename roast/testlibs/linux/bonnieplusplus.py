#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


class BonniePlusPlus:
    def bonnieplusplus_perf_test(self, mnt_path, cmd_options):
        self.is_bin_exist("bonnie++", silent_discard=False)
        cmd = f"bonnie++ -d {mnt_path} -u root {cmd_options}"
        self.console.runcmd(cmd, timeout=4200)
