#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.sysdevices import SysDevices


class DmaLinux(DtsLinux, SysDevices, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, dmaIp, dma_nodes_path="amba/dma*"):
        self.capture_dmesg()
        self.dma_dts_list = self.list_dts_parameters(
            dma_nodes_path, parameter="compatible"
        )
        self.dma_dts_nodes = self.get_dts_nodes(self.dma_dts_list, dmaIp)
        return self.get_channels(self.dma_dts_nodes, "dma")

    def dma_run(self, timeout=60):
        distro = self.get_system_distro()
        if distro == "systemd":
            self.console.runcmd("journalctl -f > /var/log/messages 2>&1 &")
        self.console.runcmd("echo > /var/log/messages")
        self.console.runcmd(
            f"echo 1 > {self.sys_dmatest}/run; sleep {timeout}; \r\n",
            timeout=timeout + 60,
        )
        if distro == "systemd":
            self.console.runcmd("pkill journalctl")
        self.console.sync()
        self.console.runcmd(
            "cat /var/log/messages",
            expected=self.console.prompt,
            expected_failures=[
                "Could not start test",
                "no channels configured",
                "Device or resource busy",
            ],
            timeout=60,
            wait_for_prompt=False,
        )

    def dmatest_cfg_iterations(self, iterations):
        self.console.runcmd(f"echo {iterations} > {self.sys_dmatest}/iterations")

    def dmatest_cfg_threads(self, threads):
        self.console.runcmd(f"echo {threads} > {self.sys_dmatest}/threads_per_chan")

    def dmatest_cfg_mode(self, mode):
        self.console.runcmd(f"echo {mode} > {self.sys_dmatest}/dmatest")

    def dmatest_cfg_noverify(self, noverify):
        self.console.runcmd(f"echo {noverify} > {self.sys_dmatest}/noverify")

    def dmatest_cfg_bufsize(self, bufsize):
        self.console.runcmd(f"echo {bufsize} > {self.sys_dmatest}/test_buf_size")

    def dmatest_cfg_channel(self, channels_list=None):
        if channels_list is None:
            self.console.runcmd(f"echo ' ' > {self.sys_dmatest}/channel")
        else:
            for channel in channels_list:
                if "root" not in channel:
                    self.console.runcmd(
                        f"echo {channel} > " f"{self.sys_dmatest}/channel"
                    )

    def dmatest_cfg_timeout(self, timeout):
        self.console.runcmd(f"echo {timeout} > {self.sys_dmatest}/timeout")

    def axidmatest_module(self, bufsize, iterations):
        self.console.runcmd(
            f"modprobe axidmatest test_buf_size={bufsize} iterations={iterations}"
        )

    def axivdmatest_module(self, bufsize, iterations):
        self.console.runcmd(
            f"modprobe vdmatest test_buf_size={bufsize} iterations={iterations}"
        )
        self.console.runcmd(
            f"modprobe -r vdmatest; modprobe vdmatest hsize=640 vsize=480"
        )
        self.console.runcmd(
            f"modprobe -r vdmatest; modprobe vdmatest hsize=1280 vsize=720"
        )
        self.console.runcmd(
            f"modprobe -r vdmatest; modprobe vdmatest hsize=1920 vsize=1080"
        )

    def dma_print_result(self):
        val1 = self.console.output().count(": summary ")
        val2 = self.console.output().count(", 0 failures")
        if val1 == 0 or val1 != val2:
            assert False, "dma test failed"
