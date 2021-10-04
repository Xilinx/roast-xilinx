#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.versal import *

PLNX_BSP = "xilinx-vpk120-es1-v{version}-final.bsp"
plnx_proj = "xilinx-vpk120-es1-{version}"
plnx_package_boot = True
uboot_devicetree = "versal-vpk120-revA"
dtb_dtg = uboot_devicetree.lower()
