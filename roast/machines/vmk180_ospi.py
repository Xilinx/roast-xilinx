# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.machines.versal import *

PLNX_BSP = "xilinx-vmk180-ospi-v{version}-final.bsp"
plnx_proj = "xilinx-vmk180-ospi-{version}"
uboot_devicetree = "versal-vmk180-revA-x-ebm-03-revA"
dtb_dtg = uboot_devicetree.lower()
