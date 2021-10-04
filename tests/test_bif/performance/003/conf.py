#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

# Bif file format
from roast.component.bif.generate import Header, Component, Block

bootheader = "init={static_images_path}/reginit.ini"
test_type = "uboot"
test_functionality = "performance"
Key_type = "RED_UNCOMP"

common_enc_str = "encryption=aes , dpacm_enable , keysrc= bbram_red_key"

bif = (
    Block(
        header=Header(name="pmc_subsys"),
        components=[
            Component(
                name="plm",
                params=[
                    "{common_enc_str} aeskeyfile= {perf_keys}/bbram_red_key.nky",
                    "path={plm_elf}",
                ],
            ),
            Component(
                name="pmccdo",
                params=[
                    "aeskeyfile= pmc_data.nky\n file={topology_cdo}",
                    "path={pmccdo_path}",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="metaheader"),
        components=[
            Component(
                name="cdo",
                params=["{common_enc_str} aeskeyfile= gen0.nky", "path={lpd_data_cdo}"],
            ),
        ],
    ),
    Block(
        header=Header(name="lpd_subsys"),
        components=[
            Component(
                name="cdo",
                params=[
                    "{common_enc_str} aeskeyfile= gen1.nky\n file={dap_cdo}",
                    "path={lpd_data_cdo}",
                ],
            ),
            Component(
                name="psm",
                params=["{common_enc_str} aeskeyfile= gen2.nky", "path={psm_elf}"],
            ),
        ],
    ),
    Block(
        header=Header(name="pl_cfi_subsys"),
        components=[
            Component(
                name="cdo",
                params=["{common_enc_str} aeskeyfile= gen3.nky", "path={un_rcdo_cdo}"],
            ),
            Component(
                name="cdo",
                params=["{common_enc_str} aeskeyfile= gen4.nky", "path={rnpi_cdo}"],
            ),
        ],
    ),
    Block(
        header=Header(name="aie_subsys"),
        components=[
            Component(
                name="cdo",
                params=["{common_enc_str} aeskeyfile= gen5.nky", "path={ai_data_cdo}"],
            ),
        ],
    ),
    Block(
        header=Header(name="fpd_subsys"),
        components=[
            Component(
                name="cdo",
                params=[
                    "{common_enc_str}, aeskeyfile= gen6.nky",
                    "path={fpd_data_cdo}",
                ],
            ),
        ],
    ),
    Block(
        header=Header(name="aie_subsys"),
        components=[
            Component(
                name="aie-elf",
                params=["{common_enc_str} aeskeyfile= gen7.nky", "path={ai_elfs}"],
            ),
        ],
    ),
    Block(
        header=Header(name="subsystem"),
        components=[
            Component(
                name="a72",
                params=[
                    "{common_enc_str}, exception_level=el-3, aeskeyfile= gen9.nky",
                    "path={bl31_elf}",
                ],
            ),
            Component(
                name="a72",
                params=[
                    "{common_enc_str}, exception_level=el-2,aeskeyfile= gen10.nky",
                    "path={uboot_elf}",
                ],
            ),
            Component(
                name="sys_dtb",
                params=[
                    "{common_enc_str}, aeskeyfile= gen11.nky",
                    "path={systest_dtb}",
                ],
            ),
        ],
    ),
    Block(
        header=Header(name="subsystem"),
        components=[
            Component(
                name="r5",
                params=["{common_enc_str}, aeskeyfile= gen12.nky", "path={r5_elf}"],
            ),
        ],
    ),
)
del Header, Component, Block
