#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import re
import logging

log = logging.getLogger(__name__)


class MtdLinux:
    def is_mtd_exist(self, peripheral):
        self.console.sync()
        self.console.runcmd("cat /proc/mtd", expected="\r\n")
        items = re.findall("mtd.*:", self.console.output())
        log.info(f"----- {items} ==")
        self.mtd_list = []
        for x in items:
            self.mtd_device = x.split(":")[0]
            self.mtd_num = self.mtd_device[-1]
            self.console.runcmd(
                f"mtd_debug info /dev/{self.mtd_device}", expected="\r\n"
            )
            if ("spi" in peripheral and "MTD_NORFLASH" in self.console.output()) or (
                "nand" in peripheral and "MTD_NANDFLASH" in self.console.output()
            ):
                self.mtd_list.append(self.mtd_num)
        if not self.mtd_list:
            assert False, f"{peripheral} device is not found"
        return self.mtd_list

    def get_mtd_size(self, mtd_device):
        self.mtdsize = {}
        for mtd_num in mtd_device:
            self.console.runcmd(f"mtd_debug info /dev/mtd{mtd_num}", expected="\r\n")
            size = re.search(f"mtd.size = (\d[0-9]+)", self.console.output())
            if size:
                self.mtdsize[f"/dev/mtd{mtd_num}"] = size.group(1)
        return self.mtdsize

    def flash_erase(self, mtd_device, extra_args=""):
        self.console.runcmd(
            f"flash_erase {extra_args} {mtd_device} 0 0", expected="100 % complete"
        )

    def ubiformat(self, mtd_device, extra_args="-e 0 -y"):
        self.console.runcmd(
            f"ubiformat {mtd_device} {extra_args}", expected="100 % complete"
        )

    def ubiattach(self, mtd_device):
        self.console.runcmd(f"ubiattach -p {mtd_device}")

    def ubimkvol(self, ubifs_device="/dev/ubi0", extra_args="-N data"):
        self.console.runcmd(f"ubimkvol {extra_args} -m {ubifs_device}")

    def ubidetach(self, mtd_num):
        self.console.runcmd(f"ubidetach --mtdn={mtd_num}")

    def flashcptest(self, mtd_num, size):
        self.console.sync()
        cmdlist = [
            f"dd if=/dev/urandom of=/tmp/test.img bs={size} count=2",
            f"flashcp -v /tmp/test.img /dev/mtd{mtd_num}",
        ]
        self.console.runcmd_list(cmdlist, expected="\r\n")
        res_str = self.console.output()
        res_str = res_str.strip().split("\n")[-1]
        if re.match("Verify(.*?)(100%)", res_str):
            log.info("flashcp test passed")
        else:
            assert False, "flashcp test failed"

    def mtdmoduletest(self, mtd_num, module, extra_args=""):
        self.console.runcmd("lsmod", expected="\r\n")
        if module in self.console.output():
            cmd = f"depmod; rmmod {module}"
            self.console.runcmd(cmd, expected="\r\n")
        cmd = f"depmod; modprobe {module} dev={mtd_num} {extra_args}"
        self.console.runcmd(
            cmd,
            expected="finished",
            expected_failures=f"{module}: error:",
            timeout=3000,
        )
