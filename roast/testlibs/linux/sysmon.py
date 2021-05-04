#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import re
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.sysdevices import SysDevices
from roast.testlibs.linux.kconfig import Kconfig
from roast.utils import check_if_string_in_file


class Sysmon(FileOps, DtsLinux, SysDevices, Kconfig, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def check_sysmon_regn(self, pass_string="Successfully"):
        """
        Checks if sysmon is enabled in the device tree
        """
        self.console.runcmd(f"dmesg | grep -r sysmon", expected="\r\n")
        console_print = self.console.output()
        if pass_string not in console_print:
            assert False, "Sysmon is not registered"

    def check_iio_devices(self):
        """
        Returns the iio device id. (e.g. iio:device0)
        """
        self.console.runcmd(f"ls {self.iio_devices}", expected="\r\n")
        iio_device = self.console.output().split()
        if iio_device:
            return iio_device[0]
        else:
            assert False, "No iio device is found"

    def iio_device_dir(self):
        """
        Changes working directory to the iio device directory.
        """
        self.console.runcmd(
            f"cd {self.iio_devices}/{self.check_iio_devices()}", expected="\r\n"
        )

    def find_iio_device_name(self):
        """
        Returns the specific sysmon device name as per Device Tree.
        (e.g. xlnx,versal-sysmon)
        """
        self.iio_device_dir()
        self.console.runcmd(f"cat name", expected="\r\n")
        iio_device_name = self.console.output()
        return iio_device_name

    def validate_supply_name(self, supply_name, path="."):
        """
        Validates the given supply name as per the design/device tree.
        """
        self.console.runcmd(f"find {path} -name {supply_name}", expected="\r\n")
        if self.console.output():
            return True
        else:
            return False

    def event_monitor(self, event_monitor_path="", action="start"):
        """
        Valid actions are "start" or "stop"
        Either starts or stops the iio event monitor application process
        in the background.Checks in the rootfs if no path is given explicitly.
        """
        device_name = self.find_iio_device_name()
        if not event_monitor_path:
            self.is_bin_exist("iio_event_monitor", silent_discard=False)
            event_monitor_path = "iio_event_monitor"
        if action == "start":
            self.console.runcmd(
                f"{event_monitor_path} {device_name} &",
                err_msg="Event Monitor Initialisation Failed",
                timeout=50,
            )
        elif action == "stop":
            self.console.runcmd(
                f"pidof {event_monitor_path} {device_name}", expected="\r\n"
            )
            pid_no = self.console.output()
            if pid_no:
                self.console.runcmd(f"kill -9 {pid_no}")
        else:
            assert False, "Not a valid action for event_monitor"

    def read_sysmon_value(self, supply_name):
        """
        Reads the sysmon value (temp/voltage) on device for the given supply.
        """
        if self.validate_supply_name(supply_name):
            self.console.runcmd(f"cat {supply_name}", expected="\r\n")
            return self.console.output()
        else:
            assert False, "Valid supply name is not given to be read"

    def read_threshold_levels(self, event_name):
        """
        Reads threshold levels for the given suppy fixed as per the design.
        """
        if self.validate_supply_name(event_name, "events/"):
            self.console.runcmd(f"cat events/{event_name}", expected="\r\n")
            return self.console.output()
        else:
            assert False, "Valid event name is not given to be read"

    def set_sysmon_events(self, event_name, value="1"):
        """
        Sets sysmon events if value is >= 1, to raise an alarm when the
        system crosses a threshold value for a particular supply, otherwise
        reset the event.
        """
        if self.validate_supply_name(event_name, "events/"):
            self.console.runcmd(f"echo {value} > events/{event_name}")
        else:
            assert False, "Valid event name is not given to be created"

    def set_threshold_levels(self, event_name, val):
        """
        Sets the threshold levels for the given supply. Has to be used to
        explicitly trigger an alarm.
        """
        if self.validate_supply_name(event_name, "events/") and val:
            self.console.runcmd(f"echo {val} > events/{event_name}")
        else:
            assert (
                False
            ), "A valid event name or the value, is not given while setting levels"

    def check_event_occurrence(
        self, file_path, pass_string_regex, silent_discard=False
    ):
        """
        Checks the occurrence of an alarm in the log file.
        """
        if not check_if_string_in_file(file_path, pass_string_regex, re.DOTALL):
            if not silent_discard:
                assert False, "Triggered Event was not found in the log"
            else:
                return False
        else:
            return True
