#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.utils import *
from roast.component.basebuild import Basebuild
from roast.xexpect import Xexpect
import logging

log = logging.getLogger(__name__)


class Yocto(Basebuild):
    def __init__(self, config, setup: bool = False):
        super().__init__(config, setup=config.yocto_reset)
        super().configure()
        self.repo_path = config.repo_path
        self.console = Xexpect(log=log, exit_nzero_ret=True)
        self.yocto_url = config.yocto_url
        self.yocto_branch = config.yocto_branch
        self.yocto_manifest_xml = config.yocto_manifest_xml
        self.repo_bundle_url = config.repo_bundle_url
        self.workdir = config.workDir
        self.imagesdir = config.imagesDir
        self.deploy_dir = f"{config['yocto.conf.TMPDIR']}/deploy"
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

    def reset_conf_file(self):
        remove(f"{self.workdir}/build/conf/auto.conf")

    def set_conf_vals(self):
        for key in self.config["yocto.conf"].keys():
            value = self.config[f"yocto.conf.{key}"]
            newline = f'{key} = "{value}"'
            add_newline(f"{self.workdir}/build/conf/auto.conf", newline)
        for entries in self.config["yocto.exactconf"]:
            if "{{" in entries:
                entries = entries.format()
            add_newline(f"{self.workdir}/build/conf/auto.conf", entries)

    def image_builder(self, recipe, extra_args="", timeout=1000):
        bitbake_cmnd = f"bitbake {recipe} {extra_args}"
        self.console.runcmd(bitbake_cmnd, timeout=timeout)

    def deploy(self, deploy_dir=""):
        """This Function deploy the generated yocto build images to specific location
        Parameters:
            yocto_artifacts - to copy any specific files
            yocto_deploy_dir : to copy images to specific location
            deploy_dir : From location
        """

        ret = True
        if self.config.get("yocto_deploy_dir"):
            yocto_deploy_dir = self.config.yocto_deploy_dir
            if not is_dir(yocto_deploy_dir):
                mkdir(yocto_deploy_dir)
        else:
            yocto_deploy_dir = self.imagesdir

        if not deploy_dir:
            deploy_dir = self.deploy_dir

        if "yocto_artifacts" in self.config:
            for image in self.config["yocto_artifacts"]:
                image_file = find_file(image, deploy_dir)
                if image_file:
                    if is_file(image_file):
                        copy_file(image_file, yocto_deploy_dir)
                    elif is_dir(image_file):
                        copyDirectory(image_file, yocto_deploy_dir, symlinks=True)
                else:
                    log.error(f"{image} does not exists in {deploy_dir}")
                    ret = False
        else:
            copyDirectory(deploy_dir, yocto_deploy_dir, symlinks=True)
        return ret


def yocto_build(
    config,
    reset_timeout=500,
    sync_timeout=500,
    setupfile="",
    recipe_name="petalinux-image-minimal",
    recipe_extra_args="",
    build_timeout=1000,
    deploy_dir="",
):

    yocto_builder = Yocto(config)

    yocto_builder.fetch()

    yocto_builder.repo_reset(timeout=reset_timeout)

    yocto_builder.repo_sync(timeout=sync_timeout)

    yocto_builder.repo_start()

    yocto_builder.sdk_setup(setupfile=setupfile)

    yocto_builder.reset_conf_file()

    yocto_builder.set_conf_vals()

    yocto_builder.image_builder(
        recipe=recipe_name, extra_args=recipe_extra_args, timeout=build_timeout
    )

    yocto_builder.deploy(deploy_dir=deploy_dir)

    return True
