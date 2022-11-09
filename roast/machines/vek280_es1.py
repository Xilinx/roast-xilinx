#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.versal import *

PLNX_BSP = "xilinx-vek280-es1-v{version}-final.bsp"
plnx_proj = "xilinx-vek280-es1-{version}"
plnx_package_boot = True
uboot_devicetree = "versal-vek280-revA"
dtb_dtg = uboot_devicetree.lower()
