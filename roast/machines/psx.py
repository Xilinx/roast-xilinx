#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

platform = "psx"
procs = ["a78", "R52", "PLM"]
serial_port = "serial"


arch = "arm64"
linux_compiler = "aarch64-linux-gnu-"
kernel_loadaddr = 0x80000

kernel_defconfig = "xilinx_defconfig"
kernel_artifacts = ["arch/arm64/boot/Image"]
uboot_defconfig = "xilinx_versal_virt_defconfig"

dtb_arch = "aarch64"
dtb_loadaddr = 0x1000

uboot_artifacts = ["u-boot.elf", "arch/arm/dts/{system_dtb}"]

atf_artifacts = ["versal/release/bl31/bl31.elf"]
atf_compile_flags = "RESET_TO_BL31=1 PLAT=versal bl31 VERSAL_PLATFORM=silicon \
BUILD_BASE=../atf-build"

# Boot scr
boot_scr_loadaddr = 0x20000000

rootfs_loadaddr = 0x30000000
overrides = ["psx"]

system_dtb = "{uboot_devicetree}.dtb"
