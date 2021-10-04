#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

component = "plm"

xsct_xsa = "{designs_path}/tenzing_se1/outputs/tenzing_se1.xsa"


# Bif file format
from roast.component.bif.generate import Header, Component, Block

bif = (
    Block(
        header=Header(name="pmc_subsys"),
        components=[
            Component(name="plm", params=["path={plm_elf}"]),
            Component(
                name="pmccdo", params=["file={topology_cdo}", "path={pmccdo_path}"]
            ),
        ],
    ),
    Block(
        header=Header(name="lpd_subsys"),
        components=[
            Component(name="cdo", params=["path={lpd_data_cdo}"]),
            Component(name="psm", params=["path={psm_elf}"]),
        ],
    ),
    Block(
        header=Header(name="pl_cfi_subsys"),
        components=[
            Component(name="cdo", params=["path={rcdo_cdo}"]),
            Component(name="cdo", params=["path={rnpi_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="fpd_subsys"),
        components=[
            Component(name="cdo", params=["path={fpd_data_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="subsystem"),
        components=[
            Component(name="a72", params=["path={a72_ocm_elf}"]),
        ],
    ),
)
del Header, Component, Block
