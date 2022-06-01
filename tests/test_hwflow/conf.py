#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
import os

ROOT = ""
buildDir = "{ROOT}/tests/test_hwflow/_tmp"

# Settings to test with hwflow package version 6.1
hwflow_ver = "2.0"
version = "2021.2"
build = "{version}_2021_1021_1001"
VIVADO = "/proj/xbuilds/{build}/installs/lin64/Vivado/{version}/bin/vivado"

# Design script and outputs
design_name = "versal_3bram"
design_script = f"{os.path.dirname(__file__)}/{design_name}.py"
artifacts = [
    "outputs",
    "@design.runs/impl_1/gen_files",
    "@design.runs/impl_1/static_files",
    "@design.runs/impl_1/@design_wrapper.pdi.bif",
    "main.tcl",
    "config_bd.tcl",
    "vivado.log",
]
deploy_dir = "{buildDir}/hwflow_images/{version}/{build}/{design_name}"

# LSF settings
lsf_mode = False
lsf_options = "-Is"
lsf_queue = "long"
lsf_osver = "ws7"
lsf_mem = "65536"
lsf_xsjbsub = ""

# Hardware flow repo settings
hwflow_url = "git@gitenterprise.xilinx.com:SET-HW/hwflow2_0.git"
hwflow_branch = "master"
