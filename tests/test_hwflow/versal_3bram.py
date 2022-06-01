#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from hwflow import Project
from hwflow import Hier
from hwflow_configs.boards import tenzing, se1
from hwflow_data.cips.cips import cips
from hwflow_data.axi_bram_ctrl.axi_bram_ctrl import axi_bram_ctrl
from hwflow_data.emb_mem_gen.emb_mem_gen import emb_mem_gen


def main():
    proj = Project("versal_3bram")
    proj.output.extend(["xsa", "bit"])
    proj.vivado_mode = "batch"
    proj.auto_addr_assign = 1
    proj.error_report = 1

    tenzing.config_project(proj)
    h0 = Hier()
    ps = cips()
    tenzing.config_ps(ps)
    se1.config_ps(ps)

    # PL IP's
    bram_ctrl_0 = axi_bram_ctrl()
    bram_ctrl_0.data_width = 128

    bram_ctrl_1 = axi_bram_ctrl()
    bram_ctrl_1.data_width = 128

    bram_ctrl_2 = axi_bram_ctrl()
    bram_ctrl_2.data_width = 128

    mem_0 = emb_mem_gen()
    mem_0.memory_type = "True_Dual_Port_RAM"
    mem_0.memory_primitive = "URAM"

    mem_1 = emb_mem_gen()
    mem_1.memory_type = "True_Dual_Port_RAM"
    mem_1.memory_primitive = "URAM"

    mem_2 = emb_mem_gen()
    mem_2.memory_type = "True_Dual_Port_RAM"
    mem_2.memory_primitive = "BRAM"

    # CONNECTIONS
    h0.connect(ps, bram_ctrl_2.s_axi)
    h0.connect(ps.ps_noc_cci0, bram_ctrl_0.s_axi)
    h0.connect(ps.ps_noc_cci0, bram_ctrl_1.s_axi)
    h0.connect(bram_ctrl_0.bram_porta, mem_0.bram_porta)
    h0.connect(bram_ctrl_0.bram_portb, mem_0.bram_portb)
    h0.connect(bram_ctrl_1.bram_porta, mem_1.bram_porta)
    h0.connect(bram_ctrl_1.bram_portb, mem_1.bram_portb)
    h0.connect(bram_ctrl_2.bram_porta, mem_2.bram_porta)
    h0.connect(bram_ctrl_2.bram_portb, mem_2.bram_portb)

    proj.add_hier(h0)
    proj.generate_tcl()
    proj.run_vivado()


if __name__ == "__main__":
    main()
