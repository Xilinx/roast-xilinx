#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import math
import logging
from roast.xexpect import Xexpect
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps
from roast.testlibs.linux.dts import DtsLinux
from roast.testlibs.linux.sysdevices import SysDevices
from roast.testlibs.linux.kconfig import Kconfig

log = logging.getLogger(__name__)


class I2cLinux(FileOps, DtsLinux, SysDevices, Kconfig, BaseLinux):
    def __init__(self, console, config):
        super().__init__(console, config)

    def get_device_path(self, channel):
        self.console.sync()
        self.console.runcmd(
            f"find {self.sys_devices} -iname {channel}", expected="\r\n"
        )
        i2c_dev_path = self.console.output().split("\n")[0].rstrip()
        return i2c_dev_path

    def get_device_name(self, channel, dev_addr):
        i2c_dev_path = self.get_device_path(channel)
        if self.is_file_exist(f"{i2c_dev_path}/{dev_addr}/of_node"):
            self.console.sync()
            self.console.runcmd(
                f"ls -l {i2c_dev_path}/{dev_addr} | grep of_node |"
                f" awk '{{print $NF}}'",
                expected="\r\n",
            )
            i2c_dev_name = self.console.output().split("base/")[-1]
        else:
            i2c_dev_name = f"{i2c_dev_path}/{dev_addr}"
        return i2c_dev_name

    def get_devices(self, channel):
        i2c_dev_path = self.get_device_path(channel)
        i2c_dev = channel[-1]
        self.console.sync()
        self.console.runcmd(f"ls {i2c_dev_path} | grep '{i2c_dev}-'", expected="\r\n")
        self.devices = []
        if self.console.output():
            self.devices = self.console.output().split("\n")
            self.devices = [i.rstrip() for i in self.devices]
            return self.devices

    def detect_channel(self, i2c_chan, channel, i2c_devices):
        self.console.runcmd(f"i2cdetect -y -r {i2c_chan}", expected="\r\n")
        self.i2cdetect_output = self.console.output().splitlines()
        for index, device in enumerate(self.i2c_devices):
            displacement = int(device[-1], 16)
            addr_line = device[0]
            addresses = ["UU", device]
            for item in self.i2cdetect_output:
                if f"{addr_line}0: " in item:
                    item = item.split(": ")[1]
                    dev_name = self.get_device_name(channel, self.i2c_dev[index])
                    if item.split()[displacement] in addresses:
                        self.i2c_detect.append(dev_name)
                        break
                    else:
                        return dev_name

    def is_i2c_detect(self, i2c_channels=None, silent_discard=True):
        self.i2c_not_detect = []
        self.i2c_detect = []
        for channel in i2c_channels:
            self.i2c_dev = self.get_devices(channel)
            if not self.i2c_dev:
                continue
            self.i2c_devices = [s[2:] for s in self.i2c_dev]
            self.i2c_devices = [i.lstrip("0") for i in self.i2c_devices]
            i2c_chan = channel.split("-")[-1]
            dev_name = self.detect_channel(i2c_chan, channel, self.i2c_devices)
            if dev_name is None:
                pass
            else:
                for address in self.i2c_devices:
                    self.console.runcmd(
                        f"i2ctransfer -y -f {i2c_chan} w1@0x{address} 0x00",
                        expected="\r\n",
                    )
                    self.console.runcmd(
                        f"i2ctransfer -y -f {i2c_chan} w1@0x{address} 0x00 r1@0x{address}",
                        expected="\r\n",
                    )
                dev_name = self.detect_channel(i2c_chan, channel, self.i2c_devices)
                if dev_name is None:
                    continue
                else:
                    self.i2c_not_detect.append(dev_name)
        log.info("============== SUMMARY ==============")
        log.info("i2c detected peripherals     : " f"{self.i2c_detect}")
        log.info(f"i2c not detected peripherals : {self.i2c_not_detect}")
        log.info("======================================")
        if not silent_discard and self.i2c_not_detect:
            assert False, f"{self.i2c_not_detect} not detected"
        return self.i2c_detect, self.i2c_not_detect

    def get_bus_speed(self, node_path, node_address):
        self.console.sync()
        cmd = (
            f"hexdump {self.sys_dt_base}/{node_path}@{node_address}/"
            "clock-frequency | grep 0000000"
        )
        self.console.runcmd(cmd, expected="\r\n")
        self.i2c_speed = self.console.output().split()
        self.i2c_speed = (
            self.i2c_speed[1][2:]
            + self.i2c_speed[1][:2]
            + self.i2c_speed[2][2:]
            + self.i2c_speed[2][:2]
        )
        self.i2c_speed_dts = (int(self.i2c_speed, 16)) / 1000
        self.host_console = xexpect()
        cmd = f"cat {self.config['ROOT']}/dmesg.txt | grep {node_address}.*kHz"
        self.host_console.runcmd(cmd)
        self.i2c_speed_dmesg = int(
            self.host_console.output().split("kHz")[0].split()[-1]
        )
        log.info(f"i2c bus speed from dts : {self.i2c_speed_dts} kHz")
        log.info(f"i2c bus speed from dmesg : {self.i2c_speed_dmesg} kHz")
        if self.i2c_speed_dmesg == self.i2c_speed_dts:
            log.info(f"i2c bus speed configured properly " f"from dts")
            return self.i2c_speed_dmesg
        else:
            assert False, f"{self.i2c_speed_dmesg} not detected"

    def find_eeprom_device(self):
        self.console.sync()
        self.console.runcmd(f"find {self.sys_devices} -iname eeprom", expected="\r\n")
        self.eeprom_device = self.console.output().split("\n")[0]
        self.eeprom_i2c = self.eeprom_device.split("/")[-2]
        self.eeprom_i2c_bus = self.eeprom_i2c.split("-")[0]
        self.eeprom_address = self.eeprom_i2c.split("-")[1][-2:]
        self.eeprom_info = {
            "i2c_bus": self.eeprom_i2c_bus,
            "address": self.eeprom_address,
            "sysfs_interface": self.eeprom_device,
        }
        return self.eeprom_info

    def isUp(self, i2c_nodes_path="amba/i2c*", I2cIp="cdns", silent_discard=True):
        self.capture_dmesg()
        self.all_i2c_nodes = self.list_dts_parameters(
            i2c_nodes_path, parameter="compatible"
        )
        self.i2c_nodes = self.get_dts_nodes(self.all_i2c_nodes, I2cIp)
        self.i2c_channels = self.get_channels(self.i2c_nodes, "i2c")
        return self.is_i2c_detect(self.i2c_channels, silent_discard=silent_discard)

    def i2c_transfer(self, write_bytes_count, i2c_command, read_bytes_count):
        cmd = (
            f"i2ctransfer -f -y {self.i2c_bus_number} "
            f"w{write_bytes_count}@0x{self.i2c_slave_address} "
            f"0x{i2c_command} r{read_bytes_count}@0x{self.i2c_slave_address}"
        )
        self.console.runcmd(cmd, expected="\r\n")

    def format_i2ctransfer_output(self):
        return int(
            self.console.output().split()[0][-2:]
            + self.console.output().split()[1][-2:],
            16,
        )

    def get_hwmon_value(self, i2c_device, parameter):
        cmd = f"find /sys/devices -iname hwmon* | grep {i2c_device}"
        self.console.runcmd(cmd, expected="\r\n")
        hwmon_path = self.console.output().split("\n")[-1]
        cmd = f"cat {hwmon_path}/{parameter}"
        self.console.runcmd(cmd, expected="\r\n")
        return int(self.console.output())

    def ina2xx(self):
        self.capture_boot_dmesg()
        if "ina2xx" in self.console.output():
            log.info("ina2xx driver probed")
        else:
            assert False, "ina2xx driver not probed"

        self.i2c_device = self.console.output().partition(
            ": power monitor" " ina226 (Rshunt" " = 2000 uOhm)"
        )
        self.i2c_device = self.i2c_device[0].split()[-1]
        self.i2c_bus_number = self.i2c_device.split("-")[0]
        self.i2c_slave_address = self.i2c_device.split("-")[1][-2:]
        if not self.i2c_bus_number.isdigit():
            assert False, "ina2xx slave device not found"

        self.console.sync()
        self.console.runcmd("i2cdetect -l")
        self.console.runcmd(f"echo y | i2cdetect -r {self.i2c_bus_number}")
        log.info("Defualt calibration_value is 2048")
        log.info("Defualt Current_LSB value is 1.25 " "Milli Amps")

        self.console.sync()
        # Get voltage, current and power values with i2c commands
        self.i2c_transfer("1", "00", "2")
        self.console.sync()

        self.i2c_transfer("1", "05", "2")
        self.console.sync()

        self.i2c_transfer("1", "01", "2")
        shunt_vol_reg0 = self.format_i2ctransfer_output() * 2.5 / 1000
        self.console.sync()

        self.i2c_transfer("1", "02", "2")
        bus_vol_reg0 = self.format_i2ctransfer_output() * 1.25
        self.console.sync()

        self.i2c_transfer("1", "03", "2")
        power_register0 = self.format_i2ctransfer_output() * 25 * 125 * 10
        self.console.sync()

        self.i2c_transfer("1", "04", "2")
        current_register0 = self.format_i2ctransfer_output() * 1.25
        self.console.sync()

        # Get voltage, current and power from hardware monitor sysfs interface
        shunt_vol_reg1 = self.get_hwmon_value(self.i2c_device, "in0_input")
        bus_vol_reg1 = self.get_hwmon_value(self.i2c_device, "in1_input")
        current_register1 = self.get_hwmon_value(self.i2c_device, "curr1_input")
        power_register1 = self.get_hwmon_value(self.i2c_device, "power1_input")

        log.info(
            f"registers     i2c                    sysfs"
            f"--------------------------------------------------------"
            f"shunt vol {shunt_vol_reg0}mV	{shunt_vol_reg1}mV"
            f"bus vol   {bus_vol_reg0}mV	{bus_vol_reg1}mV"
            f"power     {power_register0}mV	{power_register1}mW"
            f"current   {current_register0}mA	{current_register1}mA"
            f"--------------------------------------------------------"
        )

        ina2xx_i2c = [
            int(shunt_vol_reg0),
            int(bus_vol_reg0),
            int(power_register0),
            int(current_register0),
        ]
        ina2xx_hwmon = [
            int(shunt_vol_reg1),
            int(bus_vol_reg1),
            int(power_register1),
            int(current_register1),
        ]
        for i in range(len(ina2xx_i2c)):
            if not math.isclose(ina2xx_i2c[i], ina2xx_hwmon[i], abs_tol=10):
                assert False, "ina2xx_i2c[i] not matched"

    def eeprom_dd(self, eeprom_device, bs="1", count="256"):
        eeprom_w = "/eeprom_write"
        eeprom_r = "/eeprom_read"
        self.createfile(eeprom_w, bs, count)
        cmdlist = [
            f"dd if={eeprom_w} of={eeprom_device} bs={bs} count={count}",
            f"dd if={eeprom_device} of={eeprom_r} bs={bs} count={count}",
        ]
        self.console.runcmd_list(cmdlist)
        diff = self.compfile(eeprom_w, eeprom_r)
        self.console.runcmd(f"rm {eeprom_w} {eeprom_r}")
        if not diff:
            assert False, "eeprom write and read test failed"

    def eeprom_rw_random_iterations(
        self, eeprom_i2c_bus, eeprom_address, iterations="10", extra_addr_bytes="0"
    ):
        eeprom_rw_cmd = (
            f"eeprom -d /dev/i2c-{eeprom_i2c_bus} -a 0x{eeprom_address} -w c "
            f"-n 0 -i {iterations} -o {extra_addr_bytes}"
        )
        failures = ["Cannot read from eeprom for comparision", "fail"]
        self.console.runcmd(
            eeprom_rw_cmd,
            expected="write read comparison completed",
            expected_failures=failures,
        )

    def eeprom_rw_file(
        self, eeprom_i2c_bus, eeprom_address, bs="1", count="100", extra_addr_bytes="0"
    ):
        eeprom_w = "/eeprom_write"
        eeprom_r = "/eeprom_read"
        self.createfile(eeprom_w, bs, count)
        file_size = self.get_file_size(eeprom_w)
        eeprom_rw_cmd = (
            f"eeprom -d /dev/i2c-{eeprom_i2c_bus} -a 0x{eeprom_address} "
            f"-n {file_size} -o {extra_addr_bytes}"
        )
        failures = ["Cannot read from eeprom for comparision", "fail"]
        self.console.runcmd(
            f"{eeprom_rw_cmd} -w c -f {eeprom_w}",
            expected="write read comparison completed",
            expected_failures=failures,
        )
        self.console.runcmd(f"{eeprom_rw_cmd} -f {eeprom_r}")
        diff = self.compfile(eeprom_w, eeprom_r)
        self.console.runcmd(f"rm {eeprom_w} {eeprom_r}")
        if not diff:
            assert False, "eeprom write read with file test failed"

    def eeprom_read(self, eeprom_i2c_bus, eeprom_address, numbData="100", offset="1"):
        eeprom_r1 = "/tmp/eeprom_read1"
        eeprom_r2 = "/tmp/eeprom_read2"
        eeprom_read_cmd = (
            f"eeprom -d /dev/i2c-{eeprom_i2c_bus} -a 0x{eeprom_address} "
            f"-n {numbData} -o {offset}"
        )
        self.console.runcmd(f"{eeprom_read_cmd} -f {eeprom_r1}")
        self.console.runcmd(f"{eeprom_read_cmd} -f {eeprom_r2}")
        diff = self.compfile(eeprom_r1, eeprom_r2)
        self.console.runcmd(f"rm {eeprom_r1} {eeprom_r2}")
        if not diff:
            assert False, "eeprom read test failed"

    def eeprom_rw_incremental_iterations(
        self,
        eeprom_i2c_bus,
        eeprom_address,
        numbData=10,
        iterations="100",
        extra_addr_bytes="0",
        hostIp="10.10.70.101",
    ):
        ping_txt = "/tmp/ping.txt"
        self.console.runcmd(f"ping {hostIp} > {ping_txt} &", expected="\r\n")
        ping_pid = self.console.output().split()[-1]
        eeprom_rw_cmd = (
            f"eeprom -d /dev/i2c-{eeprom_i2c_bus} -a 0x{eeprom_address} -w c "
            f"-n {numbData} -i {iterations} -t i -o {extra_addr_bytes}"
        )
        failures = ["Cannot read from eeprom for comparision", "fail"]
        self.console.runcmd(
            eeprom_rw_cmd,
            expected="write read comparison completed",
            expected_failures=failures,
            timeout=2700,
        )
        self.console.runcmd(f"kill -2 {ping_pid}")
        self.console.runcmd(
            f"cat {ping_txt}; rm {ping_txt}", expected=", 0% packet loss"
        )

    def i2c_dtb_overlay_frequency(self, i2c_node, bitstream_bin, dtbo_file, serverIp):
        self.get_tftp_file(bitstream_bin, serverIp)
        self.load_bitstream(bitstream_bin, dtbo_file)
        self.console.runcmd(f"hexdump {self.sys_dt_base}/{i2c_node}/clock-frequency")
