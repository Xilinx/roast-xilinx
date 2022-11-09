#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import re
import time
import logging
from roast.xexpect import Xexpect
from roast.component.basebuild import Basebuild
from roast.utils import *  # pylint: disable=unused-wildcard-import


class BaseCrossCompile(Basebuild):
    def __init__(self, config, app_name, setup=True):

        super().__init__(config, setup=setup)
        self.console = Xexpect(log, exit_nzero_ret=True)

        self._setup_args()
        self.app_name = app_name

    def _copy_src(self):
        src = (
            f"{self.config['ROOT']}/"
            + "/".join(self.config["test_param_path_list"][0:3])
            + "/src"
        )
        dest = os.path.join(self.config["workDir"], "src")
        if is_dir(src):
            copyDirectory(src, dest)

    def _setup_args(self):
        if "CARDANO_ROOT" in self.config:
            self.cardano_root = self.config["CARDANO_ROOT"]
        self.lib_file = self.config["lib_file"]

    def pre_configure(self):
        super().configure()
        self.srcDir = os.path.join(self.workDir, "src")
        self._copy_src()
        self.compiler_flags = ""
        self.linker_flags = ""
        self.include_dir = []
        self.lib_dir = []

    def configure(self):

        VITIS_DIR = self.config.vitisPath
        XLNX_LICENSE = self.config["XILINXD_LICENSE_FILE"]
        cmdlist = [
            f"export XILINXD_LICENSE_FILE={XLNX_LICENSE}",
            f"export VITIS_DIR={VITIS_DIR}",
            f"source {self.config.vitisPath}/settings64.sh",
            f"cd {self.workDir}",
        ]
        self.console.runcmd_list(cmdlist)
        if "AIETOOLS_ROOT" in self.config:
            AIETOOLS_ROOT = self.config.AIETOOLS_ROOT
            cmdlist = [
                f"export AIETOOLS_ROOT={AIETOOLS_ROOT}",
                f"export PATH={VITIS_DIR}/bin:$PATH",
            ]
            self.console.runcmd_list(cmdlist)

        # Add user include paths
        if "user_include_path" in self.config:
            for path in self.config.user_include_path:
                path = parse_config(self.config, path)
                self.include_dir += [path]

        # Add user compiler flags
        if "user_compiler_flags" in self.config:
            self.compiler_flags += self.config.user_compiler_flags

        # Add Cardano Source path to include
        if self.config.get("cardano_app"):
            self.include_dir.append(f"{self.config.cardano_base_ws_dir}/images/src")

        self.include = ["-I" + dir for dir in self.include_dir]
        self.include = " ".join(self.include)

        # Add user library paths
        if "user_lib_path" in self.config:
            for path in self.config.user_lib_path:
                path = parse_config(self.config, path)
                self.lib_dir += [path]

        self.lib = ["-L" + dir for dir in self.lib_dir]
        self.lib = " ".join(self.lib)

        # Add user linker flags
        if self.config.get("user_linker_flags"):
            self.linker_flags += self.config.user_linker_flags

    def deploy(self, src_file_name):
        if "deploy_artifacts" in self.config:
            for artifact in self.config["deploy_artifacts"]:
                artifact_path = os.path.join(self.workDir, artifact)
                if is_dir(artifact_path):
                    copyDirectory(artifact_path, os.path.join(self.imagesDir, artifact))
                else:
                    copy_match_files(
                        self.workDir, self.imagesDir, artifact, follow_src_dir=True
                    )

            cmd_list = [
                f"cd {self.imagesDir}",
                f"tar cvfJ deploy_artifacts.tar.xz ./*",
            ]
            self.console.runcmd_list(cmd_list)

        aie_path = os.path.join(self.workDir, "aie_control." + self.app_name["exe"])
        if is_file(f'{self.workDir}/{src_file_name}.{self.app_name["exe"]}'):
            copy_file(
                f'{self.workDir}/{src_file_name}.{self.app_name["exe"]}',
                self.imagesDir,
            )
            log.info(f"{self.app_name['exe']} created successfully")
        else:
            raise Exception(f"Error: {self.app_name['exe']} creation failed")


class BaremetalCrossCompile(BaseCrossCompile):
    def compile(self, src_file_name):
        compile_cmd = [
            self.app_name["compiler"][self.config["param"]],
            self.compiler_flags,
            self.app_name["compile_flags"],
            f'-MT"{self.srcDir}/{src_file_name}.cpp"',
            self.app_name["procname"][self.config["param"]],
            f'-MF"{self.srcDir}/{src_file_name}.d"',
            f'-MT"{self.srcDir}/{src_file_name}.o"',
            "-o",
            f'"{self.srcDir}/{src_file_name}.o"',
            f"{self.include}",
            f"{self.srcDir}/{src_file_name}.cpp",
        ]

        if self.config.get("exe_file_format") == "eabi":
            compile_cmd += [self.config["abi_cmd"]]

        cmd = " ".join(compile_cmd)
        self.console.runcmd(cmd, err_msg="Baremetal Compilation Failed")
        time.sleep(5)

    def link(self, src_file_name):

        link_cmd = [
            self.app_name["compiler"][self.config["param"]],
            " -v",
            self.app_name["procname"][self.config["param"]],
            f"{self.lib}",
            "-o",
            f"{self.workDir}/{src_file_name}.{self.app_name['exe']}",
            f"{self.srcDir}/{src_file_name}.o",
        ]

        if self.config.get("exe_file_format") == "eabi":
            link_cmd += [self.config["abi_cmd"]]

        link_cmd += [self.app_name["link_flags"] + self.linker_flags]

        cmd = " ".join(link_cmd)
        self.console.runcmd(cmd, err_msg="Baremetal Linking Failed")
        time.sleep(5)


class LinuxCrossCompile(BaseCrossCompile):
    def pre_configure_linux(self, base_ws_dir=None, sysroot_providers=None):
        # initialize empty sysroot
        self.sysroot_opts = ""
        # Generate the app_sysroot.
        app_sysroot = os.path.join(self.config.workDir, "app_sysroot")
        mkdir(app_sysroot)
        # Copy sysroot_providers
        for app in sysroot_providers:
            provider_path = os.path.join(
                base_ws_dir, *app, "images", "sysroot-provider"
            )
            # raise error if sysroot-provider doesnt exist
            is_dir(provider_path, False)
            # Copy the contents of provider into app_sysroot preserving the sysmlinks
            copyDirectory(provider_path, app_sysroot, True)

        # Add its include and lib paths
        self.include_dir += [os.path.join(app_sysroot, "include")]
        self.lib_dir += [os.path.join(app_sysroot, "lib")]

    def compile(self, src_file_name):

        link_cmd = [
            self.app_name["compiler"][self.config["param"]],
            self.sysroot_opts,
            self.compiler_flags,
            self.app_name["compile_flags"],
            self.include,
            self.app_name["procname"][self.config["param"]],
            f"{self.lib}",
            "-o",
            f"{self.workDir}/{src_file_name}.{self.app_name['exe']}",
            f"{self.srcDir}/{src_file_name}.cpp",
        ]

        if self.config.get("cardano_app"):
            cardano_linux_src = self.config.get("cardano_linux_src")
            if cardano_linux_src:
                link_cmd.append(f"{self.workDir}/{cardano_linux_src}")
            else:
                link_cmd.append(
                    f"{self.config.cardano_base_ws_dir}/images/src/{self.config['cardano_src']}.cpp"
                )

        link_cmd.append(self.app_name["link_flags"])
        link_cmd.append(self.linker_flags)

        cmd = " ".join(link_cmd)
        self.console.runcmd(cmd, err_msg="Linux Cross Compilation Failed")
        time.sleep(5)


def baremetal_runner(config, setup=True):
    app_name = {
        "compiler": {"a72": "aarch64-none-elf-g++", "r5": "armr5-none-eabi-g++"},
        "compile_flags": "-Wall -O0 -g3 -c -fmessage-length=0 -D__AIEBAREMTL__ -DPS_ENABLE_AIE -MMD -MP",
        "procname": {"a72": "-mcpu=cortex-a72", "r5": "-mcpu=cortex-r5"},
        "link_flags": "-ladf_api -Wl,--start-group,-lxil,-lgcc,-lc,-lstdc++,--end-group",
        "exe": "elf",
    }
    bm = BaremetalCrossCompile(config, app_name, setup)
    bm.pre_configure()
    # Baremetal application path for include and lib

    # When CIPS3.0 designs are used bsp path is not created based on xsct proc name,
    # Instead its being truncated to match the name which was generated
    # while CIPS 2.1 is used which of length 3 for all the versal platform components.
    if len(bm.config["xsct_proc_name"]) >= 3 and re.search(
        "cips", bm.config["xsct_proc_name"], re.IGNORECASE
    ):
        proc_list = bm.config["xsct_proc_name"].split("_")
        proc_list = proc_list[-3:]
        bm.config["xsct_proc_name"] = "_".join(proc_list)

    bm.component_ws_dir = os.path.join(
        bm.config.component_ws_dir, "images", bm.config["xsct_proc_name"]
    )
    bm.include_dir += [f"{bm.component_ws_dir}/include"]
    bm.ldscript = os.path.join(bm.config.component_ws_dir, "images", "lscript.ld")
    bm.lib_dir += [
        f"{bm.component_ws_dir}/lib",
        f"{config.AIETOOLS_ROOT}/lib/{config.lib_file}.o/",
    ]

    if config["HEAP_SIZE"]:
        bm.linker_flags += f" -Xlinker --defsym=_HEAP_SIZE={config['HEAP_SIZE']} "
    bm.linker_flags += f" -Wl,-T -Wl,{bm.ldscript}"

    bm.configure()
    bm.compile("aie_control")
    bm.link("aie_control")
    bm.deploy("aie_control")


def linux_runner(config, setup=True):
    app_name = {
        "compiler": {"linux": "aarch64-linux-gnu-g++"},
        "compile_flags": "-DPS_ENABLE_AIE -DXAIE_DEBUG -DUSE_XRT",
        "procname": {"linux": ""},
        "link_flags": "-lstdc++ -lxaiengine ",
        "exe": "run",
    }
    src_file = "aie_control"

    bm = LinuxCrossCompile(config, app_name, setup)
    bm.pre_configure()
    bm.pre_configure_linux(
        base_ws_dir=config.base_ws_dir,
        sysroot_providers=config.get("sysroot_providers"),
    )

    if config.get("cardano_app"):
        # Get cardano application built base dir
        bm.config.cardano_base_ws_dir = os.path.join(
            config.buildDir, "/".join(config.test_path_list), "cardano"
        )
        config["src_path"] = f"{config.cardano_base_ws_dir}/images"
        # check for the presence of dir and error as "build case failed"
        assert is_dir(
            os.path.join(config.cardano_base_ws_dir, "images")
        ), "Cardano Build case failed"
        copyDirectory(f"{config['src_path']}", bm.workDir)

        # Add adf header files and libs
        bm.include_dir.append(f"{config.AIETOOLS_ROOT}/include")
        bm.lib_dir += [f"{config.AIETOOLS_ROOT}/lib/{config.lib_file}.o/"]

        # Leverage XRT source code for cross compiling.
        src_file = "aie_control_xrt"
        if not is_file(f"{bm.srcDir}/{src_file}.cpp"):
            err_msg = "Cardano build test Failed"
            log.error(err_msg)
            raise Exception(err_msg)

    if config.get("xrt_app") or config.get("cardano_app"):
        # Add sysroot if defined in config to linking flags
        sysroot = config.get("XRT_SYSROOT")
        if sysroot:
            bm.sysroot_opts = f"--sysroot {sysroot}"
            bm.include_dir.append(f"{sysroot}/usr/include/xrt")

    bm.configure()
    bm.compile(src_file)
    bm.deploy(src_file)
    # Return the instance to leverage in self tests.
    return bm
