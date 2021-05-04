#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from roast.confParser import generate_conf
from roast.component.basebuild import Basebuild


def test_basebuild_params(request, build_dir):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    test_name = "main"
    params = ["test1"]
    # override configuration
    wsDir = os.path.join(build_dir, "tests", test_name, *params)
    logDir = os.path.join(wsDir, "log")
    workDir = os.path.join(wsDir, "work")
    imagesDir = os.path.join(wsDir, "images")
    overrides = [
        f"buildDir={build_dir}",
        f"wsDir={wsDir}",
        f"logDir={logDir}",
        f"workDir={workDir}",
        f"imagesDir={imagesDir}",
    ]

    config = generate_conf(
        rootdir, fspath, test_name, params=params, overrides=overrides
    )
    builder = Basebuild(config)
    builder.configure()
    assert os.path.exists(builder.config["wsDir"])
    assert os.path.exists(builder.config["logDir"])
    assert os.path.exists(builder.config["workDir"])
    assert os.path.exists(builder.config["imagesDir"])
    assert os.path.exists(os.path.join(builder.config["workDir"], "conf.py"))
    assert os.path.exists(os.path.join(builder.config["workDir"], "test_dummy.py"))
    assert os.getcwd() == config["workDir"]
