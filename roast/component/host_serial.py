#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
from roast.serial import SerialBase


class HostSerial(SerialBase):
    def __init__(self, config) -> None:
        super().__init__(config)

    def _configure(self):
        self.interface = self.config.get("board_interface")
        if self.interface == "host_target":
            # self.prompt = "(%|#|>|\\$|# )"
            self.hostname = socket.gethostname()
            if self.config.get("remote_host"):
                self.hostname = self.config["remote_host"]
        else:
            raise Exception(f"ERROR: invalid serial interface {self.interface}")

    def _connect(self):
        picom_connect(self, self.config["com"], self.config["baudrate"])

    def exit(self):
        if self.is_live:
            picom_disconnect(self)
            self.is_live = False


def picom_connect(cons, com, baudrate):  # FIXME: Refactor application control
    cmd = f"picocom -b {baudrate} {com}"
    expected_failures = [
        "picocom: command not found",
        "FATAL: cannot open",
        "Error",
        "ERROR",
    ]
    cons.prompt = None
    expected = "Terminal ready"
    cons.runcmd(cmd, expected_failures, expected, timeout=60)


def picom_disconnect(cons):
    expected = "Thanks for using picocom"
    cons.sendcontrol("a")
    cons.sendcontrol("x")
    cons.expect(expected, wait_for_prompt=False)
