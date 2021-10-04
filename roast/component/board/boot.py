#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import re
import inspect
from time import sleep
from roast.component.petalinux import petalinux_boot
from roast.component.basebuild import Basebuild
from roast.utils import convert_list, is_file, get_base_name, get_files
from box import Box


"""
These Classes holds methods that performs Linux Boot on target in Osl flow based on platform.
"""


class BaseBoot:
    def __init__(self, serialcon, xsdbcon):
        self.serialcon = serialcon
        self.xsdbcon = xsdbcon

    def set_processor(self):
        processor = Box(default_box=True, box_intact_types=[list, tuple])
        processor.versal = "Versal *"
        processor.a72_0 = "Cortex-A72*#0"
        processor.a72_1 = "Cortex-A72*#1"
        processor.a53_0 = "Cortex-A53*#0"
        processor.a53_1 = "Cortex-A53*#1"
        processor.r5_0 = "Cortex-R5*#0"
        processor.r5_1 = "Cortex-R5*#1"
        processor.a9_0 = "*Cortex-A9*#0"
        processor.MB_PSM = "MicroBlaze PSM"
        processor.MB_PPU = "MicroBlaze PPU"
        processor.MB_PMU = "MicroBlaze PMU"
        processor.MB = "MicroBlaze*#0"
        processor.PSU = "PSU"
        processor.ARM = "arm*#0"
        processor.DPC = "DPC"
        self.proc = processor

    def load_pmufw(self, elf_path):
        self.xsdbcon.load_elf(elf_path)
        sleep(5)

    def load_fsbl(self, fsbl_path):
        self.xsdbcon.load_elf(fsbl_path)
        sleep(5)

    def load_devicetree(self, dtb_path, dtb_loadaddr=0x100000):
        self.xsdbcon.load_data(dtb_path, dtb_loadaddr, timeout=400)
        sleep(5)

    def load_kernel(self, kernel_path, kernel_loadaddr=0x200000):
        self.xsdbcon.load_data(kernel_path, kernel_loadaddr, timeout=400)
        sleep(2)

    def load_rootfs(self, rootfs_path, rootfs_loadaddr=0x04000000):
        self.xsdbcon.load_data(rootfs_path, rootfs_loadaddr, timeout=1800)
        sleep(5)

    def load_boot_scr(self, boot_scr_path, boot_scr_loadaddr=0x20000000):
        self.xsdbcon.load_data(boot_scr_path, boot_scr_loadaddr, timeout=400)
        sleep(5)

    def load_uboot(self, uboot_path):
        self.xsdbcon.load_elf(uboot_path)
        sleep(5)

    def load_atf(self, atf_path):
        self.xsdbcon.load_elf(atf_path)
        sleep(5)

    def load_bitstream(self, bitfile_path):
        self.xsdbcon.fpga(bitfile_path)
        sleep(5)

    def set_proc(self, proc):
        self.xsdbcon.set_proc(proc)


class BootZynqmp(BaseBoot):
    def __init__(self, serialcon, xsdbcon, imagesdir, config):
        self.images_dir = imagesdir
        self.config = config
        super().__init__(serialcon, xsdbcon)
        self.set_processor()

    def _linux_boot(self):
        self._load_pmufw()
        self._load_fsbl()
        self._load_bitstream()
        self._load_devicetree()
        self._load_uboot()
        self._load_atf()
        self.xsdbcon.runcmd("con")
        uboot_login(self.serialcon)
        self.xsdbcon.runcmd("stop")
        self._load_kernel()
        self._load_rootfs()
        self._load_boot_scr()
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.disconnect()
        self.serialcon.prompt = None
        self.serialcon.sendline(f"source {hex(self.config['boot_scr_loadaddr'])}")

    def _uboot_boot(self):
        self._load_pmufw()
        self._load_fsbl()
        self._load_bitstream()
        self._load_devicetree()
        self._load_uboot()
        self._load_atf()
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.disconnect()

    def _load_pmufw(self):
        macros = {"0xffca0038": "0x1ff"}
        self.xsdbcon.set_proc(self.proc["PSU"])
        self.xsdbcon.write(macros)
        self.set_proc(self.proc["MB_PMU"])
        self.load_pmufw(f"{self.images_dir}/pmufw.elf")
        self.xsdbcon.runcmd("con")

    def _load_fsbl(self):
        self.set_proc(self.proc["a53_0"])
        self.xsdbcon.rst_proc()
        self.load_fsbl(f"{self.images_dir}/zynqmp_fsbl.elf")
        self.xsdbcon.runcmd("con")
        sleep(2)
        self.xsdbcon.runcmd("stop")

    def _load_bitstream(self):
        if self.config.get("is_rfdc_board"):
            isolation_data = {"0xFFD80118": "0x00800000", "0xFFD80120": "0x00800000"}
            pl_logic_reset = {
                "0xFF0a002C": "0x80000000",
                "0xFF0A0344": "0x80000000",
                "0xFF0A0348": "0x80000000",
                "0xFF0A0054": "0x0",
            }
            macros = {"0xFF0A0054": "0x80000000"}
            validate_macros = {"0xFF0A0344": "0x80000000", "0xFF0A0348": "0x80000000"}
            self.load_bitstream(f"{self.images_dir}/system.bit")
            self.xsdbcon.write(isolation_data)
            self.xsdbcon.write(pl_logic_reset)
            self._validate_address(validate_macros)
            sleep(5)
            self.xsdbcon.write(macros)
            sleep(5)

    def _validate_address(self, addr_value):
        for addr, value in addr_value.items():
            reg_value = self.xsdbcon.read(addr)
            assert hex(int(reg_value[0])) == value, "ERROR: Register value mismatch"

    def _load_kernel(self):
        self.load_kernel(f"{self.images_dir}/Image", self.config["kernel_loadaddr"])

    def _load_rootfs(self):
        self.load_rootfs(self.config["rootfs_path"], self.config["rootfs_loadaddr"])

    def _load_devicetree(self):
        self.load_devicetree(
            f"{self.images_dir}/{self.config['system_dtb']}",
            self.config["dtb_loadaddr"],
        )

    def _load_boot_scr(self):
        self.load_boot_scr(
            self.config["boot_scr_path"], self.config["boot_scr_loadaddr"]
        )

    def _load_atf(self):
        self.load_atf(f"{self.images_dir}/bl31.elf")

    def _load_uboot(self):
        self.load_uboot(f"{self.images_dir}/u-boot.elf")


class BootZynq(BootZynqmp):
    def __init__(self, serialcon, xsdbcon, imagesdir, config):
        super().__init__(serialcon, xsdbcon, imagesdir, config)

    def _linux_boot(self):
        self.set_proc(self.proc["ARM"])
        self._load_fsbl()
        self.xsdbcon.runcmd("con")
        sleep(2)
        self.xsdbcon.runcmd("stop")
        sleep(3)
        self.set_proc(self.proc["ARM"])
        self._load_uboot()
        sleep(2)
        self._load_devicetree()
        sleep(2)
        self.xsdbcon.runcmd("con")
        uboot_login(self.serialcon)
        self.xsdbcon.runcmd("stop")
        self.set_proc(self.proc["ARM"])
        sleep(2)
        self._load_kernel()
        self._load_rootfs()
        self._load_boot_scr()
        self.xsdbcon.runcmd("con")
        sleep(5)
        self.xsdbcon.disconnect()
        self.serialcon.prompt = None
        self.serialcon.sendline(f"source {hex(self.config['boot_scr_loadaddr'])}")

    def _uboot_boot(self):
        self.set_proc(self.proc["ARM"])
        self._load_fsbl()
        sleep(2)
        self.xsdbcon.runcmd("con")
        sleep(3)
        self.xsdbcon.runcmd("stop")
        self.set_proc(self.proc["ARM"])
        self._load_devicetree()
        sleep(2)
        self.set_proc(self.proc["ARM"])
        self._load_uboot()
        sleep(2)
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.disconnect()

    def _load_fsbl(self):
        self.load_fsbl(f"{self.images_dir}/zynq_fsbl.elf")

    def _load_kernel(self):
        self.load_kernel(f"{self.images_dir}/uImage")


class BootMicroblaze(BootZynqmp):
    def __init__(self, serialcon, xsdbcon, imagesdir, config):
        super().__init__(serialcon, xsdbcon, imagesdir, config)

    def _load_bitstream(self):
        self.load_bitstream(f"{self.images_dir}/system.bit")

    def _load_uboot(self):
        self.load_uboot(f"{self.images_dir}/u-boot")

    def _load_kernel(self):
        self.load_kernel(
            f"{self.images_dir}/{self.config['kernel_image']}",
            self.config["kernel_loadaddr"],
        )

    def _load_devicetree(self):
        self.load_devicetree(
            f"{self.images_dir}/{self.config['system_dtb']}",
            self.config["dtb_loadaddr"],
        )

    def _load_rootfs(self):
        self.load_rootfs(self.config["rootfs_path"], self.config["rootfs_loadaddr"])

    def _load_boot_scr(self):
        self.load_boot_scr(
            self.config["boot_scr_path"], self.config["boot_scr_loadaddr"]
        )

    def _linux_boot(self):
        self._load_bitstream()
        sleep(2)
        self.set_proc(self.proc["MB"])
        self.xsdbcon.runcmd("catch {stop}")
        sleep(1)
        self._load_uboot()
        sleep(2)
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.runcmd("stop")
        self.set_proc(self.proc["MB"])
        self._load_kernel()
        sleep(2)
        self.set_proc(self.proc["MB"])
        self._load_devicetree()
        sleep(2)
        self.set_proc(self.proc["MB"])
        self._load_rootfs()
        sleep(2)
        self.set_proc(self.proc["MB"])
        self._load_boot_scr()
        self.xsdbcon.runcmd("con")
        sleep(2)
        self.xsdbcon.disconnect()

    def _uboot_boot(self):
        self._load_bitstream()
        sleep(2)
        self.set_proc(self.proc["MB"])
        self.xsdbcon.runcmd("catch {stop}")
        sleep(1)
        self._load_uboot()
        sleep(2)
        self.xsdbcon.runcmd("con")
        sleep(1)
        self.xsdbcon.disconnect()


class BootVersal(BootZynqmp):
    def __init__(self, serialcon, xsdbcon, imagesdir, config):
        super().__init__(serialcon, xsdbcon, imagesdir, config)

    def _linux_boot(self):
        self.set_proc(self.proc["versal"])
        self.xsdbcon.device_program(self.config["pdi_file"])
        self.xsdbcon.stop()
        sleep(3)
        self.serialcon.prompt = None
        self._load_kernel()
        self._load_rootfs()
        self._load_boot_scr()
        self.xsdbcon.runcmd("con")

    def _uboot_boot(self):
        self.xsdbcon.device_program(self.config["pdi_file"])


def jtag_boot(serialcon, xsdbcon, config, imagesdir, variant, boot="linux"):
    set_rootfs(config)
    set_bootscr(config, variant)
    class_dict = {
        "zynqmp": BootZynqmp,
        "zynq": BootZynq,
        "microblaze": BootMicroblaze,
        "versal": BootVersal,
    }
    # Instatiating Boot class based on variant passed
    BootLinux = class_dict[variant](serialcon, xsdbcon, imagesdir, config)
    getattr(BootLinux, f"_{boot}_boot")()


def set_rootfs(config):
    if not config["rootfs_path"].endswith("cpio.gz.u-boot"):
        files = get_files(
            f"{config['rootfs_base_path']}/{config['platform']}",
            extension="cpio.gz.u-boot",
            abs_path=True,
        )
        config["rootfs_path"] = "".join(files)


def set_bootscr(config, variant):
    import roast.component.osl.build_component

    if not config["boot_scr_path"].endswith(".scr"):
        scr_dir = os.path.dirname(
            inspect.getsourcefile(roast.component.osl.build_component)
        )
        config["boot_scr_path"] = os.path.join(scr_dir, f"{variant}.scr")


def load_pdi(
    board, pdi_file=None, expected_msg="Total PLM Boot Time", expected_failures=None
) -> None:
    board.xsdb.device_program(pdi_file)
    board.serial.expect(
        expected=expected_msg,
        expected_failures=expected_failures,
        err_index=len(convert_list(expected_failures)),
    )


def linux_login_cons(
    cons, user="root", password="root", login=True, timeout=500
) -> None:
    """This Function is to login on target linux
    Parameters:
        cons - console was acquired serial or qemu instance.
        user - userid for target login
        password - password to login on target
        login - False flag will look for auto login
    """
    if login:
        cons.expect(expected="login:", timeout=timeout)
        cons.sendline("\r\n")
        cons.expect(expected="login:")
        cons.runcmd(user, expected="Password:")
        cons.runcmd(cmd=password, expected="~# ")
    else:
        cons.expect(expected="~# ", timeout=timeout)
    cons.prompt = r"root(.*?)# "
    cons.runcmd(r"PS1='\u:\t:\w\$ '", timeout=10)
    cons._setup_init()
    cons.exit_nzero_ret = True


def is_linux_cons(linuxcons, prompt="# ") -> bool:
    """This Function is to login on target linux
    Parameters:
       linuxcons - linuxcons was target serial or qemu instance
    """
    ret = True
    try:
        linuxcons.sendcontrol("c")
        linuxcons.sendline("\r\n")
        linuxcons.prompt = prompt
        linuxcons.runcmd("cd", timeout=10)
        linuxcons.prompt = r"root(.*?)# "
        linuxcons.runcmd(r"PS1='\u:\t:\w\$ '", timeout=10)
        linuxcons.sync()
        linuxcons._setup_init()
        linuxcons.exit_nzero_ret = True
    except Exception as err:
        ret = False
    return ret


def uboot_login(cons, prompt="(ZynqMP>|Zynq>|U-Boot>|Versal> )") -> None:
    """This Function is to acquite uboot on target
    Parameters:
       cons - console was acquired serial or qemu instance.
    """
    cons.exit_nzero_ret = False
    cons.expect(expected="Hit any key to stop autoboot")
    cons.sendcontrol("x")
    cons.expect(expected=prompt)
    cons.prompt = prompt


def linux_login(board, user="root", password="root", timeout=500, login=True) -> None:
    linux_login_cons(
        board.serial, user=user, password=password, login=login, timeout=timeout
    )


def is_linux(board, prompt="# ") -> bool:
    ret = is_linux_cons(board.serial, prompt="# ")
    return ret


def linux(board, timeout=500, expected_msg="Total PLM Boot Time") -> None:

    xsdbcon = board.xsdb
    serialcon = board.serial
    config = board.config
    images_dir = config["component_deploy_dir"]

    load_interface = config["load_interface"]
    variant = config["platform"]

    if load_interface == "tcl":
        xsdbcon.run_tcl(config["linux_run_tcl"])
        if config.get("tcl_args"):
            xsdbcon.runcmd(config["tcl_args"])
    elif load_interface == "petalinux":
        if board.config["boottype"] == "prebuilt":
            petalinux_boot(
                board.config,
                hwserver=board.systest.systest_host,
                rootfs=board.config.get("rootfs"),
            )
        elif board.config["boottype"] == "kernel":
            petalinux_boot(
                board.config,
                boottype="kernel",
                bitfile=board.config.get("bitfile"),
                proj_path=board.config["plnx_proj_path"],
                hwserver=board.systest.systest_host,
                rootfs=board.config.get("rootfs"),
            )

    elif load_interface == "images":
        jtag_boot(serialcon, xsdbcon, config, images_dir, variant)
    # Wait for Linux console
    linux_login_cons(
        board.serial, timeout=timeout, login=(not board.config.get("autologin", False))
    )
    board.is_linux = True


def copy_init_files(board):
    # Copy init files after boot.
    if board.first_boot:
        for dst_path, src_files in (board.config.get("board_init_files", {})).items():
            for src_file in src_files:
                board.config["tmp_value"] = src_file
                # Check if file is present on host machine
                if not is_file(board.config["tmp_value"]):
                    print(f"ERROR: No Such File: {board.config['tmp_value']}")
                    raise OSError
                board.put(board.config["tmp_value"], dst_path)
                # Check if file is tar, then extract it with -C dst_path
                f_name = get_base_name(board.config["tmp_value"])
                if re.search(r"\.tar", f_name):
                    board.serial.runcmd(f"cd {dst_path}")
                    board.serial.runcmd(f"tar xvf {f_name}")
        board.serial.runcmd("cd")
        board.first_boot = False


def linuxcons(config, board_session, timeout=1000, expected_msg="Total PLM Boot Time"):
    board = board_session
    bb = Basebuild(config, setup=False)
    bb.configure()
    board.config = config

    if is_linux(board):
        board.is_linux = True
    else:
        board.is_linux = False
        board.target_ip = None

    pre_boot = config.get("pre_boot")
    if pre_boot:
        board.is_linux = True

    # Check for board live status
    if board.is_linux:
        board.invoke_xsdb = False
        board.invoke_hwserver = False
        board.reboot = False
        if board.serial:
            board.serial.mode = False
        board.start()
        if not is_linux(board):
            raise Exception("ERROR: No linux prompt")

    elif not pre_boot:
        # boot till linux
        board.is_linux = False
        board.invoke_xsdb = True
        board.invoke_hwserver = True
        board.reboot = True
        board.first_boot = True
        board.start()
        linux(board, timeout, expected_msg)

    copy_init_files(board)
    return board
