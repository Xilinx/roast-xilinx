#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

platform = "microblaze"
procs = ["microblaze"]
serial_port = "serial"

arch = "microblaze"
linux_compiler = "microblazeel-xilinx-linux-gnu-"

dtb_loadaddr = 0x81E00000
dtb_arch = "microblaze"
dtb_dtg = "microblaze-generic"
dtb_defconfig = "microblaze-generic_defconfig"
dtb_compiler = "microblazeel-xilinx-linux-gnu-"

kernel_loadaddr = 0x80000000
kernel_defconfig = "mmu_defconfig"
kernel_artifacts = ["arch/microblaze/boot/simpleImage.system.ub"]
kernel_image = "simpleImage.system.ub"

uboot_defconfig = "microblaze-generic_defconfig"
uboot_artifacts = ["u-boot"]

boot_scr_loadaddr = 0xBF200000

rootfs_loadaddr = 0x82E00000

overrides = ["microblaze"]

system_dtb = "microblaze-generic.dtb"
uboot_devicetree = "microblaze-generic"
