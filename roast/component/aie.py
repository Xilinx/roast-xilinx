#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import time
import sys
import logging
from roast.component.board.boot import load_pdi, is_linux, linuxcons
from roast.utils import is_file, copyDirectory, get_original_path
from roast.component.cardano import check_cardano

log = logging.getLogger(__name__)


def run_plm(
    board,
    expected_msg="Total PLM Boot Time",
    expected_failures=None,
    load_aie_pdi=False,
):
    if load_aie_pdi:
        load_pdi(
            board, pdi_file=board.config["aie_pdi"], expected_failures=expected_failures
        )
    load_pdi(board, expected_msg=expected_msg, expected_failures=expected_failures)


def run_std_app(board, procname, load_boot_pdi=False):
    load_pdi(board, pdi_file=board.config["aie_pdi"])
    if load_boot_pdi:
        load_pdi(board, expected_msg="SBI PDI Load: Done")
    board.xsdb.set_proc(procname)
    board.xsdb.rst_proc()
    time.sleep(5)
    aie_elf = f"{board.config['imagesDir']}/aie_control.elf"
    if not is_file(aie_elf):
        print(f"ERROR: No Such File {aie_elf}", file=sys.stderr)
        raise Exception("Build test Failed")
    board.xsdb.load_elf(f"{board.config['imagesDir']}/aie_control.elf")
    board.xsdb.runcmd("con")


def run_aie_demo(board):
    board.serial.prompt = "# "
    board.serial.runcmd(
        "aie-matrix-multiplication",
        expected="Success!",
        expected_failures="ERROR: XGeMM Failed!",
        timeout=600,
        err_msg="aie-matrix-multiplication Failed!",
    )


def copy_linux_app(board):
    test = board.config["test"]
    src_file = f"{board.config['imagesDir']}/deploy_artifacts.tar.xz"
    board.put(src_file, "~/")
    # board.serial.terminal.interact()

    board.serial.runcmd(f"mkdir -p ~/{test}")
    cmd_list = [f"tar xvf deploy_artifacts.tar.xz -C {test}/", f"cd {test}"]
    board.serial.runcmd_list(cmd_list)


def run_linux_app(board):
    test = board.config["test"]
    wait_for_prompt = False if test == "clock_gating" else True
    board.serial.runcmd("lsmod", expected="\r\n")
    if "zocl" in board.serial.output():
        board.serial.runcmd("rmmod zocl &> /dev/null")
        board.serial.runcmd(
            "modprobe zocl",
            expected="Initialized zocl",
            err_msg="Loading zocl module failed",
        )
    try:
        if board.config.get("cardano_app"):
            cmd = "./aie_control_xrt.run ./aie_xrt.xclbin"
        else:
            cmd = "./aie_control.run"

        board.serial.runcmd(
            cmd,
            wait_for_prompt=wait_for_prompt,
            expected=board.config.get("expected_str", "SUCCESS"),
            expected_failures=[
                "FAILED",
                "Segmentation fault",
                "Aborted",
                "Device open error",
            ],
        )
    except Exception as err:
        # Reset console to normal state for consecutive tests
        is_linux(board)
        assert False, err


def copy_linux_test_images(config, test):
    linux_images = f"{config['buildDir']}/{config['machine']}/{test}/linux/images/"
    src_file = f"{linux_images}/deploy_artifacts.tar.xz"
    if not is_file(src_file):
        log.error(f"ERROR: No Such File {src_file}")
        raise Exception("Build test Failed")
    copyDirectory(linux_images, config["imagesDir"])
    check_cardano(config)


def petalinux_aie_boot(config, board_session, boottype):
    config["plnx_proj"] = config["PLNX_BSP"]
    config["load_interface"] = "tcl"
    config["boottype"] = boottype
    plnx_bsp_path = get_original_path(f"{config.BSP_PATH}/{config.PLNX_BSP}")

    # check for PLNX BSP before acquiring board
    if not is_file(plnx_bsp_path):
        print(f"Petalinux BSP {plnx_bsp_path} Not found", file=sys.stderr)
        raise Exception("Petalinux BSP Not found")

    if config.get("load_interface") == "tcl":
        for artifact in config.get("plnx_artifacts", []):
            if not is_file(f"{config.get('deploy_dir')}/{artifact}"):
                log.error(f"{artifact} not found in {config.get('deploy_dir')}")
                raise Exception("Petalinux Build test Failed")
    if boottype == "kernel":
        config[
            "plnx_proj_path"
        ] = f"{config['buildDir']}/{config['machine']}/petalinux/default_build/work/{config['PLNX_BSP']}"

    board_session.invoke_xsdb = False
    board = linuxcons(config, board_session)
    return board
