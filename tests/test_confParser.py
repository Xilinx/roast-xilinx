#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import inspect
import pytest
from roast.confParser import get_machine_file


def test_get_machine_file():
    import roast.machines.zynq

    assert get_machine_file("zynq") == inspect.getsourcefile(roast.machines.zynq)
