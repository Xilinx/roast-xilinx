#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import pytest
from roast.component.relay import Relay


def test_usb_relay(mocker):
    mock_session = mocker.Mock("session")
    mock_session.host = mocker.Mock("host")
    mock_session.host_console = mocker.Mock("host_console")
    mock_session.host_console.runcmd = mocker.Mock("runcmd")
    r = Relay(relay_type="usb", session=mock_session)
    assert isinstance(r, Relay)
    r.disconnect()
    mock_session.host_console.runcmd.assert_called_with(
        "sudo usb_relay off", "J283", mocker.ANY, wait_for_prompt=False
    )
    r.connect()
    mock_session.host_console.runcmd.assert_called_with(
        "sudo usb_relay on", "J283", mocker.ANY, wait_for_prompt=False
    )
    mock_time = mocker.patch(
        "roast.component.usbrelay.time.sleep", return_value=mocker.Mock("sleep")
    )
    r.reconnect(7)
    mock_time.assert_called_with(7)
