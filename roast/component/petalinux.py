#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import re
import atexit
import shutil
import subprocess
from datetime import datetime
import logging
from typing import Optional
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.xexpect import Xexpect
from roast.component.basebuild import Basebuild

log = logging.getLogger(__name__)


class Petalinux(Basebuild):
    """This Petalinux class contains api's for all common petalinux options"""

    configs_dir = "project-spec/configs"
    meta_user = "project-spec/meta-user"
    recipes_apps = f"{meta_user}/recipes-apps"
    recipes_bsp = f"{meta_user}/recipes-bsp"
    project_config = f"{configs_dir}/config"
    rootfs_config = f"{configs_dir}/rootfs_config"
    user_rootfs_config = f"{meta_user}/conf/user-rootfsconfig"
    plnxbspconf_file = f"{meta_user}/conf/petalinuxbsp.conf"
    devicetree_dir = f"{recipes_bsp}/device-tree"
    fsbl_dir = f"{recipes_bsp}/fsbl"
    pmufw_dir = f"{recipes_bsp}/pmu-firmware"
    plm_dir = f"{recipes_bsp}/plm"
    psmfw_dir = f"{recipes_bsp}/psm-firmware"
    system_user_file = f"{devicetree_dir}/files/system-user.dtsi"
    kernel_dir = f"{meta_user}/recipes-kernel/linux/linux-xlnx"
    kernel_bbappend = f"{meta_user}/recipes-kernel/linux/linux-xlnx_%.bbappend"
    devicetree_append = f"{devicetree_dir}/device-tree.bbappend"
    fsbl_bbappend = f"{fsbl_dir}/fsbl-firmware_%.bbappend"
    atf_dir = f"{recipes_bsp}/arm-trusted-firmware"
    atf_bbappend = f"{atf_dir}/arm-trusted-firmware_%.bbappend"
    uboot_dir = f"{meta_user}/recipes-bsp/u-boot"
    uboot_bbappend = f"{uboot_dir}/u-boot-xlnx_%.bbappend"
    pmufw_bbappend = f"{pmufw_dir}/pmu-firmware_%.bbappend"
    plm_bbappend = f"{plm_dir}/plm-firmware_%.bbappend"
    psmfw_bbappend = f"{psmfw_dir}/psm-firmware_%.bbappend"
    openamp_dir = f"{meta_user}/recipes-openamp"
    libmetal_dir = openamp_dir
    openamp_bbappend = f"{openamp_dir}/open-amp/open-amp_%.bbappend"
    libmetal_bbappend = f"{openamp_dir}/libmetal/libmetal_%.bbappend"
    xen_dir = f"{meta_user}/recipes-extended/xen"
    xen_bbappend = f"{xen_dir}/xen_%.bbappend"
    recipesmm_dir = f"{meta_user}/recipes-multimedia/"
    gst_dir = f"{recipesmm_dir}/gstreamer/"
    vcu_dir = f"{recipesmm_dir}/vcu/"
    vcu_firmware_dir = f"{recipesmm_dir}/vcu/vcu-firmware"
    vcu_firmware_bbappend = f"{vcu_dir}/vcu-firmware.bbappend"
    vcu_omxil_dir = f"{recipesmm_dir}/vcu/libomxil-xlnx"
    vcu_omxil_bbappend = f"{vcu_dir}/libomxil-xlnx.bbappend"
    vcu_ctrlsw_dir = f"{recipesmm_dir}/vcu/libvcu-xlnx"
    vcu_ctrlsw_bbappend = f"{vcu_dir}/libvcu-xlnx.bbappend"
    vcu_modules_dir = f"{recipesmm_dir}/vcu/kernel-module-vcu"
    vcu_modules_bbappend = f"{vcu_dir}/kernel-module-vcu.bbappend"
    gstreamer_dir = f"{recipesmm_dir}/gstreamer/gstreamer1.0"
    gstreamer_bbappend = f"{gst_dir}/gstreamer1.0_%.bbappend"
    gst_plugins_bad_dir = f"{recipesmm_dir}/gstreamer/gstreamer1.0-plugins-bad"
    gst_plugins_bad_bbappend = f"{gst_dir}/gstreamer1.0-plugins-bad_%.bbappend"
    gst_plugins_base_dir = f"{recipesmm_dir}/gstreamer/gstreamer1.0-plugins-base"
    gst_plugins_base_bbappend = f"{gst_dir}/gstreamer1.0-plugins-base_%.bbappend"
    gst_plugins_good_dir = f"{recipesmm_dir}/gstreamer/gstreamer1.0-plugins-good"
    gst_plugins_good_bbappend = f"{gst_dir}/gstreamer1.0-plugins-good_%.bbappend"
    gst_omx_dir = f"{recipesmm_dir}/gstreamer/gstreamer1.0-omx"
    gst_omx_bbappend = f"{gst_dir}/gstreamer1.0-omx_%.bbappend"

    def __init__(self, config, setup: bool = True):
        super().__init__(config, setup)
        self.plnx_tool = config["PLNX_TOOL"]
        self.bsp_path = config["BSP_PATH"]
        self.plnx_pkg = None
        self.plnx_tmp = config["PLNX_TMP_PATH"]
        self.plnx_proj = config["plnx_proj"]

        self.workDir = config["workDir"]
        self.imagesDir = config["imagesDir"]
        self.wsDir = config["wsDir"]
        self.config["platform"] = config["platform"]

        self.proj_dir = f"{self.workDir}/{self.plnx_proj}"
        self.petalinux_images = f"{self.proj_dir}/images"
        self.qemu_boot = False
        # Acquire bash console.
        self.runner = Xexpect(log, exit_nzero_ret=True)
        atexit.register(self.__del__)
        myconfs = [
            "RECIPE_NAME",
            "RECIPE_NEW_NAME",
            "FETCHURI",
            "SOURCE_PATH",
            "RECIPE_DESTINATION",
            "IMAGE_RECIPE",
            "WORKSPACE_LAYERPATH",
            "EXISTING_RECIPENAME",
            "RECIPE_UPGRADE",
        ]
        for myconf in myconfs:
            if myconf in config:
                setattr(self, myconf.lower(), getattr(config, myconf))

    def source_tool(self, timeout: int = 120) -> None:
        """This Function source the petalinux tool.

        Parameters:
            PLNX_TOOL - by default set to petalinux daily_latest
        """
        if not is_file(self.plnx_tool):
            raise Exception(f"Error: ({self.plnx_tool}) is not a file")
        cmd = f"source {self.plnx_tool}"
        self.runner.runcmd(cmd=str(cmd), timeout=timeout)
        log.info(f"Petalinux Tool : {self.runner.runcmd(f'echo $PETALINUX')}")

    def create_project(self, timeout: int = 300) -> None:
        """This Function sources the creates petalinux project based on user configuration,

        Parameters:
           PLNX_TOOL : petalinux tool path
           platform  : versal, zynqMP, zynq, microblaze
           plnx_flow : BSP, template (by default BSP)
           BSP_PATH  : bsp path (default set to petalinux daily_latest)
           PLNX_BSP  : bsp name
           plnx_proj : project name
        """
        remove(f"{self.proj_dir}")

        self.source_tool()
        cmd = f"petalinux-create -t project "
        if self.config.get("plnx_flow") == "template":
            log.info("Using templete flow to create petalinux project...")
            cmd += f"--template {self.config['platform']}"
        else:
            log.info("Using bsp flow to create petalinux project...")
            self.plnx_bsp = self.config["PLNX_BSP"]
            self.plnx_bsp_path = get_original_path(f"{self.bsp_path}/{self.plnx_bsp}")
            if not is_file(self.plnx_bsp_path):
                log.error(f"Petalinux BSP {self.plnx_bsp_path} Not found")
                assert False, "Petalinux BSP Not found"
            cmd += f"-s {self.plnx_bsp_path} "

        if "plnx_proj" in self.config:
            cmd += f" -n {self.plnx_proj}"

        self.runner.runcmd(f"cd {self.workDir}")
        self.runner.runcmd(cmd=str(cmd), timeout=timeout)
        self.runner.runcmd(f"cd {self.plnx_proj}")
        os.chdir(self.proj_dir)
        if self.config.get("plnx_init_cmds"):
            self.runner.runcmd_list(self.config.plnx_init_cmds)

    def fetch_project(self):
        """This Function clones petalinux project from git,

        Parameters:
            PLNX_TOOL : petalinux tool path
            plnx_proj : project name
            bsp_src : bsp source
        >>> git.bsp.url : "https://gitenterprise.xilinx.com/bsp_src.git"
            git.bsp.branch : "master"
        """
        self.source_tool()
        if "git.bsp.url" in self.config:
            url = self.config.git.bsp.url
            if "git.bsp.branch" not in self.config:
                self.config.git.bsp.branch = "master"
            clone(
                self.config.git.bsp,
                self.proj_dir,
                recurse_submodules=self.config.git.bsp.recurse_submodules,
            )
            os.chdir(self.proj_dir)
            self.runner.runcmd(f"cd {self.proj_dir}")
        else:
            err_msg = "git.bsp.url not found in config"
            assert False, err_msg

    def create_apps(self, timeout: int = 300) -> None:
        """This Function creates user applications in petalinux project,

        Parameters:
            user_apps : it is dictionary
        >>> Usage:
            1. user_apps = { 'appname' : [ 'app files1', 'app file2' ] }
            2. user_apps = { 'appname' : [ 'app files' ],
                             'appname_bbfile' : 'userspecfic bbfile path'}
        """

        plnx_apps = self.config["user_apps"]
        if plnx_apps:
            for app_name, files in plnx_apps.items():
                app_name = app_name.lower()
                if "bbfile" not in app_name:
                    files = convert_list(files)
                    if self.config.get("plnx_flow") == "template":
                        create_apps_cmd = f"petalinux-create -t apps --template install -n {app_name.strip()} --enable"
                        self.runner.runcmd(cmd=str(create_apps_cmd), timeout=timeout)
                        remove_all_files(f"{self.recipes_apps}/{app_name}/files/")
                    else:
                        create_apps_cmd = (
                            f"petalinux-create -t apps -n {app_name.strip()} --enable"
                        )
                        self.runner.runcmd(cmd=str(create_apps_cmd), timeout=timeout)
                    for data in files:
                        data = parse_config(self.config, data)
                        if is_dir(data):
                            copyDirectory(
                                data,
                                f"{self.proj_dir}/{self.recipes_apps}/{app_name}/files/",
                            )
                        else:
                            copy_file(
                                data,
                                f"{self.proj_dir}/{self.recipes_apps}/{app_name}/files/",
                            )
            for app_name, files in plnx_apps.items():
                app_name = app_name.lower()
                if "bbfile" in app_name:
                    files = parse_config(self.config, files)
                    app_name = os.path.splitext(os.path.basename(files))[0]
                    copy_file(files, f"{self.proj_dir}/{self.recipes_apps}/{app_name}/")
        else:
            log.warning("No user apps to create ")

    def set_tmp_path(self):
        """This Function to set temp path for petalinux project

        Parameters:
            PLNX_TMP_PATH : Default it set to '/tmp/petalinux'
        """

        if self.plnx_tmp:
            tmp_dir = (
                self.plnx_proj + "-" + datetime.now().strftime("%Y.%m.%d-%H.%M.%S")
            )

            if os.getenv("JOB_NAME"):
                tmp_dir = f"{os.getenv('JOB_NAME')}/{tmp_dir}"

            self.plnx_tmp = os.path.join(self.plnx_tmp, tmp_dir)

            mkdir(self.plnx_tmp)
            os.chmod(self.plnx_tmp, 0o777)
            add_newline(
                f"{self.project_config}", f'CONFIG_TMP_DIR_LOCATION="{self.plnx_tmp}"'
            )

        if is_filesystem_nfs(self.proj_dir):
            self.plnx_tmp = self.get_tmp_path()

    def get_tmp_path(self):
        with open(f"{self.proj_dir}/{self.project_config}", "r") as read_obj:
            for line in read_obj:
                if "CONFIG_TMP_DIR_LOCATION" in line:
                    matchObj = re.search('CONFIG_TMP_DIR_LOCATION="(.*)"', line)
                    tmp_path = matchObj.group(1)
                    return tmp_path

    def silent_config(self, timeout: int = 600) -> None:
        """This Function apply the user configuration to petalinux project
        Parameter: plnx_config_component (optional)
        """

        plnx_silent_cmd = "yes | petalinux-config"
        if "plnx_config_component" in self.config:
            plnx_silent_cmd += f" -c {self.config['plnx_config_component']}"
        plnx_silent_cmd += " --silentconfig"

        self.runner.runcmd(cmd=str(plnx_silent_cmd), timeout=timeout)

    def get_hwdesign(self, timeout: int = 600) -> None:
        """This Function apply hardware design file(.xsa) on petalinux project

        Parameter:
            hw_design_path : .xsa file path
        """

        hw_design = get_original_path(self.config["hw_design_path"])
        hwdesign_cmd = (
            f"yes | petalinux-config --get-hw-description={hw_design} --silentconfig"
        )
        self.runner.runcmd(cmd=str(hwdesign_cmd), timeout=timeout)

    def plnx_build(self, timeout: int = 3600) -> None:
        """This Function runs petalinux build command on project
        Parameter: None
        """

        build_cmd = "petalinux-build"
        if self.config.get("plnx_build_timeout", ""):
            timeout = self.config.plnx_build_timeout

        self.runner.runcmd(cmd=str(build_cmd), timeout=timeout)

    def set_config(self):
        """This Function apply the user configs on petalinux project

        >>> Usage:
            plnx_configs = { rootfs :   [ 'CONFIG_xen=y',
                                          'CONFIG_open-amp_demo is not set' ],
                             project :  [ 'CONFIG_ROOTFS_INITRD=y' ],
                             kernel :   [ 'CONFIG_XILINX_ETHERNET=y'],
                             user-rootfs : ['CONFIG_kernel-module-hdmi'],
                             bspconf : ['IMAGE_INSTALL_append = "iperf3"']
                           }
        """

        component_map = {
            "user-rootfs": {"conf": f"{self.user_rootfs_config}"},
            "rootfs": {"conf": f"{self.rootfs_config}"},
            "project": {"conf": f"{self.project_config}"},
            "kernel": {
                "conf": f"{self.kernel_dir}/bsp.cfg",
                "conf_dir": f"{self.kernel_dir}",
                "bbappend": [
                    'FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"',
                    'SRC_URI += "file://bsp.cfg"',
                ],
            },
            "uboot": {
                "conf": f"{self.uboot_dir}/files/bsp.cfg",
                "conf_dir": f"{self.uboot_dir}",
                "bbappend": ['SRC_URI += "file://bsp.cfg"'],
            },
            "bspconf": {"conf": f"{self.plnxbspconf_file}"},
        }

        components = ("plm", "pmufw", "fsbl", "psmfw")

        for key, value in self.config["plnx_configs"].items():
            value = convert_list(value)
            if key in component_map:
                if "conf_dir" in component_map[key].keys():
                    mkdir(str(component_map[key]["conf_dir"]))
                if "bbappend" in component_map[key].keys():
                    append_list = convert_list(component_map[key]["bbappend"])
                    for val in append_list:
                        add_newline(getattr(self, f"{key}_bbappend"), str(val))
                for itr in value:
                    itr = parse_config(self.config, itr)
                    add_newline(str(component_map[key]["conf"]), str(itr))
            elif key in components:
                mkdir(getattr(self, f"{key}_dir"))
                for itr in value:
                    itr = parse_config(self.config, itr)
                    add_newline(getattr(self, f"{key}_bbappend"), str(itr))
            else:
                err_msg = f"Invalid arg {key} in plnx_configs"
                assert False, err_msg

    def apply_patch(self):
        components = ("atf", "pmufw", "fsbl", "uboot")
        for key, value in self.config["apply_patches"].items():
            value = convert_list(value)
            component_dir = f"{key}_dir"
            mycomponent_dir = getattr(self, component_dir)
            append_file = f"{key}_bbappend"
            myappend_file = getattr(self, append_file)
            mkdir(mycomponent_dir)
            if "kernel" in key:
                add_newline(f"{self.kernel_bbappend}", 'SRC_URI += "file://bsp.cfg"')
                add_newline(
                    myappend_file,
                    'FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"',
                )
            if key in components:
                add_newline(
                    myappend_file,
                    'FILESEXTRAPATHS_prepend := "${THISDIR}:"',
                )
            else:
                add_newline(
                    myappend_file,
                    'FILESEXTRAPATHS_prepend := "${THISDIR}/${PN}:"',
                )
            for itr in value:
                if itr.endswith(".patch"):
                    if is_file(f"{itr}"):
                        copy_file(f"{itr}", mycomponent_dir)
                        itr = os.path.basename(f"{itr}")
                        add_newline(myappend_file, f'SRC_URI += "file://{itr}"')
                    else:
                        copy_file(f"{self.config['workDir']}/{itr}", mycomponent_dir)
                        add_newline(myappend_file, f'SRC_URI += "file://{itr}"')
                else:
                    log.info("Invalid patch...")

    def apply_external_component(self):
        """This function adds support to apply external src on petalinux project
            for kernel, uboot, atf, fsbl, xen, openamp components

        Parameters:
            url - component git url
            externalsrc - local src path
            srcrev - commid id/tag
            branch - git branch
            checksum - source checksum
        >>> Usage:
                plnx.component.uboot.url = "<git url>"
                plnx.component.uboot.branch = "master"
                plnx.component.uboot.srcrev = "12223434222"
                plnx.component.uboot.checksum = "<checksum>"
                plnx.component.xen.externalsrc= "<external source path>"
                plnx.component.openamp.url= "<source url>"
        """

        def _external_repo_setup(self, key):
            if key == "openamp":
                key = "open-amp"
            component = re.sub("-", "", key)
            comp = f"{component}_bbappend"
            comp_dir = f"{component}_dir"
            mycomp_dir = getattr(self, comp_dir)
            mkdir(f"{mycomp_dir}/{key}")
            bbappend = getattr(self, comp)
            return bbappend

        def _component_map(self):
            component_map = {}
            component_map["atf"] = "ARM__TRUSTED__FIRMWARE"
            component_map["uboot"] = "U__BOOT"
            component_map["kernel"] = "LINUX__KERNEL"
            return component_map

        for key, value in self.config.plnx.component.items():
            if key in ["kernel", "uboot", "atf"]:
                component_map = _component_map(self)
                if value["url"]:
                    add_newline(
                        f"{self.project_config}",
                        f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_REMOTE=y",
                    )
                    add_newline(
                        f"{self.project_config}",
                        f"# CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_EXT__LOCAL__SRC is not set",
                    )
                    add_newline(
                        f"{self.project_config}",
                        f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_REMOTE_DOWNLOAD_PATH=\"{value['url']};protocol=https\"",
                    )
                    if value["srcrev"]:
                        add_newline(
                            f"{self.project_config}",
                            f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_REMOTE_REFERENCE=\"{value['srcrev']}\"",
                        )
                    else:
                        add_newline(
                            f"{self.project_config}",
                            f'CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_REMOTE_REFERENCE="${{AUTOREV}}"',
                        )
                    if value["branch"]:
                        add_newline(
                            f"{self.project_config}",
                            f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_REMOTE_BRANCH=\"{value['branch']}\"",
                        )
                    if value["checksum"]:
                        add_newline(
                            f"{self.project_config}",
                            f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_LIC_FILES_CHKSUM_REMOTE=\"{value['checksum']}\"",
                        )
                else:
                    if value["externalsrc"]:
                        add_newline(
                            f"{self.project_config}",
                            f"# CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_REMOTE is not set",
                        )
                        add_newline(
                            f"{self.project_config}",
                            f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_EXT__LOCAL__SRC=y",
                        )
                        add_newline(
                            f"{self.project_config}",
                            f"CONFIG_SUBSYSTEM_COMPONENT_{component_map[key]}_NAME_EXT__LOCAL__SRC_PATH=\"{value['externalsrc']}\"",
                        )
            else:
                bbappend = _external_repo_setup(self, key)
                if value["externalsrc"]:
                    repo_name = get_base_name(value["externalsrc"])
                    self.runner.runcmd(
                        cmd=f"rsync -av --exclude '.git*' {value['externalsrc']} {self.workDir}",
                        timeout=120,
                    )
                    add_newline(bbappend, f"inherit externalsrc")
                    add_newline(bbappend, f'EXTERNALSRC = "{self.workDir}/{repo_name}"')
                    add_newline(
                        bbappend, f'EXTERNALSRC_BUILD = "{self.workDir}/{repo_name}"'
                    )
                    if value["checksum"]:
                        add_newline(
                            bbappend,
                            f"LIC_FILES_CHKSUM = \"file://license.txt;md5={value['checksum']}\"",
                        )
                elif value["url"]:
                    if value["checksum"]:
                        add_newline(
                            bbappend,
                            f"LIC_FILES_CHKSUM = \"file://license.txt;md5={value['checksum']}\"",
                        )
                    add_newline(bbappend, f"REPO = \"{value['url']};protocol=https\"")
                    if value["srcrev"]:
                        if value["srcrev"] == "AUTOREV":
                            add_newline(bbappend, 'SRCREV = "{AUTOREV}"')
                        else:
                            add_newline(bbappend, f"SRCREV = \"{value['srcrev']}\"")
                    if value["branch"]:
                        add_newline(bbappend, f"BRANCH = \"{value['branch']}\"")
                    # Add build dependency using this var, for the component being built
                    if value["depends"]:
                        add_newline(bbappend, f"DEPENDS += \"{value['depends']}\"")
                else:
                    log.info(
                        "Invalid external component src option.... using default petalinux sources"
                    )

    def update_dtsi_file(self):
        """This function adds user dtsi file to petalinux project

        Parameter:
            plnx_user_dtsi_files : user .dtsi file

        >>> Usage:
            plnx_user_dtsi_files = ['<path to dtsi file>']
        """

        mkdir(self.devicetree_dir)
        if "plnx_user_dtsi_files" in self.config:
            dt_files = convert_list(self.config["plnx_user_dtsi_files"])
            for file in dt_files:
                copy_file(file, f"{self.devicetree_dir}/files/")
                dt_file = os.path.basename(file)
                if dt_file.endswith(".dtsi"):
                    add_newline(f"{self.system_user_file}", f'/include/ "{dt_file}"')
                    add_newline(
                        f"{self.devicetree_append}", f'SRC_URI += "file://{dt_file}"'
                    )
                else:
                    log.error("Invalid dtsi input")

    def link_dtsi_file(self):
        """This function softlink system-user.dtsi file with user provided dtsi file

        Parameter:
           plnx_user_dtsi_file : user .dtsi file

        >>> Usage:
            plnx_user_dtsi_file = 'path to user dtsi file'
        """
        if "plnx_user_dtsi_file" in self.config:
            plnx_user_dtsi_file = self.config["plnx_user_dtsi_file"]
            system_dt_file = os.path.basename(self.system_user_file)
            user_dt_file = os.path.basename(plnx_user_dtsi_file)
            if os.path.isabs(plnx_user_dtsi_file):
                if is_file(plnx_user_dtsi_file):
                    copy_file(plnx_user_dtsi_file, f"{self.devicetree_dir}/files/")
                else:
                    err_msg = "ERROR: No {plnx_user_dtsi_file} exists"
                    assert False, err_msg
            os.chdir(f"{self.devicetree_dir}/files/")
            symlink(system_dt_file, user_dt_file)
            os.chdir(self.proj_dir)

    def pack_bsp(self, timeout: int = 300) -> None:
        """This Function packages the petalinux project into BSP"""

        self.plnx_pkg = self.config["plnx_pkg"]
        if not self.plnx_pkg.split():
            self.plnx_pkg = self.plnx_bsp

        pack_cmd = f"petalinux-package --bsp -p ./ -o {self.workDir}/{self.plnx_pkg}"
        self.runner.runcmd(cmd=str(pack_cmd), timeout=timeout)

    def run_user_script(self, timeout: int = 600) -> None:
        """This Function can be useful to run any user script after petalinux project creation.
        Parameters:
            user_script : supports .sh and .py
        >>> Usage:
            user_script = { "file_name" : "example.sh",
                            "args" : "<script args if any>",
                            "expected" : "<any script to match to know
                                        the script execution complete>"
            }

        """

        userSuite = self.config["user_script"]
        script = userSuite["file_name"]
        args = userSuite["args"]
        expected = userSuite["expected"]

        if is_file(f"{self.workDir}/{script}") == True:
            if script.endswith(".sh"):
                config_cmd = f"sh {self.workDir}/{script} {args}"
            elif script.endswith(".py"):
                config_cmd = f"python {self.workDir}/{script} {args}"
            else:
                log.error(f"{script} not supported to execute")
        else:
            raise Exception(f"ERROR: {self.workDir}/{script} not exist")
        self.runner.runcmd(cmd=str(config_cmd), expected=expected, timeout=timeout)

    def plnx_package_boot(self, timeout: int = 600) -> None:
        """This Function creates BOOT.BIN"""

        if self.config["platform"].strip().lower() == "zynqmp":
            plnx_bin_cmd = "petalinux-package --boot %s %s %s %s" % (
                "--fsbl images/linux/zynqmp_fsbl.elf",
                "--u-boot images/linux/u-boot.elf",
                "--pmufw images/linux/pmufw.elf",
                "--fpga images/linux/system.bit --force",
            )
        elif self.config["platform"].strip().lower() == "zynq":
            plnx_bin_cmd = "petalinux-package --boot %s %s %s" % (
                "--fsbl images/linux/zynq_fsbl.elf",
                "--u-boot images/linux/u-boot.elf",
                "--fpga images/linux/system.bit --force",
            )
        elif self.config["platform"].strip().lower() == "versal":
            plnx_bin_cmd = "petalinux-package --boot --force --u-boot"
        elif self.config["platform"].strip().lower() == "microblaze":
            plnx_bin_cmd = ""
        else:
            log.error(f"{(self.config['platform'])} not supported")
            raise Exception(f"Error: {(self.config['platform'])} not supported")
        self.runner.runcmd(cmd=str(plnx_bin_cmd), timeout=timeout)

    def build_sdk(self, timeout: int = 3600) -> None:
        """This Function runs petalinux sdk command on project"""

        build_sdk_cmd = "petalinux-build --sdk"
        self.runner.runcmd(cmd=str(build_sdk_cmd), timeout=timeout)

    def extract_sdk(self, timeout: int = 3600) -> None:
        """This Function extracts the sdk on project"""
        extract_sdk_cmd = "petalinux-package --sysroot"
        self.runner.runcmd(cmd=str(extract_sdk_cmd), timeout=timeout)

    # Fix me
    def plnx_package_wic(self, wic_args=None, timeout=600):
        """This Function can be useful to generate wic image to prepare sd card.
        Parameters:
            wic_args : None (or) --bootfiles "BOOT.BIN boot.scr system.dtb image.ub"
        """
        wic_cmd = "petalinux-package --wic"
        if wic_args:
            wic_cmd += f" {wic_args}"
        self.runner.runcmd(cmd=str(wic_cmd), timeout=timeout)

    def deploy(self):
        """This Function deploy the generated petalinux build images to specfic location
        Parameters:
            plnx_artifacts - to copy any specific files
            deploy_dir : to copy images to specific location
        >>> Usage:
            plnx_artifacts = ['image.ub', 'BOOT.BIN', 'Image', 'system.xsa' ]
            deploy_dir = "<path>"
        """
        ret = True
        if "deploy_dir" in self.config:
            deploy_dir = self.config["deploy_dir"]
            if not is_dir(deploy_dir):
                mkdir(deploy_dir)

            log.info(f"Checking petalinux artifacts in {self.proj_dir}")
            if "plnx_artifacts" in self.config:
                for image in self.config["plnx_artifacts"]:
                    image_file = find_file(image, f"{self.proj_dir}/images/linux")
                    if image_file:
                        if is_file(image_file):
                            copy_file(image_file, deploy_dir)
                        elif is_dir(image_file):
                            copyDirectory(
                                image_file, f"{deploy_dir}/{image}", symlinks=True
                            )
                    else:
                        log.error(f"{image} does not exist in {self.workDir}")
                        ret = False

        copyDirectory(f"{self.proj_dir}/images/linux", self.imagesDir, symlinks=True)
        return ret

    def deploy_bsp(self):
        """This Function deploys the petalinux bsp to specified location

        Parameter:
            deploy_dir : <path>
        """

        deploy_dir = self.config["deploy_dir"]
        if deploy_dir:
            if is_dir(deploy_dir) == False:
                mkdir(deploy_dir)
            else:
                remove(deploy_dir)
                mkdir(deploy_dir)
            log.info(f"Copying plnx packed bsp to {deploy_dir}")
            shutil.copy(f"{self.workDir}/{self.plnx_pkg}", deploy_dir)
        shutil.copy(f"{self.workDir}/{self.plnx_pkg}", self.imagesDir)

    def _run_boot(
        self,
        cmd: str,
        proj_path: Optional[str] = None,
        hwserver: Optional[str] = None,
        bitfile: Optional[str] = None,
        rootfs: Optional[str] = None,
    ) -> None:
        """This function create petalinux boot command"""

        if proj_path:
            self.proj_dir = proj_path
        if not bitfile:
            bitfile = f"{self.proj_dir}/pre-built/linux/images/system.bit"
        if bitfile.endswith(".bit"):
            if self.config.get("platform") != "versal":
                if self.config.get("plnx_no_rev_check"):
                    cmd += f' --after-connect "fpga -no-revision-check {bitfile}"'
                else:
                    cmd += f" --bitstream {bitfile}"
        if rootfs:
            cmd += f" --rootfs {rootfs}"
        if hwserver:
            cmd += f" --hw_server-url {hwserver}:3121"

        if not is_dir(self.proj_dir):
            log.error(f"Petalinux Project Directory {self.proj_dir} not found")
            assert False, "Petalinux project directory not found"

        self.runner.runcmd(f"cd {self.proj_dir}")
        self.runner.runcmd(cmd=str(cmd), timeout=3600)

    def _run_qemu_boot(self, cmd, proj_path=None, qemu_args=None, rootfs=None):
        """This function create petalinux qemu boot command"""
        if proj_path:
            self.proj_dir = proj_path
        if rootfs:
            cmd += f" --rootfs {rootfs}"
        if qemu_args:
            cmd += f" {qemu_args}"

        if not is_dir(self.proj_dir):
            log.error(f"Petalinux Project Directory {self.proj_dir} not found")
            assert False, "Petalinux project directory not found"
        self.runner.runcmd(f"cd {self.proj_dir}")
        self.qemu_boot = True
        self.runner.sendline(cmd=str(cmd))

    def plnx_boot(
        self,
        boottype=None,
        proj_path=None,
        hwserver=None,
        bitfile=None,
        qemu_args=None,
        rootfs=None,
    ):
        if boottype not in ("prebuilt 2", "prebuilt 3", "kernel", "uboot"):
            raise Exception(
                """Invalid petalinux boot type selected
            support types are: prebuilt 2, prebuilt 3, kernel, uboot"""
            )

        if hwserver:
            cmd = f"petalinux-boot --jtag -v --{boottype}"
            self._run_boot(cmd, proj_path, hwserver, bitfile, rootfs)
        else:
            cmd = f"petalinux-boot --qemu --{boottype}"
            self._run_qemu_boot(cmd, proj_path, qemu_args, rootfs)

    def __del__(self):
        """This function deletes the petalinux project created under TEMP path.

        Parameters:
            PLNX_TMP_PATH : tmp path to to build petalinux project
            skip_clean_temp : to skip temp clean
        >>> skip_clean_temp = true

        """
        if self.config.get("skip_clean_temp"):
            log.info("Skipped petaliux project temp clean...")
        else:
            if self.plnx_tmp:
                log.info(
                    f"Petaliunx project temp clean successful on path : {self.plnx_tmp} ..."
                )
                remove(self.plnx_tmp)

        if self.qemu_boot:
            self.runner.sendcontrol("a")
            self.runner.sendline("x")

    def devtool(self, operation, timeout=12000):
        """This function performs petalinux-devtool options"""
        self.source_tool()
        self.create_project()
        if operation == "add":
            self.runner.runcmd(
                cmd=f" petalinux-devtool {operation} {self.recipe_name}  {self.fetchuri}",
                timeout=2000,
            )
        elif operation == "modify":
            self.runner.runcmd(
                cmd=f" petalinux-devtool {operation} {self.existing_recipename} ",
                timeout=1000,
            )
        elif operation == "upgrade":
            self.runner.runcmd(
                cmd=f" petalinux-devtool {operation} {self.recipe_upgrade}",
                timeout=2000,
            )
        elif operation in ("status", "export"):
            self.runner.runcmd_list(
                cmd_list=[
                    f"petalinux-devtool add {self.recipe_name} {self.fetchuri}",
                    f"petalinux-devtool {operation}",
                ],
                timeout=600,
            )
        elif operation in (
            "latest-version",
            "check-upgrade-status",
            "search",
            "build",
            "find-recipe",
            "configure-help",
            "update-recipe",
            "configure",
        ):
            self.runner.runcmd_list(
                cmd_list=[
                    f"petalinux-devtool add {self.recipe_name} {self.fetchuri}",
                    f"petalinux-devtool {operation} {self.recipe_name}",
                ],
                timeout=2000,
            )
        elif operation == "rename":
            self.runner.runcmd_list(
                cmd_list=[
                    f"petalinux-devtool add {self.recipe_name} {self.fetchuri}",
                    f"petalinux-devtool {operation} {self.recipe_name}  {self.recipe_new_name}",
                    f"petalinux-devtool search {self.recipe_new_name}",
                ],
                timeout=2000,
            )
        elif operation == "reset":
            self.runner.runcmd_list(
                cmd_list=[
                    f"petalinux-devtool add {self.recipe_name} {self.fetchuri}",
                    f" petalinux-devtool {operation}  {self.recipe_name} ",
                    f"cd {self.source_path} && rm -rf {self.recipe_name}",
                    f"cd && cd {self.workDir}/{self.plnx_proj}",
                ],
                timeout=2000,
            )
        elif operation == "finish":
            self.runner.runcmd_list(
                cmd_list=[
                    f"petalinux-devtool add {self.recipe_name} {self.fetchuri}",
                    f" petalinux-devtool {operation}  {self.recipe_name} {self.workDir}/{self.plnx_proj}/{self.recipe_destination}",
                    f"cd {self.source_path} && rm -rf {self.recipe_name}",
                    f"petalinux-devtool find-recipe {self.recipe_name}",
                    f"cd && cd {self.workDir}/{self.plnx_proj}",
                ],
                timeout=2000,
            )
        elif operation == "build-image":
            self.runner.runcmd(
                cmd=f" petalinux-devtool {operation} {self.image_recipe}", timeout=2000
            )
        elif operation == "create-workspace":
            self.runner.runcmd(
                cmd=f" petalinux-devtool {operation} {self.workspace_layerpath}",
                timeout=600,
            )
        elif operation == "import":
            self.plnx_bsp = self.config["PLNX_BSP"]
            self.runner.runcmd_list(
                cmd_list=[
                    f"petalinux-devtool add {self.recipe_name} {self.fetchuri}",
                    f" petalinux-devtool export && cd ..",
                    f"yes | petalinux-create -t project -s  {self.bsp_path}{self.plnx_bsp}",
                    f"cd {self.plnx_proj} && petalinux-devtool {operation} {self.workDir}/{self.plnx_proj}.old/build/workspace-export-*tar.gz -o",
                ],
                timeout=600,
            )
        elif operation == "extract":
            self.runner.runcmd(
                cmd=f"petalinux-devtool {operation} {self.existing_recipename} {self.workspace_layerpath}",
                timeout=2000,
            )
        elif operation == "--help":
            self.runner.runcmd(cmd=f"petalinux-devtool {operation} ")


def petalinux_build(config):

    plnx_builder = Petalinux(config)
    plnx_builder.configure()
    # create project
    plnx_builder.create_project()

    # set tmp path
    plnx_builder.set_tmp_path()

    # apply external srcs
    if "plnx" in config:
        plnx_builder.apply_external_component()

    # apply hardware design
    if "hw_design_path" in config:
        plnx_builder.get_hwdesign()

    # set project configs
    if "plnx_configs" in config:
        plnx_builder.set_config()

    if "apply_patches" in config:
        plnx_builder.apply_patch()

    # set device tree
    if "plnx_user_dtsi_files" in config:
        plnx_builder.update_dtsi_file()
    if "plnx_user_dtsi_file" in config:
        plnx_builder.link_dtsi_file()

    # App creation
    if "user_apps" in config:
        plnx_builder.silent_config()
        plnx_builder.create_apps()

    # silent config
    plnx_builder.silent_config()

    # petalinux build
    plnx_builder.plnx_build()

    # build & extract sdk
    if config.get("build_sdk"):
        plnx_builder.build_sdk()
        plnx_builder.extract_sdk()

    # create BOOT.bin
    if "plnx_package_boot" in config:
        if config["plnx_package_boot"]:
            plnx_builder.plnx_package_boot()

    # deploy images
    plnx_builder.deploy()

    return True


def petalinux_boot(
    config,
    boottype="prebuilt 3",
    proj_path=None,
    hwserver=None,
    bitfile=None,
    qemu_args=None,
    rootfs=None,
    setup=False,
):
    plnx_runner = Petalinux(config, setup=setup)
    plnx_runner.configure()
    plnx_runner.source_tool()
    ret = True

    if boottype in ("prebuilt 2", "prebuilt 3", "kernel", "uboot"):
        if boottype in ("prebuilt 2", "prebuilt 3"):
            if not is_dir(proj_path) and not is_dir(plnx_runner.proj_dir):
                plnx_runner.create_project()
        plnx_runner.plnx_boot(boottype, proj_path, hwserver, bitfile, qemu_args, rootfs)
    else:
        log.info(
            """Invalid petalinux boot type selected
        support types are: prebuilt 2, prebuilt 3, kernel, uboot"""
        )
        ret = False
    return ret
