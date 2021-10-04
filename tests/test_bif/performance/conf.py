#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

xsct_xsa = "{designs_path}/{machine}/outputs/{machine}.xsa"
r5_elf = "{static_images_path}/r5_0_tcm.elf"
un_rcdo_cdo = "{static_images_path}/design_un.rcdo"

pmccdo_path = "{designs_path}/{machine}/gen_files/pmc_data.cdo"
lpd_data_cdo = "{designs_path}/{machine}/gen_files/lpd_data.cdo"
fpd_data_cdo = "{designs_path}/{machine}/gen_files/fpd_data.cdo"
subsystem_cdo = "{designs_path}/{machine}/gen_files/subsystem.cdo"
perf_keys = "{static_images_path}/Perf_Keys"
perf_images = "{static_images_path}/Perf_Images"
dap_cdo = "{static_images_path}/Perf_Images/dap.cdo"
ai_elfs = "{static_images_path}/Perf_Images/Work_400"
ai_data_cdo = "{static_images_path}/Perf_Images/ai_engine_data.cdo"
rcdo_cdo = "{static_images_path}/Perf_Images/design.rcdo"
rnpi_cdo = "{static_images_path}/Perf_Images/design.rnpi"

wrkBk_template = "{static_images_path}/Perf_Images/template/Boot_Time_template.xlsm"
# boot_time_dir="/proj/xresults_siv/sswxtf/Boottimes/"
boot_time_dir = "{buildDir}/{machine}/performance/"
redkey_load_tcl = "{static_images_path}/Perf_scripts/bbram_red_versal.tcl"

Puf_elf = "{perf_keys}/puf.elf"
Black_Key = "{imagesDir}/black_key.txt"
Black_Iv = "{imagesDir}/puf4k_hd.txt"
Puf_log = "{perf_keys}/puf.log"
bbram_blk_read_tcl = "{perf_keys}/bbram_black.tcl"
bbram_blk_write_tcl = "{imagesDir}/bbram_black_versal.tcl"
bbram_black_key = "{imagesDir}/bbram_black_versal.tcl"
