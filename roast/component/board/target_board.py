#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import logging
from roast.component.board.board import BoardBase
from roast.component.xsdb.xsdb import Xsdb
from roast.serial import Serial
from roast.xexpect import Xexpect
from roast.component.relay import Relay
from roast.ssh import scp_file_transfer

log = logging.getLogger(__name__)
hlog = logging.getLogger(__name__ + ".host")
tlog = logging.getLogger(__name__ + ".target")


class TargetBoard(BoardBase):
    def __init__(self) -> None:
        super().__init__()

    def start(self) -> None:
        self.interface = self.config.get("board_interface")
        self.relay_type = self.config.get("relay_type")
        if self.interface == "host_target":
            self._setup_host_target()
            self.relay = Relay(self.relay_type, session=self.host_console).driver
            self._reboot()
            self.serial = Serial("host", self.config).driver

        elif self.interface == "network_target":
            self._set_nw_target()
            self.target_console = Xexpect(
                tlog,
                hostip=self.ip,
                userid=self.user,
                password=self.password,
                non_interactive=False,
            )
        elif self.interface == "qemu":
            log.info("Running Qemu Interface")
        else:
            raise Exception(f"ERROR: invalid board_interface {self.interface}")

    def _setup_host_target(self) -> None:
        self._set_host()
        if not self.isLive:
            self.host_console = Xexpect(
                hlog,
                hostname=self.host,
                non_interactive=False,
            )
            if self.invoke_hwserver:
                self.xsdb_hwserver = Xsdb(
                    self.config, hostname=self.host, setup_hwserver=True
                )
            if self.invoke_xsdb:
                self.xsdb = Xsdb(self.config, hwserver=self.host)
            self.isLive = True
        else:
            self.serial.exit()
            if self.invoke_xsdb:
                self.xsdb = Xsdb(self.config, hwserver=self.host)

    def _set_nw_target(self) -> None:
        self.ip = self.config["target_ip"]
        self.user = self.config["user"]
        self.password = self.config["password"]

    def _reboot(self) -> None:
        if self.isLive and self.reboot:
            if self.interface == "host_target":
                self.relay.reconnect()

    def put(self, src_file: str, dest_path: str) -> None:
        self._get_target_ip()
        if not self.target_ip:
            assert False, "ERROR: Not a valid target ip"
        if self.interface == "host_target":
            scp_file_transfer(
                self.host_console,
                src_file,
                dest_path,
                target_ip=self.target_ip,
                proxy_server=self.host,
            )

    def get(self, src_file: str, dest_path: str) -> None:
        self._get_target_ip()
        if self.interface == "host_target":
            scp_file_transfer(
                self.host_console,
                src_file,
                host_path=dest_path,
                transfer_to_target=False,
                target_ip=self.target_ip,
                proxy_server=self.host,
            )

    def reset(self) -> None:
        if self.isLive:
            if self.interface == "host_target":
                self.relay.reconnect()
