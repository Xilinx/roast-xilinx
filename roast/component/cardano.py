#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import glob
import logging
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.xexpect import Xexpect
from roast.component.basebuild import Basebuild
from roast.component.xsct import buildapp as xsct
from roast.component.crosscompile.crosscompile import baremetal_runner
from roast.component.bif.generate import pdi
from filelock import FileLock

log = logging.getLogger(__name__)


class Cardano(Basebuild):
    def __init__(self, config, setup=True):
        super().__init__(config, setup)
        self.console = Xexpect(log, exit_nzero_ret=True)

    def configure(self):
        super().configure()
        self.srcDir = os.path.join(self.workDir, "src")
        self.cdoDir = os.path.join(self.workDir, "Work/ps/cdo")

        VITIS_DIR = self.config.vitisPath
        AIETOOLS_ROOT = self.config.AIETOOLS_ROOT
        SYSROOT = self.config.SYSROOT
        PFM_XPFM = self.config.PFM_XPFM
        XLNX_LICENSE = self.config["XILINXD_LICENSE_FILE"]
        cmdlist = [
            f"export XILINXD_LICENSE_FILE={XLNX_LICENSE}",
            f"export VITIS_DIR={VITIS_DIR}",
            f"export AIETOOLS_ROOT={AIETOOLS_ROOT}",
            f"export XILINX_VITIS_AIETOOLS={AIETOOLS_ROOT}",
            f"export SYSROOT={SYSROOT}",
            f"export PFM_XPFM={PFM_XPFM}",
            f"export PATH={VITIS_DIR}/bin:$PATH",
            f"source {self.config.vitisPath}/settings64.sh",
        ]
        self.console.runcmd_list(cmdlist)

    def compile_cardano_app(self):

        self.console.runcmd(f"cd {self.workDir}")
        # compile cardano and generate cdo
        compile_cmd = [
            "aiecompiler -v",
            self.config["CARDANO_FLAGS"],
            f'-include="{self.srcDir}/kernels"',
            f'-include="{self.srcDir}"',
            f'{self.srcDir}/{self.config["cardano_src"]}.cpp',
        ]
        cmd = " ".join(compile_cmd)

        timeout = int(self.config.get("cardano_timeout", 800))
        self.console.runcmd(
            cmd, timeout=timeout, err_msg="Cardano App Compilation Failure"
        )

    def gen_xclbin(self):

        gen_cmd = [
            "v++ -s -p -t hw",
            f"--platform {self.config.PFM_XPFM}",
            f"--package.out_dir {self.workDir} --package.defer_aie_run",
            f"--config {self.config.vpp_package_path}/package.cfg",
            f"-o aie_xrt.xclbin",
            f"{self.workDir}/libadf.a",
        ]
        cmd = " ".join(gen_cmd)
        timeout = int(self.config.get("vpp_timeout", 600))
        self.console.runcmd(cmd, timeout=timeout, err_msg="xclbin generation failed")

    def generate_pdis(self):
        self.config["console"] = self.console
        assert pdi(self.config, "new"), "ERROR: PDI Generation failed"

    def copy_images(self):
        ret = False
        try:
            mkdir(f"{self.imagesDir}/elfs")
            mkdir(f"{self.imagesDir}/src")
            self.elfs = glob.glob(f"{self.workDir}/Work/aie/{self.config['tiles']}")
            for elf in self.elfs:
                name = os.path.basename(elf)
                copy_file(f"{elf}/Release/{name}", f"{self.imagesDir}/elfs")
            self.cdos = get_files(self.cdoDir, extension="bin")
            for cdo in self.cdos:
                copy_file(f"{self.cdoDir}/{cdo}", f"{self.imagesDir}")
            self.control_cpps = get_files(
                f"{self.workDir}/Work/ps/c_rts/", extension="cpp"
            )
            for cpp in self.control_cpps:
                copy_file(
                    f"{self.workDir}/Work/ps/c_rts/{cpp}",
                    f"{self.imagesDir}/src",
                )
            self.xclbin = get_files(self.workDir, extension="xclbin")
            for xclbin in self.xclbin:
                copy_file(f"{self.workDir}/{xclbin}", self.imagesDir)

            copyDirectory(f"{self.workDir}/Work", f"{self.imagesDir}/Work")

            ret = True
        except Exception as err:
            log.error(err)
        return ret

    def simulate_cardano_app(self):
        self.console.runcmd(f"cd {self.workDir}")
        if self.config.get("generate_input_data") and self.config.get("generate_src"):
            gen_cmd = [
                f"{self.config.AIETOOLS_ROOT}/tps/lnx64/gcc/bin/g++",
                "-static-libstdc++ -std=c++11",
                f"-I {self.workDir}/Work/temp/",
                f"{self.workDir}/src/{self.config.generate_src}.cpp",
                f"-o {self.workDir}/{self.config.generate_src}.out",
            ]
            cmd = " ".join(gen_cmd)
            self.console.runcmd(cmd)
            self.console.runcmd(f"{self.workDir}/{self.config.generate_src}.out")
        timeout = int(self.config.get("simulation_timeout", 700))
        self.console.runcmd(
            f"aiesimulator --pkg-dir={self.workDir}/Work",
            timeout=timeout,
            err_msg="Cardano app Simulation Failed",
        )

    def incremental_build(self):
        if self.config.external_aienginev2 and self.config.get("external_cardano_src"):
            self.config.AIETOOLS_ROOT = (
                f"{self.config.external_cardano_src}/prep/rdi/aietools"
            )
            self.console.runcmd(
                f"source {self.config.AIETOOLS_ROOT}/scripts/aietools_env.sh"
            )

            lock_path = os.path.join(
                get_abs_path(self.config.external_cardano_src),
                "src/products/cardano/",
                "incremental_build.lock",
            )
            lock = FileLock(lock_path)
            with lock:
                build_number = os.getenv("BUILD_NUMBER")
                if not check_if_string_in_file(
                    f"{self.config.external_cardano_src}/logs/incremetal_build.log",
                    build_number,
                ):
                    self.console.runcmd(
                        f"sh {self.config.external_cardano_src}/incremental_build.sh {self.config.external_aienginev2}",
                        expected="Incremental Build SUCCESSFUL",
                        expected_failures=["Incremental Build FAILED"],
                        timeout=3000,
                    )
                else:
                    if check_if_string_in_file(
                        f"{self.config.external_cardano_src}/logs/incremetal_build.log",
                        "Incremental Build FAILED",
                    ):
                        raise Exception("ERROR: Incremental Build FAILED")


def cardano_builder(config):
    btc = Cardano(config, setup=True)
    btc.configure()
    btc.incremental_build()
    btc.compile_cardano_app()
    btc.gen_xclbin()
    assert btc.copy_images(), "ERROR: Build Cardano Failed!"


def cardano_simulator(config):
    btc = Cardano(config, setup=False)
    btc.configure()
    if not is_file(f"{btc.config.workDir}/aie_xrt.xclbin"):
        log.error(f"No Such File {btc.config.workDir}/aie_xrt.xclbin")
        raise Exception("Build test Failed")
    btc.simulate_cardano_app(), "ERROR: Cardano Simulation Failed"


def generate_pdi_aie(config):
    bc = Basebuild(config)
    copyDirectory(config["elfs_path"], config["imagesDir"])
    assert pdi(config), "ERROR: PDI Generation failed"


def standalone_builder(config):
    xsct.xsct_builder(config)
    copyDirectory(config["elfs_path"], config["imagesDir"])
    assert pdi(config), "ERROR: PDI Generation failed"


def baremetal_lib(config, proc, setup=True):
    overrides(config, "std")
    overrides(config, proc)
    builder = xsct.AppBuilder(config, setup=setup)
    args = builder.parser(config)
    args = builder.clone_esw(args)
    builder.set_user_args(args)
    if builder.config.get("xsct_outDir", ""):
        mkdir(builder.config.xsct_outDir)

    if builder.config.get("baremetal_lib_component") == "aienginev2":
        # copy esw to workDir if external esw is given
        if builder.config.get("external_embeddedsw", ""):
            external_esw_src = builder.config.external_embeddedsw.rstrip("/")
            builder.runner.runcmd(
                cmd=f"rsync -aqv --exclude '.git*' {external_esw_src} {builder.config.workDir}",
            )
            builder.esw_path = os.path.join(builder.config.workDir, "embeddedsw")

        aie_src_path = os.path.join(builder.config.workDir, "aienginev2")
        if not builder.config.get("external_aienginev2"):
            clone(
                builder.config.git.aienginev2,
                aie_src_path,
                builder.workDir,
            )
        else:
            log.info(f"Using external aienginev2: {builder.config.external_aienginev2}")
            aie_src_path = builder.config.external_aienginev2

        lock_path = os.path.join(
            builder.esw_path, "XilinxProcessorIPLib/drivers", "aienginev2.lock"
        )
        lock = FileLock(lock_path)

        with lock:
            builder.runner.runcmd(
                f"rm -rf {builder.esw_path}/XilinxProcessorIPLib/drivers/aienginev2"
            )
            builder.runner.runcmd(
                f"ln -s {aie_src_path} {builder.esw_path}/XilinxProcessorIPLib/drivers/aienginev2"
            )
    return builder.build_app(config)


def baremetal_builder(config, proc):
    overrides(config, "std")
    overrides(config, proc)
    baremetal_runner(config)


def baremetal_cardano_builder(config):
    xsct.xsct_builder(config)
    baremetal_runner(config, setup=False)
    copyDirectory(config["elfs_path"], config["imagesDir"])
    assert pdi(config)


def check_cardano(config):
    if is_dir(f'{config["test_path"]}/cardano'):
        config["cardano_app"] = True
    else:
        config["cardano_app"] = False
