#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import filecmp
import logging
import pytest
from roast.confParser import generate_conf
from roast.component.bif.generate import generate_bif
from roast.utils import Logger, mkdir


def get_tests(dir):
    dirs = []
    dirname = os.path.join(os.path.dirname(__file__), dir)
    for entry in os.listdir(dirname):
        if not entry.startswith("__") and os.path.isdir(os.path.join(dirname, entry)):
            dirs.append(entry)
    dirs.sort()
    return dirs


def test_bif_no_seed(request, build_dir):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    wsDir = build_dir
    logDir = os.path.join(wsDir, "log")
    workDir = os.path.join(wsDir, "work")
    imagesDir = os.path.join(wsDir, "images")
    overrides = [
        f"buildDir={build_dir}",
        f"wsDir={wsDir}",
        f"logDir={logDir}",
        f"workDir={workDir}",
        f"imagesDir={imagesDir}",
        "randomize=True",
    ]
    config = generate_conf(
        rootdir=rootdir,
        test_path=fspath,
        test_name="performance",
        params=["003"],
        overrides=overrides,
    )
    mkdir(workDir)
    mkdir(imagesDir)
    del config["seed"]
    try:
        generate_bif(config=config, format_type="new")
    except:
        assert False, f"generate_bif() raised exception"


@pytest.mark.parametrize("test", get_tests("regression"))
def test_regression_bif_randomization(request, test, build_dir):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    wsDir = build_dir
    logDir = os.path.join(wsDir, "log")
    workDir = os.path.join(wsDir, "work")
    imagesDir = os.path.join(wsDir, "images")
    logger = Logger(logDir)
    overrides = [
        f"buildDir={build_dir}",
        f"wsDir={wsDir}",
        f"logDir={logDir}",
        f"workDir={workDir}",
        f"imagesDir={imagesDir}",
        "randomize=True",
    ]
    config = generate_conf(
        rootdir=rootdir,
        test_path=fspath,
        test_name="regression",
        params=[test],
        overrides=overrides,
    )
    mkdir(workDir)
    mkdir(imagesDir)
    generate_bif(config=config, format_type="new")
    logger.close()
    test_dir = os.path.join(os.path.dirname(__file__), "regression", test)
    assert filecmp.cmp(
        os.path.join(config["imagesDir"], "boot.bif"),
        os.path.join(test_dir, "boot.bif"),
    )


@pytest.mark.parametrize("test", get_tests("performance"))
def test_performance_bif_randomization(request, test, build_dir):
    rootdir = request.config.rootdir.strpath
    fspath = request.node.fspath
    wsDir = build_dir
    logDir = os.path.join(wsDir, "log")
    workDir = os.path.join(wsDir, "work")
    imagesDir = os.path.join(wsDir, "images")
    logger = Logger(logDir)
    overrides = [
        f"buildDir={build_dir}",
        f"wsDir={wsDir}",
        f"logDir={logDir}",
        f"workDir={workDir}",
        f"imagesDir={imagesDir}",
        "randomize=True",
    ]
    config = generate_conf(
        rootdir=rootdir,
        test_path=fspath,
        test_name="performance",
        params=[test],
        overrides=overrides,
    )
    mkdir(workDir)
    mkdir(imagesDir)
    generate_bif(config=config, format_type="new")
    logger.close()
    test_dir = os.path.join(os.path.dirname(__file__), "performance", test)
    assert filecmp.cmp(
        os.path.join(config["imagesDir"], "boot.bif"),
        os.path.join(test_dir, "boot.bif"),
    )
