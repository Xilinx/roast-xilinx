#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging

log = logging.getLogger(__name__)


class DtsLinux:
    def get_dtsbus_node(self, buses=("amba* -o ", "axi"), bus_req="axi"):
        self.console.sync()
        cmd = ""
        for bus in buses:
            cmd += f" -name {bus} "
        self.console.runcmd(
            f"find {self.sys_dt_base}/ -maxdepth 1 \({cmd}\)", expected="\r\n"
        )
        if bus_req in self.console.output():
            return f"/{bus_req}/"
        else:
            assert False, f"No buses {buses} found in {self.sys_dt_base}"

    def check_dt_node_status(self, dts_base=None, dt_nodes=None):
        if not dts_base:
            dts_base = self.sys_dt_base
        node_status = []
        for dt_node in dt_nodes:
            self.dts_path = f"{dts_base}/{dt_node}/status"
            dt_status = self.is_file_exist(self.dts_path)
            if not dt_status:
                node_status.append(True)
                continue
            self.console.runcmd(f"cat {self.dts_path}", expected="\r\n")
            if (
                "ok" in self.console.output()
                and "disabled" not in self.console.output()
            ):
                node_status.append(True)
            else:
                node_status.append(False)
        return node_status

    def list_dts_parameters(self, node_path, parameter=None):
        self.console.sync()
        self.console.runcmd(
            f"ls {self.sys_dt_base}/{node_path}/{parameter}", expected="\r\n"
        )
        if not self.console.output():
            log.info(f"No dts entries found for {node_path}")
            return False
        dts_params = self.console.output().split()
        dts_params = [i for i in dts_params if "root" not in i]
        return dts_params

    def get_dts_nodes(self, dts_list, Ip):
        self.dts_nodes = []
        for node in dts_list:
            self.console.sync()
            self.console.runcmd(f"cat {node}", expected="\r\n")
            if Ip in self.console.output():
                self.dts_nodes.append(
                    node.split("/")[-2][node.split("/")[-2].find("@") + 1 :]
                )
        if not self.dts_nodes:
            assert False, f"dts nodes not found for {Ip} IP"
        return self.dts_nodes
