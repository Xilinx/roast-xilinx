#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import atexit
import logging
from roast.utils import setup_logger, reset, mkdir, is_dir, copyDirectory, remove
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

        # override workDir with customized option
        if config.get("work_root_dir"):
            work_dir = os.path.join(
                config.work_root_dir,
                *config.get("base_params", ""),
                *config.get("test_path_list", ""),
                *config.get("params", ""),
                "work",
            )
            if self.setup:
                reset(work_dir)
            config["workDir"] = work_dir

        self.wsDir = config["wsDir"]
        self.workDir = config["workDir"]
        self.logDir = config["logDir"]
        self.imagesDir = config["imagesDir"]
        if self.setup:
            reset(config["wsDir"])
        mkdir(config["workDir"])
        mkdir(config["logDir"])
        mkdir(config["imagesDir"])

        log_filename = config.get("log_filename")
        console_level = config.get("console_level", logging.INFO)
        file_level = config.get("file_level", logging.DEBUG)
        console_format = config.get("console_format", "")
        file_format = config.get("file_format", "")
        time_format = config.get("time_format", "")
        report_summary = config.get("report_summary", False)
        report_tokens = config.get("report_tokens", [])
        self.logger = setup_logger(
            config["logDir"],
            log_filename=log_filename,
            console_level=console_level,
            file_level=file_level,
            console_format=console_format,
            file_format=file_format,
            time_format=time_format,
            report_summary=report_summary,
            report_tokens=report_tokens,
        )
        log.info("Logger setup completed.")
        log.debug(f'wsDir={config["wsDir"]}')
        log.debug(f'workDir={config["workDir"]}')
        log.debug(f'logDir={config["logDir"]}')
        log.debug(f'imagesDir={config["imagesDir"]}')
        log.debug(
            f"logfile={self.logger.log_path}, console_level={console_level}, file_level={file_level}"
        )
        log.debug(f"console_format={console_format}, file_format={file_format}")
        atexit.register(self.__del__)

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

    def __del__(self):
        if self.config.get("clean_work_dir"):
            remove(self.workDir)
