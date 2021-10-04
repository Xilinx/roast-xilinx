#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from box import Box
from roast.component.bif.generate import Block, Header, Component

seed = 12345
bifFile = "boot.bif"
platform = "versal"
machine = "tenzing_se1"
base_design = "{machine}"

static_images_path = "/my_static_files"
designs_path = "/my_designs/{version}/versal"
topology_cdo = "/my_designs/{version}/topology_xcvc1902.v2.cdo"

plm_elf = "/my_images/versal_plm.elf"
psm_elf = "/my_images/versal_psm_firmware.elf"

default_pdi = "{designs_path}/{base_design}/outputs/{base_design}.pdi"
uboot_pdi = "{static_images_path}/{base_design}/prod/BOOT.BIN"

a72_ocm_elf = "{static_images_path}/a72_0_ocm.elf"
a72_ddr_elf = "{static_images_path}/a72_0_ddr.elf"
a72_1_ddr_adma0_elf = "{static_images_path}/a72_1_ddr.elf"
a72_hello_world_uart1_elf = "{static_images_path}/a72_hello_world_uart1.elf"
a72_hello_world_elf = "{static_images_path}/a72_hello_world.elf"
r5_hello_world_elf = "{static_images_path}/r5_hello_world.elf"
r72_ocm_elf = "{static_images_path}/r5_0_ocm.elf"
r5_0_tcm_ipi3_elf = "{static_images_path}/r5_0_tcm.elf"
r5_1_ocm_elf = "{static_images_path}/r5_1_ocm.elf"
r5_1_ddr_adma2_elf = "{static_images_path}/r5_1_ddr_adma2.elf"
r5_1_tcm_can1_elf = "{static_images_path}/r5_1_tcm_can1.elf"
r5_rtos_elf = "{static_images_path}/r5_rtos.elf"
memest_ddr_elf = "{static_images_path}/memest_ddr.elf"
uboot_elf = "{static_images_path}/{base_design}/u-boot.elf"
bl31_elf = "{static_images_path}/{base_design}/bl31.elf"
aes_grey_key_file = "{static_images_path}/keys/bbram_grey_key.nky"
aes_red_key_file = "{static_images_path}/keys/bbram_red_key.nky"
aes_black_key_file = "{static_images_path}/keys/vncxhdtenz19_black_key.nky"
linux_image = "{static_images_path}/{base_design}/Image"
systest_dtb = "{static_images_path}/{base_design}/system.dtb"
npi_ualigned_cdo = "{static_images_path}/npi_ualigned.rnpi"
dma_140k_cdo = "{static_images_path}/dma_140k.rnpi"
dmatxfr_140k_cdo = "{static_images_path}/dmatxfr_140k.rnpi"
readback_npi = "{static_images_path}/mydesign_ddr.rba_npi"
mio13_cdo = "{static_images_path}/mio13.cdo"
apu_subsys_cdo = "{static_images_path}/apu_subsystem.cdo"
rpu_subsys_cdo = "{static_images_path}/rpu_0_subsystem.cdo"
wdt_cdo = "{static_images_path}/wdt.txt"
dap_cdo = "{static_images_path}/Perf_Images/dap.cdo"
apu_reset_elf = "{static_images_path}/apu_app.elf"

bbram_elf = "{static_images_path}/bbram_write.elf"
reconfig_tcl = "{static_images_path}/load_reconfig.tcl"
fat_formatter = "{static_images_path}/fat_formatter.tcl"
differed_load_tcl = "{static_images_path}/differed_load.tcl"

bif = (
    Block(
        header=Header(header="image", name="pmc_subsys", args=None),
        components=[
            Component(
                name="plm",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= /my_static_files/Perf_Keys/bbram_red_key.nky",
                    "path=/my_images/versal_plm.elf",
                ],
            ),
            Component(
                name="pmccdo",
                params=[
                    "aeskeyfile= pmc_data.nky\n file=/my_designs/2020.2/topology_xcvc1902.v2.cdo",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/pmc_data.cdo",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="metaheader", name=None, args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen0.nky",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/lpd_data.cdo",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="lpd_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen1.nky\n file=/my_static_files/Perf_Images/dap.cdo",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/lpd_data.cdo",
                ],
            ),
            Component(
                name="psm",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen2.nky",
                    "path=/my_images/versal_psm_firmware.elf",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="image", name="pl_cfi_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen3.nky",
                    "path=/my_static_files/design_un.rcdo",
                ],
            ),
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen4.nky",
                    "path=/my_static_files/Perf_Images/design.rnpi",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="image", name="aie_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen5.nky",
                    "path=/my_static_files/Perf_Images/ai_engine_data.cdo",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="fpd_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, aeskeyfile= gen6.nky",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/fpd_data.cdo",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="aie_subsys", args=None),
        components=[
            Component(
                name="aie-elf",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen7.nky",
                    "path=/my_static_files/Perf_Images/Work_400",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="subsystem", args=None),
        components=[
            Component(
                name="a72",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, exception_level=el-3, aeskeyfile= gen9.nky",
                    "path=/my_static_files/tenzing_se1/bl31.elf",
                ],
            ),
            Component(
                name="a72",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, exception_level=el-2,aeskeyfile= gen10.nky",
                    "path=/my_static_files/tenzing_se1/u-boot.elf",
                ],
            ),
            Component(
                name="sys_dtb",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, aeskeyfile= gen11.nky",
                    "path=/my_static_files/tenzing_se1/system.dtb",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="image", name="subsystem", args=None),
        components=[
            Component(
                name="r5",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, aeskeyfile= gen12.nky",
                    "path=/my_static_files/r5_0_tcm.elf",
                ],
            )
        ],
    ),
)

bif_shuffled = (
    Block(
        header=Header(header="image", name="pmc_subsys", args=None),
        components=[
            Component(
                name="plm",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= /my_static_files/Perf_Keys/bbram_red_key.nky",
                    "path=/my_images/versal_plm.elf",
                ],
            ),
            Component(
                name="pmccdo",
                params=[
                    "aeskeyfile= pmc_data.nky\n file=/my_designs/2020.2/topology_xcvc1902.v2.cdo",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/pmc_data.cdo",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="image", name="fpd_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, aeskeyfile= gen6.nky",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/fpd_data.cdo",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="lpd_subsys", args=None),
        components=[
            Component(
                name="psm",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen2.nky",
                    "path=/my_images/versal_psm_firmware.elf",
                ],
            ),
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen1.nky\n file=/my_static_files/Perf_Images/dap.cdo",
                    "path=/my_designs/2020.2/versal/tenzing_se1/gen_files/lpd_data.cdo",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="image", name="pl_cfi_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen4.nky",
                    "path=/my_static_files/Perf_Images/design.rnpi",
                ],
            ),
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen3.nky",
                    "path=/my_static_files/design_un.rcdo",
                ],
            ),
        ],
    ),
    Block(
        header=Header(header="image", name="aie_subsys", args=None),
        components=[
            Component(
                name="aie-elf",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen7.nky",
                    "path=/my_static_files/Perf_Images/Work_400",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="subsystem", args=None),
        components=[
            Component(
                name="r5",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key, aeskeyfile= gen12.nky",
                    "path=/my_static_files/r5_0_tcm.elf",
                ],
            )
        ],
    ),
    Block(
        header=Header(header="image", name="aie_subsys", args=None),
        components=[
            Component(
                name="cdo",
                params=[
                    "encryption=aes , dpacm_enable , keysrc= bbram_red_key aeskeyfile= gen5.nky",
                    "path=/my_static_files/Perf_Images/ai_engine_data.cdo",
                ],
            )
        ],
    ),
)

block_constraints = Box(default_box=True, box_intact_types=[list])
block_constraints.pmc_subsys.locked = True
block_constraints.pmc_subsys.dependents = ["fpd_subsys"]
block_constraints.lpd_subsys.required = True
block_constraints.lpd_subsys.dependents = ["pl_cfi_subsys"]


del Box
