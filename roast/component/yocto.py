#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.utils import *
from roast.component.basebuild import Basebuild
from roast.xexpect import Xexpect
import os
import logging

log = logging.getLogger(__name__)


class Yocto(Basebuild):
    def __init__(self, config, setup: bool = False):
        super().__init__(config, setup=setup)
        super().configure()
        self.repo_path = config.repo_path
        self.console = Xexpect(log=log, exit_nzero_ret=True)
        self.yocto_url = config.yocto_url
        self.yocto_branch = config.yocto_branch
        self.yocto_manifest_xml = config.yocto_manifest_xml
        self.repo_bundle_url = config.repo_bundle_url
        self.yocto_build_dir = os.path.join(self.workDir, "build")
        self.yocto_conf_dir = os.path.join(self.yocto_build_dir, "conf")

        """If there is no yocto.conf.TMPDIR defined in config then we are setting tmpdir
        to workdir/build/tmp and if user is running on nfsmount, then we will see the
        expected error from yocto."""
        self.yocto_tmp_dir = self.config["yocto.conf.TMPDIR"] = config.get(
            "yocto.conf.TMPDIR", os.path.join(self.yocto_build_dir, "tmp")
        )

        """If there is no yocto_ws_deploy_dir in config, then we are setting the default
        value to config['yocto.conf.TMPDIR']/deploy"""
        self.yocto_ws_deploy_dir = os.path.join(
            self.config["yocto.conf.TMPDIR"], "deploy"
        )
        if not self.repo_path:
            self.repo_path = "repo"

    def fetch(self):
        init_cmd = f"{self.repo_path} init -u {self.yocto_url} -b {self.yocto_branch} -m {self.yocto_manifest_xml}"
        if self.repo_bundle_url:
            init_cmd += f" --repo-url {self.repo_bundle_url}"
        self.console.runcmd(init_cmd)
        log.info("INFO: repo init -> DONE")

    def repo_sync(self, timeout=500):
        self.console.runcmd(f"{self.repo_path} sync -d -j 20", timeout=timeout)
        log.info("INFO: repo sync -> DONE")

    def repo_start(self):
        self.console.runcmd(f"{self.repo_path} start {self.yocto_branch} --all")
        log.info("INFO: repo start -> DONE")

    def repo_reset(self, timeout=500):
        self.console.runcmd(
            f"{self.repo_path} forall -c 'git reset --hard @{{u}}; git clean -fdx'",
            timeout=timeout,
        )
        log.info("INFO: repo reset -> DONE")

    def sdk_setup(self, setupfile=""):
        self.console.runcmd("pwd")
        if not setupfile:
            setupfile = "setupsdk"
        log.info(f"INFO: sourcing {setupfile}")
        if is_file(setupfile):
            self.console.runcmd(f"source {setupfile}")
        else:
            log.error("ERROR:Yocto setup failed.Check repo sync")
            assert False, "Setup for yocto failed, Check repo init/sync."

    def show_layers(self):
        # Returns the list of all the available layers in bblayers.conf

        self.console.runcmd(
            "bitbake-layers show-layers | awk '/^meta/{print $1}' ORS=' '", expected=" "
        )

        # Converts space separated strings into a python list and returns the list
        return self.console.output().split()

    def remove_layers(self, layers=set()):
        """Removes the mentioned layers from bblayers.conf file"""

        if not layers:
            log.info("Layers list passed in remove_layers API is empty.")
        else:
            # Get list of all the available layers
            layers_present = self.show_layers()
            # Remove redundancy if any from the given layer list.
            for entry in set(layers):
                """Checks if the mentioned layer is present in bblayers.conf. remove-layer
                returns error if the given layer is not present in bblayers.conf"""
                if entry in layers_present:
                    self.console.runcmd(f"bitbake-layers remove-layer {entry}")

    def add_layers(self, layers=set()):
        """Adds the mentioned layers in bblayers.conf file"""

        if not layers:
            log.info("Layers list passed in add_layers API is empty.")
        else:
            # Get list of all the available layers
            layers_present = self.show_layers()
            # Remove redundancy if any from the given layer list.
            for entry in set(layers):
                """bitbake-layers add-layer expects a path. get_base_name() extracts the
                layer name from the path and the layer is added if not already present"""
                if get_base_name(entry) not in layers_present:
                    self.console.runcmd(f"bitbake-layers add-layer {entry}")

    def reset_conf_file(self, conf_file="auto"):
        remove(os.path.join(self.yocto_conf_dir, f"{conf_file}.conf"))

    def set_conf_vals(self, conf_file="auto"):
        conf_file_path = os.path.join(self.yocto_conf_dir, f"{conf_file}.conf")
        for key in self.config["yocto.conf"].keys():
            value = self.config[f"yocto.conf.{key}"]
            newline = f'{key} = "{value}"'
            add_newline(conf_file_path, newline)
        for entries in self.config["yocto.exactconf"]:
            if "{{" in entries:
                entries = entries.format()
            add_newline(conf_file_path, entries)
        # Log the yocto settings done by user for better debugging
        log.info(f"yocto project config set to: {self.config['yocto']}")

    def image_builder(self, recipe_list, timeout=1000):
        """Runs the bitbake command"""

        # Convert the recipe string into a list if only one recipe is passed as a string
        recipes = [recipe_list] if isinstance(recipe_list, str) else recipe_list
        # Enables running of multiple recipes in sequence
        for recipe in recipes:
            self.console.runcmd(f"bitbake {recipe}", timeout=timeout)

    def deploy(self):
        """This Function deploys the generated yocto build images to specific location"""
        ret = True

        yocto_deploy_dir = self.config.get("yocto_deploy_dir", self.imagesDir)
        if not is_dir(yocto_deploy_dir):
            mkdir(yocto_deploy_dir)

        if self.config.get("yocto_ws_deploy_dir"):
            yocto_ws_deploy_dir = self.config.yocto_ws_deploy_dir
        else:
            yocto_ws_deploy_dir = self.yocto_ws_deploy_dir

        log.info(f"List of available artifacts: {os.listdir(yocto_ws_deploy_dir)}")

        if self.config.get("yocto_artifacts"):
            for image_list in self.config["yocto_artifacts"]:
                if isinstance(image_list, (tuple, list)):
                    image_name = image_list[0]
                    image = image_list[1]
                    image_file = find_file(image, yocto_ws_deploy_dir)
                    if image_file:
                        log.info(f"Artifact found: {image_file}")
                        image_file = get_original_path(image_file)
                        copy_data(image_file, f"{yocto_deploy_dir}/{image_name}")
                    else:
                        log.error(f"{image} does not exist in {yocto_ws_deploy_dir}")
                        ret = False
                elif isinstance(image_list, str):
                    image_files = find_files(image_list, yocto_ws_deploy_dir)
                    log.info(f"Artifacts found: {image_files}")
                    for file in image_files:
                        copy_data(file, f"{yocto_deploy_dir}/")
                    if not image_files:
                        log.error(
                            f"{image_list} does not exist in {yocto_ws_deploy_dir}"
                        )
                        ret = False
        else:
            copyDirectory(yocto_ws_deploy_dir, yocto_deploy_dir, symlinks=True)

        return ret


def yocto_build(
    config,
    reset_timeout=500,
    sync_timeout=500,
    setupfile="",
    recipe_name="petalinux-image-minimal",
    build_timeout=1000,
):

    yocto_builder = Yocto(config)

    yocto_builder.fetch()

    yocto_builder.repo_reset(timeout=reset_timeout)

    yocto_builder.repo_sync(timeout=sync_timeout)

    yocto_builder.repo_start()

    yocto_builder.sdk_setup(setupfile=setupfile)

    yocto_builder.reset_conf_file()

    yocto_builder.set_conf_vals()

    yocto_builder.image_builder(recipe=recipe_name, timeout=build_timeout)

    yocto_builder.deploy()

    return True
