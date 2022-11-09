#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import time
from roast.testlibs.linux.baselinux import BaseLinux

log = logging.getLogger(__name__)


class Edac(BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self):
        # ---------------------------------------------------
        # Checking edac driver is enabled or not
        # ---------------------------------------------------
        self.capture_boot_dmesg()
        self.console.runcmd(
            f"[ -d {self.sys_edac} ]", err_msg="EDAC driver not enabled"
        )

    def inject_error(
        self,
        error_type="CE",
        memory_controller="mc3",
        address="0x2002000",
        data="0x12345",
        bit_size="32",
    ):
        ce_cmds = [
            f'echo "{error_type}" > {self.sys_edac}/mc/{memory_controller}/inject_data_poison',
            f"echo {address} > {self.sys_edac}/mc/{memory_controller}/inject_data_error",
            f"devmem {address} {bit_size} {data}",
        ]
        self.console.runcmd_list(ce_cmds)
        self.console.runcmd(
            f"devmem {address}",
            expected=[
                f"EDAC {memory_controller.upper()}: [1-9] {error_type} Error type:{error_type}",
                f"EDAC {memory_controller.upper()}: [1-9] {error_type} DDR ECC error type",
            ],
        )

    def inject_ocm_error(
        self,
        error_type="CE",
        fault_count=4,
        err_bitpos=31,
        ue_bitpos=32,
        address="0xFFFD0000",
        data="0xFFFFFFFFFFFF",
        bits_size=64,
    ):
        """
        This function is to test funtionality of edac driver on ocm by injecting
        correctble Error and uncorrectable error.
        Arguments:
            error_type {string} -- CE/UE (correctable or uncorrectable)
            fault_count {int} -- inject fault count
            err_bitpos {int} -- inject error bit position
            ue_bitpos {int} -- inject uncorrectable bit position
            address {string} -- ocm address to inject error
            data {string} -- define some hex data to generate fault data
        """
        err_inj = {}
        ocm_edac = f"{self.sys_edac}/zynqmp_ocm"
        err_inj["ce_cmds"] = [
            f"echo {fault_count} > {ocm_edac}/inject_fault_count",
            f"echo {err_bitpos} > {ocm_edac}/inject_{error_type.lower()}bitpos",
            f"devmem {address} {bits_size} {data}",
        ]
        err_inj["ue_cmds"] = [
            f"echo {fault_count} > {ocm_edac}/inject_fault_count",
            f"echo {err_bitpos} > {ocm_edac}/inject_{error_type.lower()}bitpos0",
            f"echo {ue_bitpos} > {ocm_edac}/inject_{error_type.lower()}bitpos1",
            f"devmem {address} {bits_size} {data}",
        ]
        self.console.runcmd_list(err_inj[f"{error_type.lower()}_cmds"])
        self.console.runcmd(
            f"devmem {address}",
            expected=[
                f"EDAC DEVICE[0-9]: {error_type}: zynqmp_ocm instance: zynqmp_ocm[0-9] block: zynqmp_ocm[0-9] count: [1-9]",
            ],
        )
