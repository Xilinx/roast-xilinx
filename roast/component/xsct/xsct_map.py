#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

compiler_map = {
    "gcc": [
        "microblaze",
        "ps7_cortexa9",
        "psu_cortexr5",
        "psu_cortexa53",
        "psu_pmu",
        "psv_cortexa72",
        "psv_cortexr5",
        "psv_pmc",
        "psv_psm",
    ],
    "armcc": ["ps7_cortexa9"],
    "c++": ["psu_cortexa53", "psv_cortexa72"],
    "iar": ["ps7_cortexa9", "psu_cortexr5", "psv_cortexr5"],
    "armclang": ["psu_cortexa53", "psu_cortexr5", "psv_cortexa72", "psv_cortexr5"],
}

proc_map = {
    "microblaze": ["microblaze"],
    "zynq": ["ps7_cortexa9"],
    "zynqmp": ["psu_cortexr5", "psu_cortexa53", "psu_pmu"],
    "versal": ["psv_cortexa72", "psv_cortexr5", "psv_pmc", "psv_psm"],
}

os_map = {
    "microblaze": ["standalone", "freertos"],
    "zynq": ["standalone", "freertos"],
    "zynqmp": ["standalone", "freertos"],
    "versal": ["standalone", "freertos"],
}
