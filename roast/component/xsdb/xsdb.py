#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import socket
import os
import re
import sys
import logging
import atexit
from typing import Optional, List
from roast.xexpect import Xexpect
from roast.utils import get_base_name, get_original_path, is_file

log = logging.getLogger(__name__)


class Xsdb(Xexpect):
    def __init__(
        self,
        config,
        hostname: str = socket.gethostname(),
        hwserver: Optional[str] = None,
        setup_hwserver: bool = False,
        port: str = "3121",
        prompt: str = "xsdb%",
    ):
        self.config = config
        self.hostname = hostname
        self.hwserver = hwserver
        self.setup_hwserver = setup_hwserver
        self.port = port
        self.init_prompt = prompt
        super().__init__(log, hostname=self.hostname, non_interactive=False)
        atexit.register(self.exit)
        self._setup()

    def _setup(self):
        # Init commands for xsd to run in non-interactive mode
        vitisPath = self.config["vitisPath"]
        cmd_list = [
            f"export TCL_LIBRARY={vitisPath}/tps/tcl/tcl8.5",
            f"export RDI_DATADIR={vitisPath}/data",
            f"source {vitisPath}/settings64.sh",
            f"export HDI_APPROOT={vitisPath}",
            f"export LD_LIBRARY_PATH={vitisPath}/lib/lnx64.o",
        ]
        self.runcmd_list(cmd_list)
        self.prompt = self.init_prompt
        # Invoke RDI XSDB for non-interactive mode
        self.runcmd(f"{vitisPath}/bin/unwrapped/lnx64.o/rdi_xsdb")
        # Enable silent mode for non-interactive mode
        self.runcmd("configparams silent-mode 1")
        if self.setup_hwserver:
            self.hw_server_setup()  # setup hw_server when defined
        else:
            self.connect()  # Connect to hwserver instance

    def connect(self):
        connect_cmd = "connect "
        if self.hwserver is not None:
            connect_cmd += f"-host {self.hwserver} -port {self.port}"

        f_msgs = ["Connection refused"]
        self.runcmd(connect_cmd, expected_failures=f_msgs, expected=r"tcfchan\#")

    def hw_server_setup(self):
        f_msgs = [
            "child process exited abnormally",
            'Device hw_server command: "hw_server" .*? exited with status [-+]?[1-9]\d*',
        ]
        expected = f"INFO: To connect to this hw_server instance use url: TCP:{self.hostname}:3121"
        self.runcmd(
            "hw_server",
            f_msgs,
            expected,
            wait_for_prompt=False,
            err_msg="hw_server setup failed!",
        )

    def alive(self):
        expected = [self.init_prompt, self.hostname]
        if self.runcmd("\r\n", expected=expected, wait_for_prompt=False) == 0:
            return True

    def disconnect(self):
        self.runcmd("disconnect")

    def con(self):
        self.runcmd("con")

    def stop(self):
        self.runcmd("stop")

    def read(
        self, address: str, offset: int = 1, args: str = "-value -force"
    ) -> List[str]:
        """This Function is to read values from memory
        till offset and returns list of values
        Parameters:
            address - memory location to read value from
            offset - by default set to 1
        """
        f_msgs = ["Memory read error"]
        self.runcmd(f"mrd {args} {address} {offset}", expected_failures=f_msgs)
        reg_val = self.terminal.before
        reg_val = reg_val.lstrip().rstrip()
        return reg_val.split(" ")

    # write, write to list
    def write(self, addr_value: dict, num_words: str = None, args: str = "") -> None:
        """This Function takes dictionary, writes values to memory addresses
        Parameters:
            addr_value: Address, value dictionary
        """
        f_msgs = [
            'Invalid target. Use "targets" command to select a target',
            "instead",
            "Memory write error",
        ]
        for addr, value in addr_value.items():
            if num_words is None:
                self.runcmd(f"mwr {args} {addr} {value}", expected_failures=f_msgs)
            else:
                self.runcmd(
                    f"mwr {args} {addr} {value} {num_words}", expected_failures=f_msgs
                )

    def memorymap(self, addr, size, flags="") -> None:
        """This Function takes address, size and flag values and does memory mapping
        Parameters:
            addr - memory location
            size - size
            flags - flag to be set
        """
        f_msgs = [
            'Invalid target. Use "targets" command to select a target',
            "instead",
            "Memory write error",
        ]
        self.runcmd(
            f"memmap  -addr {addr} -size {size} -flags {flags}",
            expected_failures=f_msgs,
        )

    def mask_write(self, *address_values, args="") -> None:
        """This Function takes address values to perform mask write
        Parameters:
            addr_values: comma seperated values to write
        """
        data = ""
        for value in address_values:
            data = data + " " + value

        f_msgs = [
            'Invalid target. Use "targets" command to select a target',
            "instead",
            "Memory write error",
        ]
        self.runcmd(f"mask_write {data}", expected_failures=f_msgs)

    def get_proc(self):
        pass

    def set_proc(self, proc: str) -> None:

        # Map proc instances with simple keys
        proc_dict = {
            "versal": "Versal *",
            "a72_0": "Cortex-A72*#0",
            "a72_1": "Cortex-A72*#1",
            "a53_0": "Cortex-A53*#0",
            "a53_1": "Cortex-A53*#1",
            "r5_0": "Cortex-R5*#0",
            "r5_1": "Cortex-R5*#1",
            "a9_0": "*Cortex-A9*#0",
            "MB_PSM": "MicroBlaze PSM",
            "MB_PPU": "MicroBlaze PPU",
            "MB": "MicroBlaze*#0",
            "DPC": "DPC",
        }

        cmd = "targets -set -nocase -filter {name =~ "
        if proc in proc_dict:
            cmd += f'"{proc_dict[proc]}"' + "}"
        else:
            cmd += f'"{proc}"' + "}"

        f_msgs = ["no targets found"]
        self.runcmd(cmd, expected_failures=f_msgs)

    def rst_proc(self):
        f_msgs = ["Invalid reset type", "Cannot reset"]
        self.runcmd("rst -proc -clear-registers", expected_failures=f_msgs)

    def rst_cores(self):
        f_msgs = ["Invalid reset type", "Cannot reset"]
        self.runcmd("rst -cores", expected_failures=f_msgs)

    def run_tcl(
        self, tcl_file: str, expected: List[str] = ["SUCCESS"], timeout: int = 400
    ):
        tcl_file = get_original_path(tcl_file)
        self.runcmd(f"source {tcl_file}", expected=expected, timeout=timeout)

    def load_data(self, data_file: str, addr: str, timeout: int = 200) -> None:
        data_file = get_original_path(data_file)
        addr = hex(int(addr))
        f_msgs = [
            f"Failed to download {data_file}",
            "no such file or directory",
            "expected integer but got",
            "no such variable",
            "Memory write error",
        ]
        self.runcmd(
            f"dow -data -force {data_file} {addr}",
            expected_failures=f_msgs,
            timeout=timeout,
        )

    def load_elf(self, elf_file: str, timeout: int = 200) -> None:
        elf_file = get_original_path(elf_file)
        f_msgs = [
            f"Failed to download {elf_file}",
            "no such file or directory",
            "Memory write error",
        ]
        self.runcmd(f"dow -force {elf_file}", expected_failures=f_msgs, timeout=timeout)

    def device_program(self, pdi_file: str = None) -> None:

        if pdi_file is None:
            pdi_file = os.path.join(self.config["imagesDir"], "boot.pdi")

        pdi_file = get_original_path(pdi_file)
        assert is_file(
            filepath=pdi_file, silent_discard=False
        ), f"File does not exist: {pdi_file}"
        f_msgs = [
            "Configuration timed out waiting for DONE",
            "No supported device found",
            "PLM Error",
            "no such file or directory",
            "PLM stalled during programming",
        ]
        try:
            self.runcmd(f"device program {pdi_file}", expected_failures=f_msgs)
        except Exception as e:
            self.set_proc("DPC")
            self.runcmd("mrd -bin 0xf2019000 1000", expected="Register Dump")
            err_match_obj = re.search(
                "PLM Error Status: .*", self.output(), re.IGNORECASE
            )
            if err_match_obj:
                log.error(err_match_obj.group())
                raise Exception(err_match_obj.group())
            else:
                log.error(e)
                raise Exception(e) from None

    def fpga(self, bit_file, timeout=200) -> None:
        """This method is used to load bit stream in to target
        Parameters:
                bit_file : Path to bit file
        """
        bit_file = get_original_path(bit_file)
        f_msgs = [
            f"Failed to download {bit_file}",
            "no such file or directory",
            "bit stream is not compatible",
        ]
        self.runcmd(f"fpga -f {bit_file}", expected_failures=f_msgs)

    def exit(self):
        if self.setup_hwserver:
            self.sendcontrol("c")
        if self.alive():
            self.runcmd(
                "exit", expected=self.hostname, wait_for_prompt=False, timeout=5
            )
