#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import logging
import atexit


from roast.xexpect import Xexpect
from roast.utils import has_key
from roast.serial import SerialBase

log = logging.getLogger(__name__)


class HostSerial(SerialBase):
    def __init__(self, config) -> None:
        super().__init__(config)
        self.is_live = False
        self._configure()
        self.console = Xexpect(log, hostname=self.hostname, non_interactive=False)
        self.expect = self.console.expect
        self.sendline = self.console.sendline
        self.runcmd = self.console.runcmd
        self.runcmd_list = self.console.runcmd_list
        self.sendcontrol = self.console.sendcontrol
        self.send = self.console.send
        self.output = self.console.output
        self._setup_init = self.console._setup_init
        self.search = self.console.search
        atexit.register(self.exit)
        self._connect()
        self.is_live = True

    @property
    def prompt(self):
        return self.console.prompt

    @prompt.setter
    def prompt(self, value):
        self.console.prompt = value

    def _configure(self):
        self.interface = self.config.get("board_interface")
        if self.interface == "host_target":
            # self.prompt = "(%|#|>|\\$|# )"
            self.hostname = socket.gethostname()
            if has_key(self.config, "remote_host") and self.config["remote_host"]:
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
