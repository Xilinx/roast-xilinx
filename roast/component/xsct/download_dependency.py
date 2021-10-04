#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import sys
import shutil


def dependency_list(driver_path, test_name, destination_path):
    example_name = str(test_name) + ".c"
    data_path = str(driver_path) + "/data"
    print(example_name)
    print(data_path)
    files = os.listdir(data_path)
    dictionary = {}
    templist = []
    for file in files:
        if str(file) == "dependencies.props":
            with open(str(data_path) + "/dependencies.props") as f:
                content = f.readlines()
                content = [x.strip() for x in content]
                for item in content:
                    if not ".c" in item:
                        continue
                    templist.append([x.strip() for x in item.split("=")])
                for item in templist:
                    dictionary[item[0]] = [x.strip() for x in item[1].split(",")]
                if example_name not in dictionary:
                    print("Example Not found")
                    break
                for key, value in dictionary.items():
                    if key == example_name:
                        for item in value:
                            if item != "NULL":
                                shutil.copy(
                                    str(driver_path) + "/examples/" + str(item),
                                    destination_path,
                                )
                        break


if len(sys.argv) < 4:
    print("INCORRECT NUMBER OF ARGS")
else:
    dependency_list(sys.argv[1], sys.argv[2], sys.argv[3])
