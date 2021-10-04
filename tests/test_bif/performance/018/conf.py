#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

# Bif file format
from roast.component.bif.generate import Header, Component, Block

test_type = "uboot"
test_functionality = "performance"
Key_type = "RSA_UNCOMP"

static_images_path_conf = (
    "/proj/ssw_xhd/verification/ssw-regress/versal_regression/xtf_files/static_files"
)
perf_keys = "/proj/ssw_xhd/verification/ssw-regress/versal_regression/xtf_files/static_files/Perf_Keys"

bootheader = "image_config {{bh_auth_enable}}\n \
 pskfile = {perf_keys}/PSK.pem \
 sskfile = {perf_keys}/SSK.pem \
 init={static_images_path_conf}/reginit.ini"

common_enc_str = "authentication = rsa"

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
            Component(
                name="cdo",
                params=["{common_enc_str}\n file={dap_cdo}", "path={lpd_data_cdo}"],
            ),
            Component(name="psm", params=["{common_enc_str}", "path={psm_elf}"]),
        ],
    ),
    Block(
        header=Header(name="pl_cfi_subsys"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={un_rcdo_cdo}"]),
            Component(name="cdo", params=["{common_enc_str}", "path={rnpi_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="aie_subsys"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={ai_data_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="fpd_subsys"),
        components=[
            Component(name="cdo", params=["{common_enc_str}", "path={fpd_data_cdo}"]),
        ],
    ),
    Block(
        header=Header(name="aie_subsys"),
        components=[
            Component(name="aie-elf", params=["{common_enc_str}", "path={ai_elfs}"]),
        ],
    ),
    Block(
        header=Header(name="subsystem"),
        components=[
            Component(
                name="a72",
                params=["{common_enc_str}, exception_level=el-3", "path={bl31_elf}"],
            ),
            Component(
                name="a72",
                params=["{common_enc_str}, exception_level=el-2", "path={uboot_elf}"],
            ),
            Component(
                name="sys_dtb", params=["{common_enc_str}", "path={systest_dtb}"]
            ),
        ],
    ),
    Block(
        header=Header(name="subsystem"),
        components=[
            Component(name="r5", params=["{common_enc_str}", "path={r5_elf}"]),
        ],
    ),
)
del Header, Component, Block
