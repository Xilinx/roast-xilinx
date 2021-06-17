#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.versal import *

uboot_devicetree = "versal-vck5000-revA"
dtb_dtg = uboot_devicetree.lower()

PLNX_BSP = "xilinx-vck5000-es1-v{version}-final.bsp"
plnx_proj = "xilinx-vck5000-es1-{version}"
