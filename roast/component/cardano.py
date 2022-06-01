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

    def pre_configure(self):
        super().configure()
        self.srcDir = os.path.join(self.workDir, "src")
        self.cdoDir = os.path.join(self.workDir, "Work/ps/cdo")
        XLNX_LICENSE = self.config["XILINXD_LICENSE_FILE"]
        self.console.runcmd(f"export XILINXD_LICENSE_FILE={XLNX_LICENSE}")

    def set_aie_tool(self):
        # CI use case, build with custom cardano tool
        if self.config.get("external_cardano_src"):
            AIETOOLS_ROOT = os.path.join(
                self.config.get("external_cardano_src"), "prep/rdi/aietools"
            )
        else:
            AIETOOLS_ROOT = self.config.AIETOOLS_ROOT

        # Source cardano tool
        self.console.runcmd(f"export AIETOOLS_ROOT={AIETOOLS_ROOT}")
        self.console.runcmd(f"export XILINX_VITIS_AIETOOLS={AIETOOLS_ROOT}")
        # self.console.runcmd(f"source {AIETOOLS_ROOT}/scripts/aietools_env.sh")
        self.AIETOOLS_ROOT = AIETOOLS_ROOT

    def set_vitis_tool(self):
        self.pre_configure()
        VITIS_DIR = self.config.vitisPath
        version_dotless = self.config.version.replace(".", "")
        base_platform = f"{self.config.BASE_PLATFORM_NAME}_{version_dotless}0_{self.config.BASE_PLATFORM_VERSION_EXTENSION}"
        self.PFM_XPFM = os.path.join(
            self.config.PLATFORMS_PATH, base_platform, f"{base_platform}.xpfm"
        )
        cmdlist = [
            f"export VITIS_DIR={VITIS_DIR}",
            f"export PFM_XPFM={self.PFM_XPFM}",
        ]
        self.console.runcmd_list(cmdlist)

    def compile_cardano_app(self):

        self.console.runcmd(f"cd {self.workDir}")
        # compile cardano and generate cdo
        compile_cmd = [
            f"{self.AIETOOLS_ROOT}/bin/aiecompiler -v",
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
            f"{self.config.vitisPath}/bin/v++ -s -p -t hw",
            f"--platform {self.PFM_XPFM}",
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
            copyDirectory(f"{self.workDir}/src", f"{self.imagesDir}/src")
            self.xclbin = get_files(self.workDir, extension="xclbin")
            for xclbin in self.xclbin:
                copy_file(f"{self.workDir}/{xclbin}", self.imagesDir)

            copyDirectory(f"{self.workDir}/Work", f"{self.imagesDir}/Work")

            ret = True
        except Exception as err:
            log.error(err)
        return ret

    def simulate_cardano_app(self):
        """API to simulate cardano applications.
        Users can specify cardano tool or custom cardano tool
        """

        self.console.runcmd(f"cd {self.workDir}")

        if self.config.get("generate_input_data") and self.config.get("generate_src"):
            gen_cmd = [
                f"{self.AIETOOLS_ROOT}/tps/lnx64/gcc/bin/g++",
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
            f"{self.AIETOOLS_ROOT}/bin/aiesimulator --pkg-dir={self.workDir}/Work",
            timeout=timeout,
            err_msg="Cardano app Simulation Failed",
        )

    def incremental_build(self):
        """Build cardano tool incrementally"""
        # This is only applicable in CI scenarios.
        if self.config.get("external_aiert_src") and self.config.get(
            "external_cardano_src"
        ):
            # Get aie driver path
            aie_driver_path = os.path.join(
                self.config.get("external_aiert_src"), "driver"
            )
            cardano_src_path = self.config.get("external_cardano_src")

            lock_path = os.path.join(
                get_abs_path(cardano_src_path),
                "src/products/cardano/",
                "incremental_build.lock",
            )
            incremental_build_log = os.path.join(
                cardano_src_path, "logs/incremetal_build.log"
            )

            lock = FileLock(lock_path)
            with lock:
                build_number = os.getenv("BUILD_NUMBER")
                # This if consition make sures driver compilation only once for a build
                if not check_if_string_in_file(
                    incremental_build_log,
                    build_number,
                ):
                    # Build driver inside cardano
                    self.console.runcmd(
                        f"sh {cardano_src_path}/incremental_build.sh {aie_driver_path}",
                        expected="Incremental Build SUCCESSFUL",
                        expected_failures=["Incremental Build FAILED"],
                        timeout=3000,
                    )
                else:
                    if check_if_string_in_file(
                        incremental_build_log,
                        "Incremental Build FAILED",
                    ):
                        raise Exception("ERROR: Incremental Build FAILED")


def cardano_builder(config):
    btc = Cardano(config, setup=True)
    btc.pre_configure()
    btc.incremental_build()
    btc.set_aie_tool()
    btc.set_vitis_tool()
    btc.compile_cardano_app()
    btc.gen_xclbin()
    assert btc.copy_images(), "ERROR: Build Cardano Failed!"


def cardano_simulator(config):
    btc = Cardano(config, setup=False)
    btc.pre_configure()
    btc.set_aie_tool()
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


def get_aienginev2_repo(config, console, aie_src_path, rsync_path=None):
    if not config.get("external_aienginev2"):
        clone(
            config.git.aienginev2,
            aie_src_path,
            config.workDir,
        )
    else:
        log.info(f"Using external aienginev2: {config.external_aienginev2}")
        if rsync_path:
            rsync(console, config.external_aienginev2, rsync_path)
            aie_src_path = os.path.join(rsync_path, "aienginev2")
        else:
            aie_src_path = config.external_aienginev2
    return aie_src_path


def get_aiert_repo(console, git_params=None, external_src=None, dest_path=None):

    if not dest_path:
        raise ValueError(f"destination path cannot be empty")

    # Copy the contents into aiert directory
    dest_path = os.path.join(dest_path, "aiert")

    if external_src:
        # Remove trialing space
        external_src.rstrip("/")
        # Copy external source into workdir under component dir
        console.runcmd(
            f"rsync -aqv --exclude '.git*' {external_src}/ {dest_path}", timeout=120
        )
    else:
        # Clone the repository into destination path
        clone(git_params, dest_path)

    return dest_path


def update_aienginev2_repo(config, console, esw_path, aie_src_path):
    if config.get("external_embeddedsw"):
        external_esw_src = get_abs_path(config.external_embeddedsw)
        rsync(console, external_esw_src, config.workDir)
        esw_path = os.path.join(config.workDir, "embeddedsw")

    lock_path = os.path.join(
        esw_path, "XilinxProcessorIPLib/drivers", "aienginev2.lock"
    )
    lock = FileLock(lock_path)
    with lock:
        console.runcmd(f"rm -rf {esw_path}/XilinxProcessorIPLib/drivers/aienginev2")
        console.runcmd(
            f"ln -s {aie_src_path} {esw_path}/XilinxProcessorIPLib/drivers/aienginev2"
        )
    return esw_path


def baremetal_lib(config, proc, setup=True):

    overrides(config, "std")
    overrides(config, proc)
    repo_path = ""

    builder = xsct.AppBuilder(config, setup=setup)

    if builder.config.get("baremetal_lib_component") == "aienginev2":
        aie_src_path = os.path.join(config.workDir, "aienginev2")
        aie_src_path = get_aienginev2_repo(
            builder.config, builder.console, aie_src_path
        )
        repo_path = update_aienginev2_repo(
            builder.config, builder.console, builder.esw_path, aie_src_path
        )
    elif builder.config.get("baremetal_lib_component") == "aiert":
        git_params = builder.config.get("git.aiert")
        external_src = builder.config.get("external_aiert_src")
        aiert_path = get_aiert_repo(
            builder.console, git_params, external_src, config.workDir
        )
        repo_path = aiert_path

    args = builder.parser(config)
    if repo_path:
        args["rp"] = repo_path
    builder.set_user_args(args)

    if builder.config.get("xsct_outDir", ""):
        mkdir(builder.config.xsct_outDir)

    ret = builder.build_app(config)
    if ret:
        if len(builder.config["xsct_proc_name"]) >= 3 and re.search(
            "cips", builder.config["xsct_proc_name"], re.IGNORECASE
        ):
            proc_list = builder.config["xsct_proc_name"].split("_")
            proc_list = proc_list[-3:]
            builder.config["xsct_proc_name"] = "_".join(proc_list)

        component_ws_dir = os.path.join(
            builder.config["workDir"],
            builder.config["component"],
            builder.config["xsct_platform_name"],
            builder.config["xsct_proc_name"],
            f"{builder.config['component']}_bsp",
            "bsp",
            builder.config["xsct_proc_name"],
        )

        ldscript = (
            f"{builder.config['workDir']}/{builder.config['component']}/"
            + f"{builder.config['component']}/src/lscript.ld"
        )
        copyDirectory(
            component_ws_dir,
            f"{builder.config['imagesDir']}/{builder.config['xsct_proc_name']}",
        )
        copy_file(ldscript, builder.config["imagesDir"])

        # Validate repo
        if repo_path:
            xsct_dest_path = os.path.join(
                builder.config.imagesDir, builder.config.xsct_proc_name, "libsrc"
            )
            # Validate aie driver
            driver_src_path = os.path.join(repo_path, "driver", "src")
            # Validate aiefal repo
            fal_src_path = os.path.join(repo_path, "fal", "src")
            # Compare the sources specified against the generated bsp
            cmds = [
                f"diff -qr -x *.o {driver_src_path} {xsct_dest_path}/aienginev2_*/src",
                f"diff -qr -x *.o {fal_src_path} {xsct_dest_path}/aiefal_*/src",
            ]
            builder.console.runcmd_list(cmds)

        return ret
    else:
        return ret


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
