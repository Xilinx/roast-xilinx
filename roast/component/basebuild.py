#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import logging
from roast.utils import setup_logger, reset, mkdir, is_dir, copyDirectory
from roast.component.system import SystemBase

log = logging.getLogger(__name__)


class Basebuild(SystemBase):
    """
    This is the base class for builders.

    By default, this will create a workspace with three subdirectories - work, log, and images.
    In addition, the logger will be initiated with parameters from the configuration if provided.
    Otherwise, default logger values will be used.

    """

    def __init__(self, config, setup: bool = True):
        super().__init__(config)
        self.setup = setup
        self.wsDir = config["wsDir"]
        self.workDir = config["workDir"]
        self.logDir = config["logDir"]
        self.imagesDir = config["imagesDir"]
        if self.setup:
            reset(self.config["wsDir"])
        mkdir(self.config["workDir"])
        mkdir(self.config["logDir"])
        mkdir(self.config["imagesDir"])

        log_filename = config.get("log_filename")
        console_level = config.get("console_level", logging.INFO)
        file_level = config.get("file_level", logging.DEBUG)
        console_fmt = config.get("console_fmt", {})
        file_fmt = config.get("file_fmt", {})
        self.logger = setup_logger(
            config["logDir"],
            log_filename,
            console_level,
            file_level,
            console_fmt,
            file_fmt,
        )
        log.info("Logger setup completed.")
        log.debug(f'wsDir={config["wsDir"]}')
        log.debug(f'workDir={config["workDir"]}')
        log.debug(f'logDir={config["logDir"]}')
        log.debug(f'imagesDir={config["imagesDir"]}')
        log.debug(
            f"logfile={self.logger.handlers[1].baseFilename}, console_level={console_level}, file_level={file_level}"
        )
        log.debug(f"console_fmt={console_fmt}, file_fmt={file_fmt}")

    def configure(self):
        if self.setup:
            # Copy test files
            # Iterate from last param till test_path.
            params_list = self.config["params"]
            while True:
                src = os.path.join(self.config["test_path"], *params_list)
                if is_dir(src):
                    copyDirectory(src, self.config["workDir"])
                    break
                if params_list:
                    params_list.pop()
                else:
                    break
        if self.config.get("chdir", True):
            os.chdir(self.config["workDir"])

    def build(self):
        pass
