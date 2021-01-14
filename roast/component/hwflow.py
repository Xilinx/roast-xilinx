#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import re
import socket
import logging
from importlib import import_module
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.component.basebuild import Basebuild
from roast.providers.randomizer import Randomizer
from roast.providers.hwflow import HWFlowProvider

log = logging.getLogger(__name__)


class HwbuildRunner(Basebuild):
    def __init__(self, config):
        super().__init__(config)

    def configure(self):
        super().configure()
        self.vivado = self.config["VIVADO"]
        self.design_script = self.config["design_script"]
        self.design_path = self.workDir
        self.hwflow2_0 = False
        self.hwflow2_0_is_package = False
        self.hwflow_ver = self.config["hwflow_ver"]
        self.source = ""
        self.lsf = ""
        self.lsf_mode = self.config["lsf_mode"]
        self.lsf_options = self.config["lsf_options"]
        self.lsf_queue = self.config["lsf_queue"]
        self.lsf_osver = self.config["lsf_osver"]
        self.lsf_mem = self.config["lsf_mem"]
        self._setup()
        self._setup_vivado()

    def build(self):
        self.createhw()
        ret = self.deploy()
        return ret

    def _setup_vivado(self):
        self.env = os.environ.copy()
        self.env["PATH"] = get_dir_name(self.vivado) + ":" + self.env["PATH"]

    # Setup DesignEnv
    def _setup(self):
        if self.hwflow_ver == "2.0":
            self.hwflow2_0 = True
            if has_key(self.config, "hwflow_local"):
                self.source = {"file": self.config["hwflow_local"]}
                self._local_hw()
            else:
                # clone hwflow repo if hwflow package is not installed
                try:
                    import hwflow

                    copy_file(self.design_script, self.design_path)
                    self.hwflow2_0_is_package = True
                except ImportError:
                    self.source = {
                        "git": self.config["hwflow_url"],
                        "branch": self.config["hwflow_branch"],
                        "rev": self.config["hwflow_rev"],
                    }
                    self._clone_hw()

        else:
            if self.lsf_mode is True:
                self._setup_lsf_command()

            if has_key(self.config, "design_src"):
                self.source = self.config["design_src"]

                if has_key(self.source, "file"):
                    self._local_hw()
                elif has_key(self.source, "git"):
                    self._clone_hw()

        self.cwd = self.design_path

    # Setup LSF Command
    def _setup_lsf_command(self):
        site = socket.gethostname()[:3]
        if str(site).startswith("xhd"):
            bsub = self.config["lsf_xhdbsub"]
        elif str(site).startswith("xsj"):
            bsub = self.config["lsf_xsjbsub"]
        elif str(site).startswith("xir"):
            bsub = self.config["lsf_xirbsub"]
        else:
            bsub = self.config["lsf_xsjbsub"]

        bsub += (
            f" {self.lsf_options} -q {self.lsf_queue}"
            + f' -R "select[osver={self.lsf_osver}]"'
            + f' -R "rusage[mem={self.lsf_mem}]"'
        )
        self.lsf = bsub

    # Clone designs scripts from git repo.
    def _clone_hw(self):

        url = self.source["git"]
        branch = "master"  # Default branch to master
        if has_key(self.source, "branch"):
            branch = self.source["branch"]  # override user branch

        rev = ""  # Default rev value
        if has_key(self.source, "rev"):
            rev = self.source["rev"]

        design_name = url.split("/").pop().split(".git", 1)[0]
        if self.hwflow2_0:
            self.design_path = os.path.join(self.workDir, "hwflow2_0")
            git_clone(url, self.design_path, branch, rev)
            copy_file(self.design_script, self.design_path)
        else:
            self.design_path = os.path.join(self.workDir, design_name)
            git_clone(url, self.design_path, branch)
            if get_var(self.config, "design_relative_path"):
                self.design_path = (
                    f"{self.design_path}/{self.config.design_relative_path}"
                )
        os.chdir(self.design_path)

    # Set local design
    def _local_hw(self):
        hwfile = self.source["file"]
        design_name = hwfile.split("/").pop()
        if hwfile:
            if is_dir(hwfile) == True:
                self.design_path = f"{self.workDir}/{design_name}"
                copyDirectory(hwfile, self.design_path)
                os.chdir(self.design_path)
                if self.hwflow2_0:
                    copy_file(self.design_script, self.design_path)
            elif is_file(hwfile) == True:
                copy_file(hwfile, self.workDir)
            else:
                raise Exception(f"ERROR: {hwfile} does not exist")
        else:
            raise Exception("ERROR: FILE is empty")

    # Build design.
    def createhw(self):
        if self.hwflow2_0_is_package:
            design_script_dir = os.path.dirname(self.design_script)
            module_name, _ = os.path.splitext(os.path.basename(self.design_script))
            sys.path.append(f"{design_script_dir}")
            log.debug(f"Going to import module {module_name} ..")
            try:
                hwflow_module = import_module(module_name)
                if "main" in dir(hwflow_module):
                    # Add vivado to path, run vivado and remove vivado from path
                    _path_backup = os.environ.copy()["PATH"]
                    os.environ["PATH"] = self.env["PATH"]
                    hwflow_module.main()
                    os.environ["PATH"] = _path_backup
                    return True
                else:
                    log.debug(f"module {module_name} has no main() function")
            except ImportError:
                log.debug(f"Unable to import design script : {module_name}.py")

        if self.hwflow2_0:
            sys.path.append(f"{self.vivado}")
            self.design_module = get_base_name(self.design_script)
            runcmd_p(
                f"python3 {self.design_module}",
                log,
                env=self.env,
                cwd=self.cwd,
            )  # FIXME: This should call through current process
            return True

        elif is_file(self.design_script) == True:
            build_cmd = f"{self.vivado} -mode batch -source {self.design_script}"
            if has_key(self.config, "design_args"):
                build_cmd = f"{build_cmd} {self.config['design_args']}"

            if self.lsf_mode is True:
                build_cmd = f"{self.lsf} {build_cmd}"
            runcmd_p(build_cmd, log, env=self.env, cwd=self.cwd)
            return True

        else:
            log.error(f"{self.design_script} not exist in {self.workDir}")

        raise Exception("ERROR: Failed to build hwdesign")

    # Function to deploy design binaries.
    def deploy(self):

        # Copy artifacts to imagesDir
        if self.hwflow2_0 != True:
            log.info(f"Check design artifacts in {self.workDir}")
            ret = True

            if has_key(self.config, "artifacts"):
                artifacts = self.config["artifacts"]

                for image in artifacts:
                    image_file = find_file(image, self.workDir)
                    if image_file:
                        log.info(f"{image} exist in {self.workDir}")
                        copy_file(image_file, self.imagesDir)
                    else:
                        log.error(f"{image} not exist in {self.workDir}")
                        ret = False
        else:
            ret = self._deploy_hwflow2_0()
            if ret == False:
                raise Exception("ERROR: Failed to deploy artifacts")

        if has_key(self.config, "deploy_dir"):
            deploy_dir = self.config["deploy_dir"]
            if not is_dir(deploy_dir):
                mkdir(deploy_dir)
            copyDirectory(self.imagesDir, deploy_dir)

        return ret

    def _deploy_hwflow2_0(self):
        dir_list = get_dirs(os.getcwd())
        count = 0
        for name in dir_list:
            if re.search("hwflow_", name):
                design_name = name[7:]
                count += 1
        if count != 1:
            assert False, (
                f"ERROR: ${count} directories found" + " starting with hwflow_"
            )

        design_path = os.path.join(self.design_path, f"hwflow_{design_name}")
        xsa_path = os.path.join(design_path, "outputs", f"{design_name}.xsa")

        if is_file(xsa_path) == False:
            log.error("xsa not found in the design artifacts")
            return False
        if has_key(self.config, "artifacts"):
            artifacts = self.config["artifacts"]

            os.chdir(design_path)

            for image in artifacts:
                image = image.replace("@design", design_name)
                image_file = find_file(image, self.workDir)
                if image_file:
                    log.info(f"{image} exist in {self.workDir}")
                    if is_dir(image_file):
                        dir_name = os.path.basename(image)
                        copyDirectory(
                            image_file, os.path.join(self.imagesDir, dir_name)
                        )
                    else:
                        copy_file(image_file, self.imagesDir)
                else:
                    log.error(f"{image} not exist in {self.workDir}")

        return True


def hwrunner2(config):
    hw = HwbuildRunner(config)
    hw.configure()
    hw.createhw()
    ret = hw.deploy()
    return ret


# get test names from the directory where test module is present
def get_2_0_tests(file_path, sub_dir=None):
    dir_path = get_dir_name(get_abs_path(file_path))
    if sub_dir is not None:
        dir_path = os.path.join(dir_path, sub_dir)

    return get_files(dir_path, "py", basename=True)


# get testpath of the file
def get_design_path(config, script_name):
    test_path = config["test_path"]
    test_path = os.path.join(test_path, script_name + ".py")
    return test_path


class HWFlow(HwbuildRunner):
    def __init__(self, config):
        super().__init__(config)
        self.seed = config.get("seed", random.randrange(10000000000))
        self._randomizer = Randomizer(seed=self.seed)
        self._randomizer.add_provider(HWFlowProvider)
        self.randomizer = self._randomizer.hwflow_provider

    def build(self):
        design_script_dir = os.path.dirname(self.design_script)
        module_name, _ = os.path.splitext(os.path.basename(self.design_script))
        sys.path.append(design_script_dir)
        log.debug(f"Importing module {module_name} ..")
        try:
            hwflow_module = import_module(module_name)
            _path_backup = os.environ.copy()["PATH"]
            os.environ["PATH"] = self.env["PATH"]
            self.proj = hwflow_module.main()
            os.environ["PATH"] = _path_backup
        except ImportError:
            log.debug(f"Unable to import design script : {module_name}.py")

    def _setup(self):
        import hwflow

        copy_file(self.design_script, self.design_path)

    def get_random_parameter_values(self):
        random_parameter_values = {}
        for parameter in self.config.get("random_parameters", []):
            random_parameter_values[parameter] = self.randomizer.pick_parameter_value(
                parameter
            )
        return random_parameter_values

    def get_node_object(self, ip):
        nodes = self.proj.G.nodes(data=True)
        ip_list = ip.split(".")
        _top_ip = ip_list[0]
        node_obj = nodes[_top_ip]["node_obj"]
        for attr in ip_list[1:]:
            node_obj = getattr(node_obj, attr)
        return node_obj

    def get_width_object(self, obj):
        if obj.parent().type.val == "AXI_EXERCISER":
            if obj.direction.val == "input":
                return obj.parent().c_s_axi_data_width
            else:
                return obj.parent().c_m_axi_data_width
        elif obj.parent().type.val == "AXI_MONSTUB":
            return obj.parent().c_axi_data_width
        else:
            return None

    def get_object_name(self, obj):
        if hasattr(obj, "portname"):
            return obj.portname.val
        elif hasattr(obj, "name"):
            return obj.name.val
        else:
            return None

    def get_object_direction(self, obj, attr):
        if hasattr(obj, "direction"):
            return obj.direction.val
        elif attr in [
            "c_m_axi_data_width",
            "m_axi_mm2s_data_width",
            "m_axis_mm2s_tdata_width",
            "m_axi_s2mm_data_width",
        ]:
            return "output"
        elif attr == "c_s_axi_data_width":
            return "input"
        else:
            return None

    def get_node_connections(self, obj, direction):
        connections = []
        if direction == "output":
            for edge in self.proj.G.out_edges(nbunch=[obj.name.val], data=True):
                if (
                    edge[2]["edge_obj"].master_ref().portname.val
                    == obj.m_axi.portname.val
                ):
                    connections.append(edge[2]["edge_obj"].slave_ref())
        return connections

    def get_port_edge(self, obj=None):
        if "PORT" in obj.port_type.val:
            if obj.direction.val == "input":
                for edge in self.proj.G.out_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].master_ref().portname.val
                        == obj.portname.val
                        and edge[2]["edge_obj"].master_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        return edge
            else:
                for edge in self.proj.G.in_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].slave_ref().portname.val == obj.portname.val
                        and edge[2]["edge_obj"].slave_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        return edge
        else:
            if obj.direction.val == "input":
                for edge in self.proj.G.in_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].slave_ref().portname.val == obj.portname.val
                        and edge[2]["edge_obj"].slave_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        return edge
            else:
                for edge in self.proj.G.out_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].master_ref().portname.val
                        == obj.portname.val
                        and edge[2]["edge_obj"].master_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        return edge
        return None

    def get_port_connections(self, obj=None):
        connections = []
        if "PORT" in obj.port_type.val:
            if obj.direction.val == "input":
                for edge in self.proj.G.out_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].master_ref().portname.val
                        == obj.portname.val
                        and edge[2]["edge_obj"].master_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        connections.append(edge[2]["edge_obj"].slave_ref())

            else:
                for edge in self.proj.G.in_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].slave_ref().portname.val == obj.portname.val
                        and edge[2]["edge_obj"].slave_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        connections.append(edge[2]["edge_obj"].master_ref())
        else:
            if obj.direction.val == "input":
                for edge in self.proj.G.in_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].slave_ref().portname.val == obj.portname.val
                        and edge[2]["edge_obj"].slave_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        connections.append(edge[2]["edge_obj"].master_ref())
            else:
                for edge in self.proj.G.out_edges(
                    nbunch=[obj.parent().name.val], data=True
                ):
                    if (
                        edge[2]["edge_obj"].master_ref().portname.val
                        == obj.portname.val
                        and edge[2]["edge_obj"].master_ref().parent().name.val
                        == obj.parent().name.val
                    ):
                        connections.append(edge[2]["edge_obj"].slave_ref())
        return connections

    @staticmethod
    def set_bit(value, bit):
        return value | (1 << bit)

    @staticmethod
    def clear_bit(value, bit):
        return value & ~(1 << bit)
