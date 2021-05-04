#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.mtd import MtdLinux
from roast.testlibs.linux.kconfig import Kconfig
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.fileops import FileOps

log = logging.getLogger(__name__)


class SpiLinux(MtdLinux, Kconfig, DtsLinux, BaseLinux, FileOps):
    def __init__(self, console, config):
        super().__init__(console, config)

    def is_qspi_dual_parallel(self, peripheral, dt_node):
        self.console.sync()
        self.console.runcmd(
            f"hexdump /proc/device-tree/{dt_node}/is-dual", expected="\r\n"
        )
        self.mode = self.console.output().split("\n")[0].split()[-1]
        log.info(f"^^^^ {self.mode} ^^^")
        if "0100" in self.mode:
            log.info(f"{peripheral} is in dual parallel " "configuration")
        return self.mode

    def isUp(self, spi_interface):
        self.spi_interface = spi_interface
        self.capture_dmesg()
        return self.is_mtd_exist(self.spi_interface)

    def sector_size(self, peripheral, mtd_num, dt_node):
        # Check QSPI 4K sector config is enabled or not
        cfg_status = self.check_kernel_config(["CONFIG_MTD_SPI_NOR_USE_4K_SECTORS"])
        if cfg_status[0] == True:
            self.sector_config = "1"
        else:
            self.sector_config = "0"
        # Get current sector size
        self.console.runcmd(f"mtdinfo /dev/mtd{mtd_num}", expected="\r\n")
        self.current_sector_size = (
            self.console.output()
            .partition("Eraseblock size:                ")[2]
            .split()[2]
        )
        log.info(f"current sector size: " f"{self.current_sector_size}")
        self.config_mode = self.is_qspi_dual_parallel(peripheral, dt_node)

        if "0100" in self.config_mode and self.sector_config == "1":
            self.expected_sector_size = "8.0"
        elif "0100" in self.config_mode and self.sector_config == "0":
            self.expected_sector_size = "128.0"
        elif ("0000" in self.config_mode or "*" in self.config_mode) and (
            self.sector_config == "1"
        ):
            self.expected_sector_size = "4.0"
        elif ("0000" in self.config_mode or "*" in self.config_mode) and (
            self.sector_config == "0"
        ):
            self.expected_sector_size = "64.0"

        log.info(f"expected sector size: " f"{self.expected_sector_size}")
        if self.current_sector_size == self.expected_sector_size:
            log.info("current sector size is matched with expected sector size")
        else:
            assert False, (
                "current sector size is not matched with expected " "sector size"
            )

    def flash_protection(self, mtd_num, offset, block_count):
        # Protecing qspi flash partition by locking to erase.
        self.console.runcmd(f"flash_lock /dev/mtd{mtd_num} {offset} {block_count}")
        self.console.runcmd(
            f"flash_erase /dev/mtd{mtd_num} {offset} {block_count}",
            expected=["MTD Erase failure", "Erase operation failed"],
            expected_failures="100 % complete",
            err_msg="Failed to protect flash partition after locking",
        )
        self.console.runcmd(f"flash_unlock /dev/mtd{mtd_num} {offset} {block_count}")
        self.console.runcmd(
            f"flash_erase /dev/mtd{mtd_num} {offset} {block_count}",
            expected="100 % complete",
        )
