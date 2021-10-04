#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#


# Bif file format
from roast.component.bif.generate import Header, Component, Block

tcase_type = "copymem"
result_msg = "Boot PDI Load: Done"
id_load_list = ["0x1C000000"]

bootheader = "image_config {{bh_auth_enable}}\n \
 pskfile= {static_images_path}/pemfiles/TC_101_POS_Secure_RSA_SHA3_PPK0_BH_AES_NO_ENC_NA_TEST_PSK.pem\n \
 sskfile= {static_images_path}/pemfiles/TC_101_POS_Secure_RSA_SHA3_PPK0_BH_AES_NO_ENC_NA_TEST_SSK.pem"

common_enc_str = ", authentication=rsa"

bif = (
    Block(
        header=Header(name="pmc_subsys"),
        components=[
            Component(name="plm", params=["{common_enc_str}", "path={plm_elf}"]),
            Component(
                name="pmccdo", params=["file={topology_cdo}", "path={pmccdo_path}"]
            ),
        ],
    ),
    Block(
        header=Header(header="metaheader"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={lpd_data_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="lpd_subsys"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={dap_cdo}"]),
            Component(name="cdo", params=["{common_enc_str}", "path={lpd_data_cdo}"]),
            Component(name="psm", params=["{common_enc_str}", "path={psm_elf}"]),
        ],
    ),
    Block(
        header=Header(name="pl_cfi_subsys"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={rcdo_cdo}"]),
            Component(name="cdo", params=["{common_enc_str}", "path={rnpi_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="fpd_subsys"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={fpd_data_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="subsystem", args="copy=0x400000, delay_load"),
        components=[
            Component(name="a72", params=["{common_enc_str}", "path={a72_ddr_elf}"]),
        ],
    ),
)
del Header, Component, Block
