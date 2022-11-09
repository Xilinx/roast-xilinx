#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import logging
import os
import inspect
import glob
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.component.basebuild import Basebuild
from roast.xexpect import Xexpect


log = logging.getLogger(__name__)


class BuildComponent(Basebuild):
    def __init__(self, config):
        super().__init__(config)
        super().configure()
        self.component = config["component"]
        self.config = config

    def _setup(self):
        reset(self.wsDir)
        mkdir(self.workDir)
        mkdir(self.imagesDir)

    def build_xsct_app(self):
        print("Building %s" % self.component)
        elf_file = "%s/%s/Debug/%s.elf" % (self.workDir, self.component, self.component)
        # check for build_comp_sub_dir
        if self.config["external_embeddedsw"]:
            eswrepoPath = self.config["external_embeddedsw"]
        else:
            eswrepoPath = self.workDir + "git/"
            # FIXME: Use python module
            cmd = "git clone --reference %s/%s %s -b %s %s" % (
                self.config["gitReferenceUrl"],
                self.config["embeddedswReference"],
                self.config["embeddedswUrl"],
                self.config["embeddedswBranch"],
                eswrepoPath,
            )
            log.debug(f"cmd: {cmd}")
            runcmd(cmd, FileAdapter(log))
        copy_file(
            self.config["testXsa"], os.path.join(self.workDir, "design_1_wrapper.xsa")
        )

        # FIXME:move this to yaml

        procName = "psv_pmc_0"
        template = "versal " + self.config["component"].upper()
        if self.config["component"] == "psm":
            template += " Firmware"
            procName = "psv_psm_0"

        # FIXME: add as dictionary.
        # Donot hardcode xsa name
        app_cmd = "%s %s/build_app.tcl -pname %s " % (
            f"{self.config['vitisPath']}/bin/xsct",
            self.config["scriptsTclDir"],
            self.config["component"],
        )
        app_cmd += "-processor %s -osname standalone " % (procName)
        app_cmd += "-xsa %s/design_1_wrapper.xsa -ws %s " % (self.workDir, self.workDir)
        app_cmd += "-rp %s -app '%s'" % (eswrepoPath, template)
        runcmd(app_cmd, log)
        if is_file(elf_file):
            copy_file(elf_file, os.path.join(self.imagesDir, self.component + ".elf"))
            return True
        else:
            return False


def build(config) -> bool:
    # Fix logic to take defxsa if empty
    design = config["subtest"]
    testXsa = os.path.join(config["designs"][design], design + ".xsa")
    config["testXsa"] = testXsa

    bc = BuildComponent(config)
    return bc.build_xsct_app()


class BuildOsl(Basebuild):
    def __init__(self, config):
        super().__init__(config)
        super().configure()

        self.component = config["component"]
        self.config = config

        self.src_path = None
        self.build_path = f'{config["workDir"]}/{self.component}-build/'
        self.console = Xexpect(log, exit_nzero_ret=True)
        self._setup(self.component)

    def _setup(self, component):
        self.src_reference = self.config.get(f"git.{component}.reference")
        self.external_src = self.config.get(f"external_{component}")
        self.arch = self.config[f"{component}_arch"]
        self.compiler = self.config[f"{component}_compiler"]

        if f"{component}_defconfig" in self.config:
            self.defconfig = self.config[f"{component}_defconfig"]
        else:
            self.defconfig = None

        if f"{component}_devicetree" in self.config:
            self.console.runcmd(
                f"export DEVICE_TREE={self.config[f'{component}_devicetree']}"
            )

        self.console.runcmd(f"source {self.config['vitisPath']}/settings64.sh")
        if "sysroot_env" in self.config:
            self.console.runcmd(f"source {self.config['sysroot_env']}")
        if "sysroot_tool" in self.config:
            self.console.runcmd(f"export PATH={self.config['sysroot_tool']}:$PATH")
        self.console.runcmd(f"export ARCH={self.arch}")
        self.console.runcmd(f"export CROSS_COMPILE={self.compiler}")
        if "local_version" in self.config:
            self.console.runcmd(f"export LOCALVERSION={self.config.local_version}")
        mkdir(self.build_path)

        # export default env
        if f"{component}_env" in self.config:
            for env_var, value in self.config[f"{component}_env"].items():
                self.console.runcmd(f"export {env_var}={value}")

    def setup_src(self):
        if not self.external_src:
            self.console.runcmd(f"cd {self.config['workDir']}")

            if self.src_reference:
                clone(
                    self.config.git[f"{self.component}"],
                    f"{self.config['workDir']}/{self.component}",
                    workDir=self.config["workDir"],
                    reference=self.src_reference,
                )
            else:
                clone(
                    self.config.git[f"{self.component}"],
                    f"{self.config['workDir']}/{self.component}",
                    workDir=self.config["workDir"],
                )
                if not self.config.git[self.component]["patches"]:
                    """This Functionality apply the user configs for kernel, uboot, rootfs

                    >>> Usage:
                        kernel_configs = ['CONFIG_XILINX_ETHERNET=y']
                        rootfs_configs = ['CONFIG_xen=y', 'CONFIG_DRM=y']
                        uboot_configs = ['CONFIG_SYS_TEXT_BASE=0x10080001']
                    """
                    if self.component in ["uboot", "kernel", "rootfs"]:
                        if f"{self.component}_configs" in self.config:
                            conf_path = os.path.join(
                                self.config["workDir"], self.component
                            )
                            conf_file = find_file(self.defconfig, conf_path)
                            for item in self.config[f"{self.component}_configs"]:
                                add_newline(conf_file, item)

            self.src_path = f"{self.config['workDir']}/{self.component}/"
        else:
            if self.component not in [
                "kernel",
                "kernel_allmodconfig",
                "uboot",
                "rootfs",
            ]:
                rsync(self.console, self.external_src, self.config["workDir"])
                self.src_path = (
                    f"{self.config['workDir']}/{get_base_name(self.external_src)}"
                )
            else:
                self.src_path = self.external_src

    def configure(self):
        # configure the component
        if self.component == "kernel" or self.component == "rootfs":
            mkfile(f"{self.src_path}/.scmversion")
        if self.defconfig:
            cmd = f"make -C {self.src_path} {self.defconfig} O={self.build_path}"
            self.console.runcmd(cmd)

    def compile(self):
        extra_flags = ""
        if f"{self.component}_compile_flags" in self.config:
            extra_flags = f'{self.config[f"{self.component}_compile_flags"]}'
        if not self.config["outoftreebuild"]:
            self.build_path = self.src_path
        cmd = f'make -j {self.config["parallel_make"]} -C {self.src_path} O={self.build_path} {extra_flags}'
        self.console.runcmd(cmd, timeout=3600)

    def deploy(self):
        mkdir(self.config["deploy_artifacts"])
        for image in self.config[f"{self.component}_artifacts"]:
            image = parse_config(self.config, image)
            copy_file(
                os.path.join(self.build_path, image), self.config["deploy_artifacts"]
            )

    def generate_fit_dtb(self):
        self.console.runcmd(f"cd {self.build_path}")
        self.console.runcmd("type fdtoverlay", err_msg="fdtoverlay: not found")
        DTB_DIR = "arch/arm/dts"

        # Define dtbo_commands in tcrepo conf.py to generate dtb based on dtbo
        # Example:
        # dtbo_commands = ["fdtoverlay -o zynqmp-sm-k26-xcl2gc-ed-revA-sck-kv-g-revA.dtb -i zynqmp-sm-k26-revA.dtb zynqmp-sck-kv-g-revA.dtbo"]
        if "dtbo_commands" in self.config:
            self.console.runcmd(f"cd {self.build_path}/{DTB_DIR}")
            self.console.runcmd_list(self.config["dtbo_commands"])
            self.console.runcmd(f"cd {self.build_path}")
        else:
            err_msg = "ERROR: dtbo_commands not defined in config!"
            log.error(err_msg)
            raise Exception(err_msg)

        # Create u-boot fit image tree source (.its) file
        DT_HEADER = """
/*
 * This is a generated file.
 */
/dts-v1/;

/ {
	description = "DT Blob Creation";

	images {
"""
        DT_UBOOT = """
		fdt_1 {
			description = "zynqmp-smk-k26-revA";
			data = /incbin/("arch/arm/dts/zynqmp-smk-k26-revA.dtb");
			type = "flat_dt";
			arch = "arm64";
			compression = "none";
			hash {
				algo = "md5";
			};
		};

"""
        DT_NODE = """
		fdt_%d {
			description = "%s";
			data = /incbin/("%s");
			type = "flat_dt";
			arch = "arm64";
			compression = "none";
			hash {
				algo = "md5";
			};
		};

"""
        DT_UBOOT_CONFIG = """
	configurations {
	    default = "config_1";

		config_1 {
			description = "zynqmp-smk-k26-revA";
			fdt = "fdt_1";
		};
"""
        DT_CONFIG_NODE = """
		config_%d {
			description = "%s";
			fdt = "fdt_%d";
		};
"""
        DT_IMAGES_NODE_END = """	};

"""
        DT_END = "};"

        with open(f"{self.build_path}/uboot_fit.its", mode="w") as fit_its:
            fit_its.write(DT_HEADER)
            fit_its.write(DT_UBOOT)
            cnt = 2
            for dtb in glob.glob(f"{self.build_path}/{DTB_DIR}/*.dtb"):
                dtname = os.path.basename(dtb)
                dtb_path = f"{DTB_DIR}/{dtname}"
                fit_its.write(DT_NODE % (cnt, dtname, dtb_path))
                cnt = cnt + 1

            fit_its.write(DT_IMAGES_NODE_END)
            fit_its.write(DT_UBOOT_CONFIG)
            cnt = 2
            for dtb in glob.glob(f"{self.build_path}/{DTB_DIR}/*.dtb"):
                dtname = os.path.basename(dtb)
                fit_its.write(DT_CONFIG_NODE % (cnt, dtname, cnt))
                cnt = cnt + 1
            fit_its.write(DT_IMAGES_NODE_END)
            fit_its.write(DT_END)

        self.console.runcmd(f"./tools/mkimage -E -f uboot_fit.its -B 0x8 fit-dtb.blob")
        mkdir(self.config["deploy_artifacts"])
        copy_file(
            os.path.join(self.build_path, "fit-dtb.blob"),
            f"{self.config['deploy_artifacts']}",
        )


class BuildDtb(BuildOsl):
    def __init__(self, config, variant=None, board=None):
        super().__init__(config)
        self.board = board
        self.variant = variant

    def compile(self):
        extra_flags = ""
        if f"{self.component}_compile_flags" in self.config:
            extra_flags = f'{self.config[f"{self.component}_compile_flags"]}'

        if self.config[f"{self.component}_buildtype"] == "dtg":
            import roast.component.osl

            tcl_dir = os.path.dirname(inspect.getsourcefile(roast.component.osl))
            self.tcl = os.path.join(tcl_dir, "generate_dts.tcl")
            self.repo = os.path.join(self.config["workDir"], self.component)
            self.design = self.config[f"{self.component}_design"]
            cmd = f'unset DISPLAY && {self.config["vitisPath"]}/bin/xsct {self.tcl} {self.design} {self.repo} {self.build_path} {self.config[f"{self.component}_dtg"]}'
        else:
            cmd = f"make dtbs -C {self.src_path} O={self.build_path} {extra_flags}"
        self.console.runcmd(cmd, timeout=1500)
        self.generate_dtb()

    def generate_dtb(self):
        if self.config[f"{self.component}_buildtype"] == "dtg":
            self.dts_path = os.path.join(
                self.build_path, self.config[f"{self.component}_dtg"]
            )
            self.console.runcmd(f"cd {self.dts_path}_dts")

            if self.config["external_dtsi"]:
                dtsi_file = os.path.join(
                    f"{self.config['dtsi_basepath']}", f"{self.config['external_dtsi']}"
                )
                copy_file(dtsi_file, f"{self.dts_path}_dts")
                add_newline(
                    f"{self.dts_path}_dts/system-top.dts",
                    f"#include \"{self.config['external_dtsi']}\"",
                )
            self.console.runcmd(
                f"cpp -Iinclude -E -P -x assembler-with-cpp system-top.dts | dtc -I dts -O dtb -o {self.config['system_dtb']}"
            )


class BuildRootfsModule(BuildOsl):
    def __init__(self, config, variant=None, board=None):
        super().__init__(config)
        self.board = board
        self.variant = variant
        config["variant"] = variant

    def compile(self):
        super().compile()
        cmdlist = [f"make modules -C {self.src_path} O={self.build_path}", "sync"]
        self.console.runcmd_list(cmdlist, timeout=3600)
        mkdir(self.config["linux_module"])
        cmdlist = [
            f"make modules_install INSTALL_MOD_PATH={self.config['linux_module']} -C {self.src_path} O={self.build_path}",
            "sync",
        ]
        self.console.runcmd_list(cmdlist, timeout=3600)
        self.generate_rootfs()

    def generate_rootfs(self):
        self.src_rootfs_path = os.path.join(self.config["rootfs_path"], self.variant)
        self.src_rootfs_file = get_files(self.src_rootfs_path, extension="rootfs.cpio")[
            0
        ]
        self.src_rootfs = os.path.join(self.src_rootfs_path, self.src_rootfs_file)
        self.dest_rootfs = os.path.join(self.config["imagesDir"], self.src_rootfs_file)
        self.console.runcmd(
            "type fakeroot", err_msg="fakeroot not installed on machine"
        )
        self.console.runcmd(
            "fakeroot", expected=self.console.prompt, wait_for_prompt=False
        )
        self.console.runcmd("whoami", expected="root")
        self.console.runcmd(
            "bash --norc | cat", expected="bash-", wait_for_prompt=False
        )
        self.console.runcmd(
            r"PS1='\u@\H:\t:\w\$ '", expected=self.console.prompt, wait_for_prompt=False
        )
        self.console._setup_init()
        self.console.runcmd(f"cd {self.config['imagesDir']}")
        cmdlist = [f"cpio -idmv --no-absolute-filenames < {self.src_rootfs}", "sync"]
        self.console.runcmd_list(cmdlist, timeout=600)
        remove(f"{self.config['imagesDir']}/lib/modules", silent_discard=False)
        os.unlink(glob.glob(f"{self.config['linux_module']}/lib/modules/*/source")[0])
        os.unlink(glob.glob(f"{self.config['linux_module']}/lib/modules/*/build")[0])
        copyDirectory(
            f"{self.config['linux_module']}/lib/modules",
            f"{self.config['imagesDir']}/lib/modules",
        )
        self.console.runcmd(
            "find . -type f -print0 | xargs -0 -n 1 ls -l | grep '\-rwsr' | \
             grep '\/bin\/\|\/sbin\/' | awk '{print $9}' | xargs -r chmod 755"
        )
        self.console.runcmd("find . > ../module.txt", timeout=600)
        cmdlist = [
            f"cpio --quiet -H newc -o < ../module.txt -O {self.dest_rootfs}",
            "sync",
        ]
        self.console.runcmd_list(cmdlist, timeout=600)
        self.console.runcmd(
            f"gzip {self.dest_rootfs} && mkimage -A {self.arch} -T ramdisk -C gzip \
                    -d {self.dest_rootfs}.gz {self.dest_rootfs}.gz.u-boot"
        )
        copy_file(
            f"{self.dest_rootfs}.gz.u-boot",
            f"{self.config['deploy_artifacts']}/rootfs.cpio.gz.u-boot",
        )
