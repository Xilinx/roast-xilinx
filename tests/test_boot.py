#
# Copyright (c) 2022 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
import os
import pytest
from unittest.mock import call
from box import Box
import roast.component.board.boot
from roast.component.board.boot import *
from roast.component.board.boot import (
    switch_user,
    is_linux,
    is_linux_cons,
    _setup_linuxcons,
)
from roast.component.xsdb.xsdb import Xsdb
from roast.component.petalinux import petalinux_boot
from roast.component.board.board import Board
from roast.xexpect import Xexpect


@pytest.fixture
def test_board():
    return Board(board_type="network_target")


def class_test_board(mocker):
    board = Box(default_box=True)
    board.serial = mocker.Mock("board serial coms #0001")
    board.xsdb = mocker.Mock("board xsdb #0002")
    board.config = {}
    board.serial.sendline = mocker.Mock("board serial sendline #0003")

    return board


def test_BaseBoot_set_processor(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    mock_object.proc = None
    mock_object.set_processor()
    assert mock_object.proc.versal == "Versal *"
    assert mock_object.proc.a72_0 == "Cortex-A72*#0"
    assert mock_object.proc.a72_1 == "Cortex-A72*#1"
    assert mock_object.proc.a53_0 == "Cortex-A53*#0"
    assert mock_object.proc.a53_1 == "Cortex-A53*#1"
    assert mock_object.proc.r5_0 == "Cortex-R5*#0"
    assert mock_object.proc.r5_1 == "Cortex-R5*#1"
    assert mock_object.proc.a9_0 == "*Cortex-A9*#0"
    assert mock_object.proc.MB_PSM == "MicroBlaze PSM"
    assert mock_object.proc.MB_PPU == "MicroBlaze PPU"
    assert mock_object.proc.MB_PMU == "MicroBlaze PMU"
    assert mock_object.proc.MB == "MicroBlaze*#0"
    assert mock_object.proc.PSU == "PSU"
    assert mock_object.proc.ARM == "arm*#0"
    assert mock_object.proc.DPC == "DPC"


def test_BaseBoot_load_pmufw(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    mock_object.xsdbcon.load_elf = mocker.Mock("mock BaseRoot xsdbcon.load_elf #0004")
    mock_object.load_pmufw("path")
    mock_object.xsdbcon.load_elf.assert_called_with("path")


def test_BaseBoot_load_fsbl(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    mock_object.xsdbcon.load_elf = mocker.Mock("mock BaseRoot xsdbcon.load_elf #0005")
    mock_object.load_fsbl("path")
    mock_object.xsdbcon.load_elf.assert_called_with("path")


def test_BaseBoot_load_devicetree(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    dtb_loadaddr = 0xFF
    mock_object.xsdbcon.load_data = mocker.Mock("mock BaseRoot xsdbcon.load_data #0006")
    mock_object.load_devicetree(path, dtb_loadaddr)
    mock_object.xsdbcon.load_data.assert_called_with(path, dtb_loadaddr, timeout=400)


def test_BaseBoot_load_kernel(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    kernel_loadaddr = 0xFF
    mock_object.xsdbcon.load_data = mocker.Mock("mock BaseRoot xsdbcon.load_data #0007")
    mock_object.load_kernel(path, kernel_loadaddr)
    mock_object.xsdbcon.load_data.assert_called_with(path, kernel_loadaddr, timeout=400)


def test_BaseBoot_load_rootfs(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    rootfs_loadaddr = 0xFF
    mock_object.xsdbcon.load_data = mocker.Mock("mock BaseRoot xsdbcon.load_data #0008")
    mock_object.load_rootfs(path, rootfs_loadaddr)
    mock_object.xsdbcon.load_data.assert_called_with(
        path, rootfs_loadaddr, timeout=1800
    )


def test_BaseBoot_load_boot_scr(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    boot_scr_loadaddr = 0xFF
    mock_object.xsdbcon.load_data = mocker.Mock("mock BaseRoot xsdbcon.load_data #0009")
    mock_object.load_boot_scr(path, boot_scr_loadaddr)
    mock_object.xsdbcon.load_data.assert_called_with(
        path, boot_scr_loadaddr, timeout=400
    )


def test_BaseBoot_load_uboot(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    mock_object.xsdbcon.load_elf = mocker.Mock("mock BaseRoot xsdbcon.load_elf #0010")
    mock_object.load_uboot(path)
    mock_object.xsdbcon.load_elf.assert_called_with(path)


def test_BaseBoot_load_atf(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    mock_object.xsdbcon.load_elf = mocker.Mock("mock BaseRoot xsdbcon.load_elf #0011")
    mock_object.load_atf(path)
    mock_object.xsdbcon.load_elf.assert_called_with(path)


def test_BaseBoot_load_bitstream(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    mock_object.xsdbcon.fpga = mocker.Mock("mock BaseRoot xsdbcon.fpga #0012")
    mock_object.load_bitstream(path)
    mock_object.xsdbcon.fpga.assert_called_with(path)


def test_BaseBoot_set_proc(mocker):
    board = class_test_board(mocker)
    # creating mock objects for test execution
    mock_object = BaseBoot(board.serial, board.xsdb)
    path = "path"
    mock_object.xsdbcon.set_proc = mocker.Mock("mock BaseRoot xsdbcon.set_proc #0013")
    mock_object.set_proc(path)
    mock_object.xsdbcon.set_proc.assert_called_with(path)


def test_BootZynqmp__linux_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file", "boot_scr_loadaddr": 100}
    # creating mock objects for test execution
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object._load_bitstream = mocker.Mock("mocker BootZynqmp _load_bitstream #0014")
    mock_object._load_pmufw = mocker.Mock("mocker BootZynqmp _load_pmufw #0015")
    mock_object._load_fsbl = mocker.Mock("mocker BootZynqmp _load_fsbl #0016")
    mock_object._load_devicetree = mocker.Mock(
        "mocker BootZynqmp _load_devicetree #0017"
    )
    mock_object._load_uboot = mocker.Mock("mocker BootZynqmp _load_uboot #0018")
    mock_object._load_atf = mocker.Mock("mocker BootZynqmp _load_atf #0019")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynqmp xsdbcon.runcmd #0020")
    mock_object.xsdbcon.disconnect = mocker.Mock(
        "mocker BootZynqmp xsdbcon.disconnect #0021"
    )
    mocker_uboot_login = mocker.patch.object(roast.component.board.boot, "uboot_login")
    mock_object._load_kernel = mocker.Mock("mocker BootZynqmp _load_kernel #0022")
    mock_object._load_rootfs = mocker.Mock("mocker BootZynqmp _load_rootfs #0023")
    mock_object._load_boot_scr = mocker.Mock("mocker BootZynqmp _load_boot_scr")
    mock_object.serialcon.prompt = False
    mock_object.serialcon.sendline = mocker.Mock(
        "mocker BootZynqmp serialcon.sendline #0024"
    )

    mock_object._linux_boot()
    mock_object._load_bitstream.assert_called()
    mock_object._load_pmufw.assert_called()
    mock_object._load_fsbl.assert_called()
    mock_object._load_devicetree.assert_called()
    mock_object._load_uboot.assert_called()
    mock_object._load_atf.assert_called()
    calls = [
        call.mock_object.xsdbcon.runcmd("con"),
        call.mock_object.xsdbcon.runcmd("stop"),
        call.mock_object.xsdbcon.runcmd("con"),
    ]
    mock_object.xsdbcon.runcmd.assert_has_calls(calls)
    mock_object.xsdbcon.disconnect.assert_called()
    mocker_uboot_login.assert_called()
    mock_object._load_kernel.assert_called()
    mock_object._load_rootfs.assert_called()
    mock_object._load_boot_scr.assert_called()
    mock_object.serialcon.sendline.assert_called()


def test_BootZynqmp__uboot_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    # creating mock objects for test execution
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object._load_bitstream = mocker.Mock("mocker BootZynqmp _load_bitstream #0025")
    mock_object._load_pmufw = mocker.Mock("mocker BootZynqmp _load_pmufw #0026")
    mock_object._load_fsbl = mocker.Mock("mocker BootZynqmp _load_fsbl #0027")
    mock_object._load_devicetree = mocker.Mock(
        "mocker BootZynqmp _load_devicetree #0028"
    )
    mock_object._load_uboot = mocker.Mock("mocker BootZynqmp _load_uboot #0029")
    mock_object._load_atf = mocker.Mock("mocker BootZynqmp _load_atf #0030")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynqmp xsdbcon.runcmd #0031")
    mock_object.xsdbcon.disconnect = mocker.Mock(
        "mocker BootZynqmp xsdbcon.disconnect #0032"
    )
    mock_object._uboot_boot()
    mock_object._load_bitstream.assert_called()
    mock_object._load_pmufw.assert_called()
    mock_object._load_fsbl.assert_called()
    mock_object._load_devicetree.assert_called()
    mock_object._load_uboot.assert_called()
    mock_object._load_atf.assert_called()
    mock_object.xsdbcon.runcmd.assert_called_with("con")
    mock_object.xsdbcon.disconnect.assert_called()


def test_BootZynqmp__load_pmufw(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mocker BootZynqmp set_proc #0033")
    mock_object.xsdbcon.set_proc = mocker.Mock(
        "mocker BootZynqmp xsdbcon.set_proc #0034"
    )
    mock_object.xsdbcon.write = mocker.Mock("mocker BootZynqmp xsdbcon.write #0035")
    mock_object.load_pmufw = mocker.Mock("mocker BootZynqmp load_pmufw #0036")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynqmp xsdbcon.runcmd #0037")
    mock_object._load_pmufw()
    mock_object.set_proc.assert_called_once()
    mock_object.xsdbcon.set_proc.assert_called_once()
    mock_object.xsdbcon.write.assert_called_once()
    mock_object.load_pmufw.assert_called_once()
    mock_object.xsdbcon.runcmd.assert_called_once()


def test_BootZynqmp__load_fsbl(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mocker BootZynqmp set_proc #0038")
    mock_object.xsdbcon.rst_proc = mocker.Mock(
        "mocker BootZynqmp xsdbcon.rst_proc #0039"
    )
    mock_object.load_fsbl = mocker.Mock("mocker BootZynqmp load_fsbl #0040")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynqmp xsdbcon.runcmd #0041")
    mock_object._load_fsbl()
    mock_object.xsdbcon.rst_proc.assert_called()
    mock_object.load_fsbl.assert_called()
    calls = [
        call.mock_object.xsdbcon.runcmd("con"),
        call.mock_object.xsdbcon.runcmd("stop"),
    ]
    mock_object.xsdbcon.runcmd.assert_has_calls(calls)


def test_BootZynqmp__load_bitstream_case1(mocker):
    # is_rfdc_board in config
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "is_rfdc_board": "is_rfdc_board",
        "kernel_loadaddr": "kernel_loadaddr",
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_bitstream = mocker.Mock("mocker BootZynqmp load_bitstream #0042")
    mock_object.xsdbcon.write = mocker.Mock("mocker BootZynqmp xsdbcon.write #0043")
    mock_object._validate_address = mocker.Mock(
        "mocker BootZynqmp _validate_address #0044"
    )
    mock_object._load_bitstream()
    mock_object.load_bitstream.assert_called_with(f"{imagedir}/system.bit")
    isolation_data = {"0xFFD80118": "0x00800000", "0xFFD80120": "0x00800000"}
    pl_logic_reset = {
        "0xFF0a002C": "0x80000000",
        "0xFF0A0344": "0x80000000",
        "0xFF0A0348": "0x80000000",
        "0xFF0A0054": "0x0",
    }
    macros = {"0xFF0A0054": "0x80000000"}
    calls = [
        call.mock_object.xsdbcon.write(isolation_data),
        call.mock_object.xsdbcon.write(pl_logic_reset),
        call.mock_object.xsdbcon.write(macros),
    ]
    mock_object.xsdbcon.write.assert_has_calls(calls)
    mock_object._validate_address.assert_called()


def test_BootZynqmp__load_bitstream_case2(mocker):
    # is_rfdc_board not in config or has None
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "load_bitstream": "load_bitstream",
        "is_rfdc_board": None,
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_bitstream = mocker.Mock("mocker BootZynqmp load_bitstream #0045")
    mock_object._load_bitstream()
    mock_object.load_bitstream.assert_called_with(f"{imagedir}/system.bit")


def test_BootZynqmp__validate_address(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "kernel_image": "kernel_image",
        "kernel_loadaddr": "kernel_loadaddr",
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    addr_value = {"0reg": "0x0", "1": "0x1", "2": "0x2"}
    mock_object.xsdbcon.read = mocker.Mock("BootZynqmp xsdbcon.read #0046")
    mock_object.xsdbcon.read.side_effect = list(addr_value.keys())
    try:
        mock_object._validate_address(addr_value)
    except StopIteration:
        pass
    mock_object.xsdbcon.read.assert_called()


def test_BootZynqmp__load_kernel(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "kernel_image": "kernel_image",
        "kernel_loadaddr": "kernel_loadaddr",
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_kernel = mocker.Mock("mocker load kernel #0047")
    mock_object._load_kernel()
    mock_object.load_kernel.assert_called_with(
        f"{imagedir}/Image", config["kernel_loadaddr"]
    )


def test_BootZynqmp__load_rootfs(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "rootfs_path": "rootfs_path",
        "rootfs_loadaddr": "rootfs_loadaddr",
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_rootfs = mocker.Mock("mocker load rootfs #0048")
    mock_object._load_rootfs()
    mock_object.load_rootfs.assert_called_with(
        config["rootfs_path"], config["rootfs_loadaddr"]
    )


def test_BootZynqmp__load_devicetree(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "system_dtb": "system_dtb",
        "dtb_loadaddr": "dtb_loadaddr",
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_devicetree = mocker.Mock("mocker load devicetree #0049")
    mock_object._load_devicetree()
    mock_object.load_devicetree.assert_called_with(
        f"{imagedir}/{config['system_dtb']}",
        config["dtb_loadaddr"],
    )


def test_BootZynqmp__load_boot_scr(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "boot_scr_path": "boot_scr_path",
        "boot_scr_loadaddr": "boot_scr_loadaddr",
    }
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_boot_scr = mocker.Mock("mocker load_boot_scr #0050")
    mock_object._load_boot_scr()
    mock_object.load_boot_scr.assert_called_with(
        config["boot_scr_path"], config["boot_scr_loadaddr"]
    )


def test_BootZynqmp__load_atf(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_atf = mocker.Mock("mocker load_atf #0051")
    mock_object._load_atf()
    mock_object.load_atf.assert_called_with(f"{imagedir}/bl31.elf")


def test_BootZynqmp__load_uboot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynqmp(board.serial, board.xsdb, imagedir, config)
    mock_object.load_uboot = mocker.Mock("mocker load_uboot #0052")
    mock_object._load_uboot()
    mock_object.load_uboot.assert_called_with(f"{imagedir}/u-boot.elf")


def test_BootZynq__linux_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file", "boot_scr_loadaddr": 0xAB}
    mock_object = BootZynq(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mocker BootZynq set_proc #0053")
    mock_object.serialcon.sendline = mocker.Mock("mocker serialcon.sendline #0054")
    mock_object._load_fsbl = mocker.Mock("mocker BootZynq _load_fsbl #0055")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynq xsdbcon.runcmd #0056")
    mock_object._load_devicetree = mocker.Mock("mocker BootZynq _load_devicetree #0057")
    mock_object._load_uboot = mocker.Mock("mocker BootZynq _load_uboot #0058")
    mock_object.xsdbcon.disconnect = mocker.Mock(
        "mocker BootZynq xsdbcon.disconnect #0059"
    )
    mocker_uboot_login = mocker.patch.object(roast.component.board.boot, "uboot_login")
    mock_object._load_kernel = mocker.Mock("mocker BootZynq _load_kernel #0060")
    mock_object._load_rootfs = mocker.Mock("mocker BootZynq _load_rootfs #0061")
    mock_object._load_boot_scr = mocker.Mock("mocker BootZynq _load_boot_scr #0062")

    mock_object._linux_boot()

    calls = [
        call.mock_object.set_proc(mock_object.proc["ARM"]),
        call.mock_object.set_proc(mock_object.proc["ARM"]),
        call.mock_object.set_proc(mock_object.proc["ARM"]),
    ]
    mock_object.set_proc.assert_has_calls(calls)
    mock_object._load_fsbl.assert_called()
    mock_object._load_devicetree.assert_called()
    mock_object._load_uboot.assert_called()
    calls = [
        call.mock_object.xsdbcon.runcmd("con"),
        call.mock_object.xsdbcon.runcmd("stop"),
        call.mock_object.xsdbcon.runcmd("con"),
        call.mock_object.xsdbcon.runcmd("stop"),
        call.mock_object.xsdbcon.runcmd("con"),
    ]
    mock_object.xsdbcon.runcmd.assert_has_calls(calls)
    mock_object.xsdbcon.disconnect.assert_called()
    mocker_uboot_login.assert_called()
    mock_object._load_kernel.assert_called()
    mock_object._load_rootfs.assert_called()
    mock_object._load_boot_scr.assert_called()
    assert mock_object.serialcon.prompt == None
    mock_object.serialcon.sendline.assert_called()


def test_BootZynq__uboot_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynq(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mocker BootZynq set_proc #0063")
    mock_object._load_fsbl = mocker.Mock("mocker BootZynq _load_fsbl #0064")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynq xsdbcon.runcmd #0065")
    mock_object._load_devicetree = mocker.Mock("mocker BootZynq _load_devicetree #0066")
    mock_object._load_uboot = mocker.Mock("mocker BootZynq _load_uboot #0067")
    mock_object.xsdbcon.disconnect = mocker.Mock(
        "mocker BootZynq xsdbcon.disconnect #0068"
    )
    mock_object._uboot_boot()
    calls = [
        call.mock_object.set_proc(mock_object.proc["ARM"]),
        call.mock_object.set_proc(mock_object.proc["ARM"]),
        call.mock_object.set_proc(mock_object.proc["ARM"]),
    ]
    mock_object.set_proc.assert_has_calls(calls)
    mock_object._load_fsbl.assert_called()
    mock_object._load_devicetree.assert_called()
    mock_object._load_uboot.assert_called()
    calls = [
        call.mock_object.xsdbcon.runcmd("con"),
        call.mock_object.xsdbcon.runcmd("stop"),
        call.mock_object.xsdbcon.runcmd("con"),
    ]
    mock_object.xsdbcon.runcmd.assert_has_calls(calls)
    mock_object.xsdbcon.disconnect.assert_called()


def test_BootZynq__load_fsbl(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynq(board.serial, board.xsdb, imagedir, config)
    mock_object.load_fsbl = mocker.Mock("mocker load load_fsbl #0069")
    mock_object._load_fsbl()
    mock_object.load_fsbl.assert_called_with(f"{imagedir}/zynq_fsbl.elf")


def test_BootZynq__load_kernel(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootZynq(board.serial, board.xsdb, imagedir, config)
    mock_object.load_kernel = mocker.Mock("mocker load _kernel  #0070")
    mock_object._load_kernel()
    mock_object.load_kernel.assert_called_with(f"{imagedir}/uImage")


def test_BootMicroblaze__load_bitstream(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.load_bitstream = mocker.Mock("mocker load bitstream #0071")
    mock_object._load_bitstream()
    mock_object.load_bitstream.assert_called_with(f"{imagedir}/system.bit")


def test_BootMicroblaze__load_uboot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.load_uboot = mocker.Mock("mocker load_uboot #0072")
    mock_object._load_uboot()
    mock_object.load_uboot.assert_called_with(f"{imagedir}/u-boot")


def test_BootMicroblaze__load_kernel(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "kernel_image": "kernel_image",
        "kernel_loadaddr": "kernel_loadaddr",
    }
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.load_kernel = mocker.Mock("mocker load kernel #0073")
    mock_object._load_kernel()
    mock_object.load_kernel.assert_called_with(
        f"{imagedir}/{config['kernel_image']}",
        config["kernel_loadaddr"],
    )


def test_BootMicroblaze__load_devicetree(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "system_dtb": "system_dtb",
        "dtb_loadaddr": "dtb_loadaddr",
    }
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.load_devicetree = mocker.Mock("mocker load_devicetree #0074")
    mock_object._load_devicetree()
    mock_object.load_devicetree.assert_called_with(
        f"{imagedir}/{config['system_dtb']}",
        config["dtb_loadaddr"],
    )


def test_BootMicroblaze__load_rootfs(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "rootfs_path": "rootfs_path",
        "rootfs_loadaddr": "rootfs_loadaddr",
    }
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.load_rootfs = mocker.Mock("mocker load rootfs #0075")
    mock_object._load_rootfs()
    mock_object.load_rootfs.assert_called_with(
        config["rootfs_path"], config["rootfs_loadaddr"]
    )


def test_BootMicroblaze__load_boot_scr(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "boot_scr_path": "boot_scr_path",
        "boot_scr_loadaddr": "boot_scr_loadaddr",
    }
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.load_boot_scr = mocker.Mock("mocker load_boot_scr #0076")
    mock_object._load_boot_scr()
    mock_object.load_boot_scr.assert_called_with(
        config["boot_scr_path"], config["boot_scr_loadaddr"]
    )


def test_BootMicroblaze__linux_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "boot_scr_path": "boot_scr_path",
        "boot_scr_loadaddr": "boot_scr_loadaddr",
    }
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mocker BootZynq set_proc #0161")
    mock_object._load_bitstream = mocker.Mock("mocker BootZynq _load_bitstream #0162")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynq xsdbcon.runcmd #0163")
    mock_object._load_devicetree = mocker.Mock("mocker BootZynq _load_devicetree #0164")
    mock_object._load_uboot = mocker.Mock("mocker BootZynq _load_uboot #0165")
    mock_object.xsdbcon.disconnect = mocker.Mock(
        "mocker BootZynq xsdbcon.disconnect #0166"
    )
    mock_object._load_kernel = mocker.Mock("mocker BootZynq _load_kernel #0167")
    mock_object._load_rootfs = mocker.Mock("mocker BootZynq _load_rootfs #0168")
    mock_object._load_boot_scr = mocker.Mock("mocker BootZynq _load_boot_scr #0169")
    mock_object._linux_boot()
    mock_object.set_proc.assert_called()
    mock_object._load_bitstream.assert_called()
    mock_object.xsdbcon.runcmd.assert_called()
    mock_object._load_devicetree.assert_called()
    mock_object._load_uboot.assert_called()
    mock_object.xsdbcon.disconnect.assert_called()
    mock_object._load_kernel.assert_called()
    mock_object._load_rootfs.assert_called()
    mock_object._load_boot_scr.assert_called()


def test_BootMicroblaze__uboot_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {
        "pdi_file": "pdi_file",
        "boot_scr_path": "boot_scr_path",
        "boot_scr_loadaddr": "boot_scr_loadaddr",
    }
    mock_object = BootMicroblaze(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mocker BootZynq set_proc #0170")
    mock_object._load_bitstream = mocker.Mock("mocker BootZynq _load_bitstream #0171")
    mock_object.xsdbcon.runcmd = mocker.Mock("mocker BootZynq xsdbcon.runcmd #0172")
    mock_object._load_uboot = mocker.Mock("mocker BootZynq _load_uboot #0173")
    mock_object.xsdbcon.disconnect = mocker.Mock(
        "mocker BootZynq xsdbcon.disconnect #0174"
    )
    mock_object._uboot_boot()
    mock_object.set_proc.assert_called()
    mock_object._load_bitstream.assert_called()
    mock_object.xsdbcon.runcmd.assert_called()
    mock_object._load_uboot.assert_called()
    mock_object.xsdbcon.disconnect.assert_called()


def test_BootVersal_uboot_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}
    mock_object = BootVersal(board.serial, board.xsdb, imagedir, config)
    mock_object.xsdbcon.device_program = mocker.Mock("mock device_program #0077")
    mock_object._uboot_boot()
    mock_object.xsdbcon.device_program.assert_called()


def test_BootVersal_linux_boot(mocker):
    board = class_test_board(mocker)
    imagedir = os.path.join(".", "images")
    config = {"pdi_file": "pdi_file"}

    mock_object = BootVersal(board.serial, board.xsdb, imagedir, config)
    mock_object.set_proc = mocker.Mock("mock set proc")
    mock_object.xsdbcon.device_program = mocker.Mock("mock device_program #0078")
    mock_object.xsdbcon.stop = mocker.Mock("mock xsdbcon.stop #0079")
    mock_object.xsdbcon.runcmd = mocker.Mock("mock xsdbcon.runcmd #0080")
    mock_object._load_kernel = mocker.Mock("mock _load_kernel #0081")
    mock_object._load_rootfs = mocker.Mock("mock _load_rootfs #0082")
    mock_object._load_boot_scr = mocker.Mock("mock _load_boot_scr #0083")
    mock_object._linux_boot()
    mock_object.xsdbcon.device_program.assert_called()
    mock_object.xsdbcon.stop.assert_called()
    mock_object.xsdbcon.runcmd.assert_called()
    mock_object._load_kernel.assert_called()
    mock_object._load_rootfs.assert_called()
    mock_object._load_boot_scr.assert_called()


def test_linuxcons_case1(mocker):
    # is_linux(board) is True
    # pre_boot exists in config
    # board.serial exists
    board = Box(default_box=True)
    mocker_basebuild = mocker.patch.object(roast.component.board.boot, "Basebuild")
    mocker_basebuild.configure = mocker.Mock("basebuild config")
    board.config = {"pre_boot": "pre_boot"}
    mocker_is_linux = mocker.patch.object(roast.component.board.boot, "is_linux")
    mocker_is_linux.return_value = True
    board.is_linux = False
    board.target_ip = "none"
    board.invoke_xsdb = "invoke xsdb"
    board.invoke_hwserver = "incoke hardware"
    board.reboot = "reboot"
    board.serial = mocker.Mock("board serial #0084", return_value=1)
    board.serial.mode = "mode"
    board.start = mocker.Mock("board start")
    mocker_switch_user_root = mocker.patch.object(
        roast.component.board.boot, "switch_user_root"
    )
    mocker_copy_init_files = mocker.patch.object(
        roast.component.board.boot, "copy_init_files"
    )
    mocker_switch_user = mocker.patch.object(roast.component.board.boot, "switch_user")
    result = linuxcons(board.config, board)
    mocker_is_linux.assert_has_calls(
        [call.mocker_is_linux(board), call.mocker_is_linux(board)]
    )
    assert board.is_linux == True
    assert board.invoke_xsdb == False
    assert board.invoke_hwserver == False
    assert board.reboot == False
    assert board.serial.mode == False
    board.start.assert_called_once()
    mocker_switch_user_root.asser_called()
    mocker_copy_init_files.asser_called()
    mocker_switch_user.asser_called()
    assert result == board


def test_linuxcons_case2(mocker):
    # is_linux(board) is False
    # pre_boot exists in config
    # board.serial exists
    board = Box(default_box=True)
    mocker_basebuild = mocker.patch.object(roast.component.board.boot, "Basebuild")
    mocker_basebuild.configure = mocker.Mock("basebuild config #0085")
    board.config = {"pre_boot": "pre_boot"}
    mocker_is_linux = mocker.patch.object(roast.component.board.boot, "is_linux")
    mocker_is_linux.return_value = False
    board.is_linux = False
    board.target_ip = "none"
    board.invoke_xsdb = "invoke xsdb"
    board.invoke_hwserver = "incoke hardware"
    board.reboot = "reboot"
    board.serial = mocker.Mock("board serial #0086", return_value=1)
    board.serial.mode = "mode"
    board.start = mocker.Mock("board start #0087")
    try:
        linuxcons(board.config, board)
        print("Expected to raise exception but did not")
        assert 1 == 0
    except Exception:
        mocker_is_linux.assert_has_calls(
            [call.mocker_is_linux(board), call.mocker_is_linux(board)]
        )
        assert board.target_ip == None
        assert board.is_linux == True
        assert board.invoke_xsdb == False
        assert board.invoke_hwserver == False
        assert board.reboot == False
        assert board.serial.mode == False
        board.start.assert_called_once()


def test_linuxcons_case3(mocker):
    # is_linux(board) is False
    # pre_boot does not exists in config
    # board.serial exists
    board = Box(default_box=True)
    mocker_basebuild = mocker.patch.object(roast.component.board.boot, "Basebuild")
    mocker_basebuild.configure = mocker.Mock("basebuild config #0088")
    board.config = {}
    mocker_is_linux = mocker.patch.object(roast.component.board.boot, "is_linux")
    mocker_is_linux.return_value = False
    board.is_linux = False
    board.target_ip = "none"
    board.invoke_xsdb = "invoke xsdb"
    board.invoke_hwserver = "incoke hardware"
    board.reboot = "reboot"
    board.serial = mocker.Mock("board serial #0089", return_value=1)
    board.serial.mode = "mode"
    board.start = mocker.Mock("board start #0090")
    mocker_switch_user_root = mocker.patch.object(
        roast.component.board.boot, "switch_user_root"
    )
    mocker_copy_init_files = mocker.patch.object(
        roast.component.board.boot, "copy_init_files"
    )
    mocker_switch_user = mocker.patch.object(roast.component.board.boot, "switch_user")
    mocker_linux = mocker.patch.object(roast.component.board.boot, "linux")
    result = linuxcons(board.config, board)
    mocker_is_linux.assert_called_once()
    assert board.is_linux == False
    assert board.invoke_xsdb == True
    assert board.invoke_hwserver == True
    assert board.reboot == True
    assert board.first_boot == True
    assert board.serial.mode == "mode"
    board.start.assert_called_once()
    mocker_linux.assert_called()
    mocker_switch_user_root.asser_called()
    mocker_copy_init_files.asser_called()
    mocker_switch_user.asser_called()
    assert result == board


def test_linuxcons_case4(mocker):
    # is_linux(board) is False
    # pre_boot exists in config
    # board.serial does not exists
    board = Box(default_box=True)
    mocker_basebuild = mocker.patch.object(roast.component.board.boot, "Basebuild")
    mocker_basebuild.configure = mocker.Mock("basebuild config #0091")
    board.config = {"pre_boot": "pre_boot"}
    mocker_is_linux = mocker.patch.object(roast.component.board.boot, "is_linux")
    mocker_is_linux.return_value = False
    board.is_linux = False
    board.target_ip = "none"
    board.invoke_xsdb = "invoke xsdb"
    board.invoke_hwserver = "incoke hardware"
    board.reboot = "reboot"
    board.serial = None
    # board.serial.mode = "mode"
    board.start = mocker.Mock("board start #0092")
    try:
        linuxcons(board.config, board)
        print("Expected to raise exception but did not")
        assert 1 == 0
    except Exception:
        mocker_is_linux.assert_has_calls(
            [call.mocker_is_linux(board), call.mocker_is_linux(board)]
        )
        assert board.target_ip == None
        assert board.is_linux == True
        assert board.invoke_xsdb == False
        assert board.invoke_hwserver == False
        assert board.reboot == False
        board.start.assert_called_once()


def test_switch_user_root_case1(mocker):
    # target user not equal to root
    board = Box(default_box=True)
    board.serial.prompt.split = mocker.Mock("board split #0093", return_value=["user"])
    mocker_root_login = mocker.patch.object(roast.component.board.boot, "_root_login")
    board.target_user = ""
    switch_user_root(board)
    mocker_root_login.assert_called_once()
    assert board.target_user == "user"


def test_switch_user_root_case2(mocker):
    # target user equal to root
    board = Box(default_box=True)
    board.serial.prompt.split = mocker.Mock("board split #0094", return_value=["root"])
    board.target_user = ""
    switch_user_root(board)
    assert board.target_user == "root"


def test_copy_init_files_case1(mocker):
    # first boot is True and OsError is raised
    board = Box(default_box=True)
    board.first_boot = True
    board.config = {
        "tmp_value": "tmp_value",
        "board_init_files": {"1": "one.txt", "2": "two.txt"},
    }
    try:
        copy_init_files(board)
        print("Error Supposed to be raised but did not")
        assert 1 == 0
    except OSError:
        print("Case successful!")


def test_copy_init_files_case2(mocker):
    # first boot is True and OsError is not raised
    # re.search returns 1
    board = Box(default_box=True)
    board.first_boot = True
    board.config = {"tmp_value": "tmp_value", "board_init_files": {"1": "o"}}
    mocker_is_file = mocker.patch.object(roast.component.board.boot, "is_file")
    mocker_is_file.return_value = 1
    board.put = mocker.Mock("board put #0095")
    mocker_get_base_name = mocker.patch.object(
        roast.component.board.boot, "get_base_name"
    )
    mocker_get_base_name.return_value = "file"
    mocker_search = mocker.patch.object(roast.component.board.boot.re, "search")
    mocker_search.return_value = 1
    board.serial.runcmd = mocker.Mock("serial runcmd #0096")
    copy_init_files(board)
    assert board.first_boot == False
    mocker_is_file.assert_called()
    board.put.assert_called_once()
    mocker_get_base_name.assert_called_once()
    mocker_search.assert_called_once()
    calls = [
        call.board.serial.runcmd("cd 1"),
        call.board.serial.runcmd("tar xvf file"),
        call.board.serial.runcmd("cd"),
    ]
    board.serial.runcmd.assert_has_calls(calls)


def test_copy_init_files_case3(mocker):
    # first boot is True and OsError is not raised
    # re.search returns 0
    board = Box(default_box=True)
    board.first_boot = True
    board.config = {"tmp_value": "tmp_value", "board_init_files": {"1": "o"}}
    mocker_is_file = mocker.patch.object(roast.component.board.boot, "is_file")
    mocker_is_file.return_value = 1
    board.put = mocker.Mock("board put")
    mocker_get_base_name = mocker.patch.object(
        roast.component.board.boot, "get_base_name"
    )
    mocker_get_base_name.return_value = "file"
    mocker_search = mocker.patch.object(roast.component.board.boot.re, "search")
    mocker_search.return_value = 0
    board.serial.runcmd = mocker.Mock("serial runcmd #0097")
    copy_init_files(board)
    assert board.first_boot == False
    mocker_is_file.assert_called()
    board.put.assert_called_once()
    mocker_get_base_name.assert_called_once()
    mocker_search.assert_called_once()
    board.serial.runcmd.assert_called_with("cd")


def test_linux_case1(mocker):
    # case1 DEFAULT CALL & load_interface == "tcl"
    board = Box(default_box=True)
    board.xsdb = mocker.Mock("mock XSDB #0098")
    board.serial = mocker.Mock("serial cons #0099")
    board.config = {
        "component_deploy_dir": "component_deploy_dir",
        "load_interface": "tcl",
        "platform": "platform",
        "linux_run_tcl": "linux_run_tcl",
        "tcl_args": "tcl_args",
        "boottype": "prebuilt",
        "rootfs": "rootfs",
        "plnx_dtb": "plnx_dtb",
    }
    board.systest.systest_host = "host"
    mocker_linux_login_cons = mocker.patch.object(
        roast.component.board.boot, "linux_login_cons"
    )
    board.is_linux = False
    board.xsdb.run_tcl = mocker.Mock("mock xsdb runtcl #0100")
    board.xsdb.runcmd = mocker.Mock("mock xsdb runcmd #0101")
    linux(board)
    board.xsdb.run_tcl.assert_called_with("linux_run_tcl")
    failure_list = [
        "Configuration timed out waiting for DONE",
        "No supported device found",
        "PLM Error",
        "no such file or directory",
        "PLM stalled during programming",
    ]
    board.xsdb.runcmd.assert_called_with(
        board.config["tcl_args"], expected_failures=failure_list
    )
    mocker_linux_login_cons.assert_called_with(board.serial, timeout=500, login=True)
    assert board.is_linux == True


def test_linux_case2(mocker):
    # case2 user defined timeout & load_interface == "petalinux"
    # boottype = prebuilt
    board = Box(default_box=True)
    board.xsdb = mocker.Mock("mock XSDB #0102")
    board.serial = mocker.Mock("serial cons #0103")
    board.config = {
        "component_deploy_dir": "component_deploy_dir",
        "load_interface": "petalinux",
        "platform": "platform",
        "linux_run_tcl": "linux_run_tcl",
        "tcl_args": "tcl_args",
        "boottype": "prebuilt",
        "rootfs": "rootfs",
        "plnx_dtb": "plnx_dtb",
    }
    board.systest.systest_host = "host"
    mocker_petalinux_boot = mocker.patch.object(
        roast.component.board.boot, "petalinux_boot"
    )
    mocker_linux_login_cons = mocker.patch.object(
        roast.component.board.boot, "linux_login_cons"
    )
    board.is_linux = False
    # petalinux_boot("dsfsdf")
    linux(board, timeout=100)
    mocker_petalinux_boot.assert_called_with(
        board.config, hwserver="host", rootfs="rootfs", dtb="plnx_dtb"
    )
    mocker_linux_login_cons.assert_called_with(board.serial, timeout=100, login=True)


def test_linux_case3(mocker):
    # case3 user defined timeout & load_interface == "petalinux"
    # boottype = kernel
    board = Box(default_box=True)
    board.xsdb = mocker.Mock("mock XSDB #0104")
    board.serial = mocker.Mock("serial cons #0105")
    board.config = {
        "component_deploy_dir": "component_deploy_dir",
        "load_interface": "petalinux",
        "platform": "platform",
        "linux_run_tcl": "linux_run_tcl",
        "tcl_args": "tcl_args",
        "boottype": "kernel",
        "rootfs": "rootfs",
        "plnx_dtb": "plnx_dtb",
        "bitfile": "bitfile",
        "plnx_proj_path": "plnx_proj_path",
    }
    board.systest.systest_host = "host"
    mocker_petalinux_boot = mocker.patch.object(
        roast.component.board.boot, "petalinux_boot"
    )
    mocker_linux_login_cons = mocker.patch.object(
        roast.component.board.boot, "linux_login_cons"
    )
    board.is_linux = False
    # petalinux_boot("dsfsdf")
    linux(board, timeout=100)
    mocker_petalinux_boot.assert_called_with(
        board.config,
        boottype="kernel",
        bitfile="bitfile",
        proj_path="plnx_proj_path",
        hwserver="host",
        rootfs="rootfs",
        dtb="plnx_dtb",
    )
    mocker_linux_login_cons.assert_called_with(board.serial, timeout=100, login=True)


def test_linux_case4(mocker):
    # case4 user defined timeout & load_interface == "images"
    #
    board = Box(default_box=True)
    board.xsdb = mocker.Mock("mock XSDB #0106")
    board.serial = mocker.Mock("serial cons #0107")
    board.config = {
        "component_deploy_dir": "component_deploy_dir",
        "load_interface": "images",
        "platform": "platform",
        "linux_run_tcl": "linux_run_tcl",
        "tcl_args": "tcl_args",
        "boottype": "kernel",
        "rootfs": "rootfs",
        "plnx_dtb": "plnx_dtb",
        "bitfile": "bitfile",
        "plnx_proj_path": "plnx_proj_path",
    }
    board.systest.systest_host = "host"
    mocker_jtag_boot = mocker.patch.object(roast.component.board.boot, "jtag_boot")
    mocker_linux_login_cons = mocker.patch.object(
        roast.component.board.boot, "linux_login_cons"
    )
    board.is_linux = False
    linux(board, timeout=200)
    mocker_jtag_boot.assert_called_once()
    mocker_linux_login_cons.assert_called_with(board.serial, timeout=200, login=True)


def test_linux_login_case1(mocker):
    # default call
    board = Box(default_box=True)
    board.serial = mocker.Mock("serial cons #0108")
    mocker_linux_login_cons = mocker.patch.object(
        roast.component.board.boot, "linux_login_cons"
    )
    linux_login(board)
    mocker_linux_login_cons.assert_called()


def test_linux_login_case2(mocker):
    # user defined call
    board = Box(default_box=True)
    board.serial = mocker.Mock("serial cons #0109")
    mocker_linux_login_cons = mocker.patch.object(
        roast.component.board.boot, "linux_login_cons"
    )
    user = "user"
    password = "password"
    timeout = 100
    login = False
    linux_login(board, user, password, timeout, login)
    mocker_linux_login_cons.assert_called_with(
        board.serial, user="user", password="password", timeout=100, login=False
    )


def test_uboot_login_case1(mocker):
    # with default prompt
    mocker_cons = mocker.Mock("parent_cons #0110")
    mocker_cons.exit_nzero_ret = True
    mocker_cons.prompt = ""
    mocker_cons.sendcontrol = mocker.Mock("cons sendline #0111")
    mocker_cons.expect = mocker.Mock(name="expect #0112", return_value=1)
    uboot_login(mocker_cons)
    calls = [
        call.mocker_cons.expect(expected="Hit any key to stop autoboot"),
        call.mocker_cons.expect(expected="(ZynqMP>|Zynq>|U-Boot>|Versal> )"),
    ]
    mocker_cons.expect.assert_has_calls(calls)
    assert mocker_cons.exit_nzero_ret == False
    assert mocker_cons.prompt == "(ZynqMP>|Zynq>|U-Boot>|Versal> )"


def test_uboot_login_case2(mocker):
    # with user defined prompt
    mocker_cons = mocker.Mock("parent_cons #0113")
    mocker_cons.exit_nzero_ret = True
    mocker_cons.prompt = ""
    prompt = "user_prompt"
    mocker_cons.sendcontrol = mocker.Mock("cons sendline #0114")
    mocker_cons.expect = mocker.Mock(name="expect #0115", return_value=1)
    uboot_login(mocker_cons, prompt="user_prompt")
    calls = [
        call.mocker_cons.expect(expected="Hit any key to stop autoboot"),
        call.mocker_cons.expect(expected=prompt),
    ]
    mocker_cons.expect.assert_has_calls(calls)
    assert mocker_cons.exit_nzero_ret == False
    assert mocker_cons.prompt == prompt


def test_is_linux_cons_case1(mocker):
    # returns True and no exception encountered
    mocker_linuxcons = mocker.Mock("linuxcons #0115")
    mocker_linuxcons.sendcontrol = mocker.Mock("send control #0116")
    mocker_linuxcons.sendline = mocker.Mock("cons sendline #0117")
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    result = is_linux_cons(mocker_linuxcons)
    mocker_linuxcons.sendcontrol.assert_called_with("c")
    calls = [
        call.mocker_linuxcons.sendline("\r\n"),
        call.mocker_linuxcons.sendline("stty sane"),
    ]
    mocker_linuxcons.sendline.assert_has_calls(calls, any_order=False)
    mocker_setup_linuxcons.assert_called_once()
    assert result == True


def test_is_linux_cons_case2(mocker):
    # returns False and exception encountered
    mocker_linuxcons = mocker.Mock("linuxcons #0118")
    mocker_linuxcons.sendcontrol = None
    mocker_linuxcons.sendline = mocker.Mock("cons sendline #0119")
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    result = is_linux_cons(mocker_linuxcons)
    assert result == False


def test_linux_login_cons_case1(mocker):
    # case1 _if_login_index1 and default timeout = 500
    login = True
    user = "petalinux"
    password = "petalinux"
    mocker_cons = mocker.Mock("parent_cons #0120")
    mocker_cons.promt = ""
    mocker_cons.sendline = mocker.Mock("cons sendline #0121")
    mocker_cons.expect = mocker.Mock(name="expect #0122", return_value=1)
    mocker_cons.runcmd = mocker.Mock("run command #0123", return_value=1)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    linux_login_cons(mocker_cons, login=True)
    mocker_cons.sendline.assert_called_with("\r\n")
    calls = [
        call.mocker_cons.expect(expected="login:", timeout=500),
        call.mocker_cons.expect(expected="login:"),
    ]
    mocker_cons.expect.assert_has_calls(calls)
    calls = [
        call.mocker_cons.runcmd(user, expected=["Password:", "New password:"]),
        call.mocker_cons.runcmd(cmd=password, expected="Retype new password:"),
        call.mocker_cons.runcmd(cmd=password, expected=[r"~\$ ", r"~# "]),
    ]
    mocker_cons.runcmd.assert_has_calls(calls)
    mocker_setup_linuxcons.assert_called_once()


def test_linux_login_cons_case2(mocker):
    # case2 _if_login_index0 and given timeout
    login = True
    user = "petalinux"
    password = "petalinux"
    mocker_cons = mocker.Mock("parent_cons #0124")
    mocker_cons.promt = ""
    mocker_cons.sendline = mocker.Mock("cons sendline #0125")
    mocker_cons.expect = mocker.Mock(name="expect #0126", return_value=1)
    mocker_cons.runcmd = mocker.Mock("run command #0127", return_value=1)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    timeout = 100
    mocker_cons.runcmd.return_value = 0
    linux_login_cons(mocker_cons, login=True, timeout=timeout)
    mocker_cons.sendline.assert_called_with("\r\n")
    calls = [
        call.mocker_cons.expect(expected="login:", timeout=timeout),
        call.mocker_cons.expect(expected="login:"),
    ]
    mocker_cons.expect.assert_has_calls(calls)
    calls = [
        call.mocker_cons.runcmd(user, expected=["Password:", "New password:"]),
        call.mocker_cons.runcmd(cmd=password, expected=[r"~\$ ", r"~# "]),
    ]
    mocker_cons.runcmd.assert_has_calls(calls)
    mocker_setup_linuxcons.assert_called_once()


def test_linux_login_cons_case3(mocker):
    # case3 if login is not True
    login = False
    timeout = 100
    user = "petalinux"
    password = "petalinux"
    mocker_cons = mocker.Mock("parent_cons #0128")
    mocker_cons.expect = mocker.Mock(name="expect #0129", return_value=1)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    linux_login_cons(mocker_cons, login=False, timeout=timeout)
    mocker_cons.expect.assert_called_with(expected="~# ", timeout=timeout)
    mocker_setup_linuxcons.assert_called_once()


def test_user_login_root(mocker):
    from roast.component.board.boot import _user_login

    mocker_cons = mocker.Mock("parent_cons #0130")
    mocker_cons.promt = ""
    mocker_cons.sendline = mocker.Mock("cons sendline #0131")
    mocker_cons.expect = mocker.Mock(name="expect #0132", return_value=1)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    target_user = "root"
    user_name = "username"
    user_password = "userpassword"
    _user_login(mocker_cons, target_user, user_name, user_password)
    mocker_cons.sendline.assert_called_with(f"su -l {user_name}")
    mocker_cons.expect.assert_called_with(
        expected=r"\$ ", timeout=10, wait_for_prompt=False
    )
    mocker_setup_linuxcons.assert_called()


def test_user_login_else(mocker):
    from roast.component.board.boot import _user_login

    mocker_cons = mocker.Mock("parent_cons #0133")
    mocker_cons.promt = ""
    mocker_cons.sendline = mocker.Mock("cons sendline #0134")
    mocker_cons.expect = mocker.Mock(name="expect #0135", return_value=1)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    target_user = "username"
    user_name = "username"
    user_password = "userpassword"
    _user_login(mocker_cons, target_user, user_name, user_password)
    calls = [
        call.mocker_cons.sendline("sudo su -"),
        call.mocker_cons.sendline(user_password),
    ]
    mocker_cons.sendline.assert_has_calls(calls, any_order=False)
    calls = [
        call.mocker_cons.expect(expected=["~# ", "ubuntu:"], timeout=10),
        call.mocker_cons.expect(expected="~# ", timeout=10),
    ]
    mocker_cons.expect.assert_has_calls(calls)


def test_user_login_else_index0(mocker):
    from roast.component.board.boot import _user_login

    mocker_cons = mocker.Mock("parent_cons #0136")
    mocker_cons.prompt = ""
    mocker_cons.sendline = mocker.Mock("cons sendline #0137")
    mocker_cons.expect = mocker.Mock(name="expect #0138", return_value=0)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    target_user = "username"
    user_name = "username"
    user_password = "userpassword"
    _user_login(mocker_cons, target_user, user_name, user_password)
    mocker_cons.sendline.assert_called_with("sudo su -")
    mocker_cons.expect.assert_called_with(expected=["~# ", "ubuntu:"], timeout=10)
    assert mocker_cons.prompt == r"root(.*?)# "


def test_petalinux_login(mocker):
    from roast.component.board.boot import _petalinux_login

    mocker_cons = mocker.Mock("parent_cons #0139", return_value=mocker.Mock("cons"))
    mocker_cons.return_value.promt = ""
    mocker_cons.return_value.sendline = mocker.Mock("cons sendline #0140")
    mocker_cons.return_value.expect = mocker.Mock(name="expect #0141", return_value=1)
    mocker_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    _petalinux_login(mocker_cons.return_value)
    mocker_cons.return_value.sendline.assert_called_with("su -l petalinux")
    mocker_cons.return_value.expect.assert_called_with(
        expected=r"\$ ", timeout=10, wait_for_prompt=False
    )


def test_root_login(mocker):
    from roast.component.board.boot import _root_login

    board = Box(default_box=True)
    mocker_cons = mocker.Mock(
        "parent_cons #0142", return_value=mocker.Mock("cons #0143")
    )
    mocker_cons.return_value.promt = ""
    mocker_cons.return_value.sendline = mocker.Mock("cons sendline #0144")
    mocker_cons.return_value.expect = mocker.Mock(name="expect", return_value=1)
    mocker_cons.return_value._setup_init = mocker.Mock("setup init #0145")
    mocker_cons.return_value.runcmd = mocker.Mock("run command #0146", return_value=1)
    mocker_cons.return_value.exit_nzero_ret = True
    mocker_cons.return_value.sync = mocker.Mock("Sync #0147")
    # print("-->", type(mocker_cons.return_value))
    _root_login(mocker_cons.return_value)
    calls = [
        call.mocker_cons.return_value.sendline("sudo su -"),
        call.mocker_cons.return_value.sendline("petalinux"),
        call.mocker_cons.return_value.sendline("passwd root"),
        call.mocker_cons.return_value.sendline("root"),
        call.mocker_cons.return_value.sendline("root"),
    ]
    mocker_cons.return_value.sendline.assert_has_calls(calls, any_order=False)
    calls = [
        call.mocker_cons.return_value.expect(expected=["~# ", "Password:"], timeout=10),
        call.mocker_cons.return_value.expect(expected="~# ", timeout=10),
        call.mocker_cons.return_value.expect(expected="New password:", timeout=10),
        call.mocker_cons.return_value.expect(
            expected="Retype new password:", timeout=10
        ),
    ]
    mocker_cons.return_value.expect.assert_has_calls(calls)
    mocker_cons.return_value._setup_init.assert_called_once()
    calls = [
        call.mocker_cons.return_value.runcmd(r"PS1='\u:\t:\w\$ '", timeout=10),
        call.mocker_cons.return_value.runcmd("sed -i 's/-w//' /etc/default/dropbear"),
    ]
    mocker_cons.return_value.runcmd.assert_has_calls(calls)
    mocker_cons.return_value.sync.assert_called_once()


def test_root_login_index0(mocker):
    from roast.component.board.boot import _root_login
    from unittest.mock import call

    board = Box(default_box=True)
    mocker_cons = mocker.Mock(
        "parent_cons #0148", return_value=mocker.Mock("cons #0149")
    )
    mocker_cons.return_value.promt = ""
    mocker_cons.return_value.sendline = mocker.Mock("cons sendline #0150")
    mocker_cons.return_value.expect = mocker.Mock(name="expect #0151", return_value=0)
    mocker_cons.return_value._setup_init = mocker.Mock("setup init #0152")
    mocker_cons.return_value.runcmd = mocker.Mock("run command #0153", return_value=0)
    mocker_cons.return_value.exit_nzero_ret = True
    mocker_cons.return_value.sync = mocker.Mock("Sync #0154")
    # print("-->", type(mocker_cons.return_value))
    _root_login(mocker_cons.return_value)
    calls = [
        call.mocker_cons.return_value.sendline("sudo su -"),
        call.mocker_cons.return_value.sendline("passwd root"),
        call.mocker_cons.return_value.sendline("root"),
        call.mocker_cons.return_value.sendline("root"),
    ]
    mocker_cons.return_value.sendline.assert_has_calls(calls, any_order=False)
    calls = [
        call.mocker_cons.return_value.expect(expected=["~# ", "Password:"], timeout=10),
        call.mocker_cons.return_value.expect(expected="New password:", timeout=10),
        call.mocker_cons.return_value.expect(
            expected="Retype new password:", timeout=10
        ),
    ]
    mocker_cons.return_value.expect.assert_has_calls(calls)
    mocker_cons.return_value._setup_init.assert_called_once()
    calls = [
        call.mocker_cons.return_value.runcmd(r"PS1='\u:\t:\w\$ '", timeout=10),
        call.mocker_cons.return_value.runcmd("sed -i 's/-w//' /etc/default/dropbear"),
    ]
    mocker_cons.return_value.runcmd.assert_has_calls(calls)
    mocker_cons.return_value.sync.assert_called_once()


def test_set_prompt_case1(mocker):
    from roast.component.board.boot import _set_prompt

    board = Box(default_box=True)
    mocker_cons = mocker.Mock("parent_cons #0155")
    mocker_cons.return_value = mocker.Mock("child cons #0156")
    mocker_cons.return_value.runcmd = mocker.Mock("run command #0157", return_value=1)
    user_name = "username"
    mocker_cons.prompt = ""
    _set_prompt(mocker_cons.return_value, user_name)
    mocker_cons.return_value.runcmd.assert_called()
    assert mocker_cons.return_value.prompt == rf"{user_name}(.*?)\$ "


def test_set_prompt_case2(mocker):
    from roast.component.board.boot import _set_prompt

    board = Box(default_box=True)
    mocker_cons = mocker.Mock("parent_cons #0155")
    mocker_cons.return_value = mocker.Mock("child cons #0156")
    mocker_cons.return_value.runcmd = mocker.Mock("run command #0157", return_value=1)
    user_name = None
    mocker_cons.prompt = ""
    _set_prompt(mocker_cons.return_value)
    mocker_cons.return_value.runcmd.assert_called()
    assert mocker_cons.return_value.prompt == r"petalinux(.*?)\$ "


def test_set_prompt_index0(mocker):
    from roast.component.board.boot import _set_prompt

    board = Box(default_box=True)
    mocker_cons = mocker.Mock("parent_cons #0155")
    mocker_cons.return_value = mocker.Mock("child cons #0156")
    mocker_cons.return_value.runcmd = mocker.Mock("run command #0157", return_value=0)
    user_name = "username"
    mocker_cons.prompt = ""
    _set_prompt(mocker_cons.return_value)
    mocker_cons.return_value.runcmd.assert_called()
    assert mocker_cons.return_value.prompt == r"root(.*?)# "


def test_load_pdi(mocker):
    board = Box(default_box=True)
    board.config = {"imagesDir": os.path.join(".", "images")}
    pdi_file = os.path.join(board.config["imagesDir"], "boot.pdi")
    board.xsdb.device_program = mocker.Mock(
        "device program #0158", return_value="device_program"
    )
    board.serial.expect = mocker.Mock(name="expect #0159", return_value="serial_expect")
    load_pdi(board, pdi_file)
    board.xsdb.device_program.assert_called()
    board.serial.expect.asser_called()


def test_set_bootscr(mocker):
    import roast.component.osl.build_component

    board = Box(default_box=True)
    board.config = {"boot_scr_path": ""}
    variant = "zynqmp"
    set_bootscr(board.config, variant)
    test_scr_dir = os.path.dirname(
        inspect.getsourcefile(roast.component.osl.build_component)
    )
    assert board.config["boot_scr_path"] == os.path.join(test_scr_dir, f"{variant}.scr")


def test_set_rootfs(mocker):
    board = Box(default_box=True)
    board.config = {
        "board_interface": "host_target",
        "rootfs_path": "",
        "rootfs_base_path": "../",
        "platform": "",
    }
    set_rootfs(board.config)
    assert board.config["rootfs_path"] == ""


def test_jtag_boot(mocker):
    board = Box(default_box=True)

    board.config.run_as_root = True
    board.config.user = "my_user"
    board.serial.prompt = "petalinux(hostname)$ "
    mock_xsdb = mocker.patch(
        "roast.component.board.target_board.Xsdb", return_value="xsdb"
    )
    mocker_set_rootfs = mocker.patch.object(roast.component.board.boot, "set_rootfs")
    mocker_bootscr = mocker.patch.object(roast.component.board.boot, "set_bootscr")
    mocker_class_dict = mocker.patch.object(
        roast.component.board.boot,
        "BootZynqmp",
        return_value=mocker.Mock("class variant #0160"),
    )
    mocker_class_dict.return_value._linux_boot = mocker.Mock(return_value="linux_boot")
    # mocker_getattr = mocker.patch.object("getattr")
    jtag_boot(
        serialcon=board.serial,
        xsdbcon=mock_xsdb,
        config=board.config,
        imagesdir=os.path.join(".", "images"),
        variant="zynqmp",
        boot="linux",
    )
    mocker_set_rootfs.assert_called_with(board.config)
    mocker_bootscr.assert_called()
    mocker_class_dict.assert_called()


def test_switch_user_plnx_root(mocker):
    board = Box(default_box=True)
    board.config.run_as_root = True
    board.config.user = "my_user"
    board.serial.prompt = "petalinux(hostname)$ "

    mock_root_login = mocker.patch.object(roast.component.board.boot, "_root_login")
    switch_user(board=board)
    mock_root_login.assert_called_with(board.serial)
    assert board.target_user == "petalinux"
    assert board.target_password == "petalinux"


def test_switch_user_ubuntu_root(mocker):
    board = Box(default_box=True)
    board.config.run_as_root = True
    user_name = "my_user"
    user_passwd = "my_password"
    board.serial.prompt = "ubuntu(hostname)$ "
    target_user = board.serial.prompt.split("(")[0]

    mock_user_login = mocker.patch.object(roast.component.board.boot, "_user_login")
    switch_user(board=board, user_name=user_name, user_passwd=user_passwd)
    mock_user_login.assert_called_with(
        board.serial, target_user, user_name, user_passwd
    )
    assert board.target_user == "ubuntu"
    assert board.target_password == "ubuntu"


def test_switch_user_ubuntu_user(mocker):
    board = Box(default_box=True)
    board.config.run_as_root = False
    user_name = "my_user"
    user_passwd = "my_password"
    board.serial.prompt = "root(hostname)$ "
    user_name = "ubuntu"
    target_user = board.serial.prompt.split("(")[0]

    mock_user_login = mocker.patch.object(roast.component.board.boot, "_user_login")
    switch_user(board=board, user_name=user_name, user_passwd=user_passwd)
    mock_user_login.assert_called_with(
        board.serial, target_user, user_name, user_passwd
    )
    assert board.target_user == "root"
    assert board.target_password == "root"


def test_switch_user_plnx_user(mocker):
    board = Box(default_box=True)
    board.config.run_as_root = False
    board.serial.prompt = "root(hostname)$ "

    mock_plnx_login = mocker.patch.object(
        roast.component.board.boot, "_petalinux_login"
    )
    switch_user(board=board)
    mock_plnx_login.assert_called_with(board.serial)
    assert board.target_user == "root"
    assert board.target_password == "root"


def test_is_linux_plnx(mocker):
    board = Box(default_box=True)
    board.serial.prompt = "# "
    user = "petalinux"

    mock_is_linux_cons = mocker.patch.object(
        roast.component.board.boot, "is_linux_cons"
    )
    is_linux(board=board)
    mock_is_linux_cons.assert_called_with(
        board.serial, prompt=board.serial.prompt, user_name=user
    )


def test_is_linux_user(mocker):
    board = Box(default_box=True)
    board.serial.prompt = "# "
    user = "my_user"

    mock_is_linux_cons = mocker.patch.object(
        roast.component.board.boot, "is_linux_cons"
    )
    is_linux(board=board, user=user)
    mock_is_linux_cons.assert_called_with(
        board.serial, prompt=board.serial.prompt, user_name=user
    )


def test_is_linux_cons(mocker):
    user_name = None
    mock_xexpect = mocker.patch(
        "roast.serial.Xexpect", return_value=mocker.Mock("xexpect")
    )

    mock_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    is_linux_cons(linuxcons=mock_xexpect)
    mock_setup_linuxcons.assert_called_with(mock_xexpect, user_name)


def test_is_linux_cons_with_user(mocker):
    user_name = "my_user"
    mock_xexpect = mocker.patch(
        "roast.serial.Xexpect", return_value=mocker.Mock("xexpect")
    )

    mock_setup_linuxcons = mocker.patch.object(
        roast.component.board.boot, "_setup_linuxcons"
    )
    is_linux_cons(linuxcons=mock_xexpect, user_name=user_name)
    mock_setup_linuxcons.assert_called_with(mock_xexpect, user_name)


def test_setup_linuxcons(mocker):
    user_name = None

    mock_xexpect = mocker.patch(
        "roast.serial.Xexpect", return_value=mocker.Mock("xexpect")
    )

    mock_set_prompt = mocker.patch.object(roast.component.board.boot, "_set_prompt")
    _setup_linuxcons(cons=mock_xexpect)
    mock_set_prompt.assert_called_with(mock_xexpect, user_name)


def test_setup_linuxcons_with_user(mocker):
    user_name = "my_user"

    mock_xexpect = mocker.patch(
        "roast.serial.Xexpect", return_value=mocker.Mock("xexpect")
    )

    mock_set_prompt = mocker.patch.object(roast.component.board.boot, "_set_prompt")
    _setup_linuxcons(cons=mock_xexpect, user_name=user_name)
    mock_set_prompt.assert_called_with(mock_xexpect, user_name)
