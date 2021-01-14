#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import time
from roast.component.relay import RelayBase


class UsbRelay(RelayBase):
    def __init__(self, session):
        self._session = session
        self.expected_failures = "J283"
        self.expected = session.host

    def disconnect(self):
        cmd = "sudo usb_relay off"
        self._session.host_console.runcmd(
            cmd, self.expected_failures, self.expected, wait_for_prompt=False
        )

    def connect(self):
        cmd = "sudo usb_relay on"
        self._session.host_console.runcmd(
            cmd, self.expected_failures, self.expected, wait_for_prompt=False
        )

    def reconnect(self, seconds=5):
        self.disconnect()
        time.sleep(seconds)
        self.connect()
