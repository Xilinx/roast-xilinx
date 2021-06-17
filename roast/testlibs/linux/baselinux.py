#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging

log = logging.getLogger(__name__)


class BaseLinux:
    def __init__(self, console, config):
        self.console = console
        self.config = config
        self.console._setup_init()
        self.console.exit_nzero_ret = True
        self.sys_dt_base = "/sys/firmware/devicetree/base"
        self.sys_amba = "/sys/devices/platform/amba"
        self.sys_axi = "/sys/devices/platform/axi"
        self.kconfig_path = "/proc/config.gz"
        self.sys_dmatest = "/sys/module/dmatest/parameters"
        self.bootargs = "/proc/cmdline"
        self.sys_devices = "/sys/devices"
        self.sys_class = "/sys/class"
        self.sys_class_dev = {
            "mmc": f"{self.sys_class}/mmc_host",
            "dma": f"{self.sys_class}/dma",
            "i2c": f"{self.sys_class}/i2c-adapter",
            "rtc": f"{self.sys_class}/rtc",
        }
        self.proc_kernel = "/proc/sys/kernel"
        self.dev_events = "/dev/input/by-path/"
        self.sys_kernel = "/sys/kernel/config"
        self.sys_debug = "/sys/kernel/debug"
        self.boot_dt = "/boot/devicetree"
        self.iio_devices = "/sys/bus/iio/devices"

    def get_kernel_info(self):
        self.console.runcmd("uname -a", expected="\r\n")
        return self.console.output()

    def get_bootargs(self):
        self.console.runcmd(f"cat {self.bootargs}", expected="\r\n")
        return self.console.output()

    def capture_boot_dmesg(self):
        cmd = "(ls /tmp/dmesg.txt >> /dev/null 2>&1 && echo yes) || echo no"
        self.console.runcmd(cmd, expected=self.console.prompt)
        if "no" in self.console.output().split("\n")[1]:
            self.console.runcmd("dmesg > /tmp/dmesg.txt")
        self.console.runcmd(
            "cat /tmp/dmesg.txt; echo 'sync' | tr '[:lower:]' '[:upper:]'",
            expected="SYNC",
            wait_for_prompt=False,
        )

    def capture_dmesg(self):
        self.console.runcmd("dmesg")
        with open(f"{self.config['ROOT']}/dmesg.txt", "w+") as f:
            f.write(str(self.console.output()))

    def set_console_loglevel(self, log_level="8"):
        self.console.runcmd(f"echo {log_level} > {self.proc_kernel}/printk")
        self.console.runcmd(f"cat {self.proc_kernel}/printk")
