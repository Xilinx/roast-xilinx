#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import time
import logging
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.xexpect import Xexpect
from roast.testlibs.linux.baselinux import BaseLinux
from roast.component.board.boot import is_linux_cons

log = logging.getLogger(__name__)


class Ethernet(BaseLinux):
    def __init__(self, console, config, eth_interface):
        super().__init__(console, config)
        self.platform = None
        self.client_ip = "10.10.70.101"
        self.client_mac = "2c:2b:59:cf:7c:00"
        self.board_ip = "10.10.70.1"
        self.ping_intervel = "1"
        self.ping_size = "45"
        self.ping_count = "10"
        self.file_size = "4096"
        self.pktgen_size = "200"
        self.pktgen_count = "1"
        self.pktgen_burst = "1"
        self.pktgen_delay = "0"
        self.pktgen_frags = "4"
        self.pktgen_vlan_id = "0"
        self.eth_interface = "eth0"
        self.host_interface = "enp9s0"
        self.updown_count = "3"
        self.mtu = "1500"
        self.udp_mtu = "1500"
        self.iperf3_binary = "iperf3"
        self.extra_iperf3_args = ""
        self.timeout = "60"
        self.client_user = None
        self.client_password = None
        self.client_sudo_login = None
        self.server_user = "root"
        self.server_password = "root"
        self.config = config
        self.terminal = console
        self.log = log
        self.eth_interface = eth_interface
        self.terminal.prompt = r"root(.*?)# "
        if self.config.get("client_user"):
            self.client_user = self.config.client_user
        if self.config.get("client_password"):
            self.client_password = self.config.client_password
        if self.config.get("client_sudo_login"):
            self.client_sudo_login = self.config.client_sudo_login
        if self.config.get("target_ip"):
            self.client_ip = self.config.target_ip
        if self.config.get("board_ip"):
            self.board_ip = self.config.board_ip
        if self.config.get("client_mac"):
            self.client_mac = self.config.client_mac

    def _setip_config(self, config):
        self.config = config

    def ping_test(self):
        cmd = f"ping {self.client_ip} -s {self.ping_size} -c {self.ping_count}"
        self.terminal.runcmd(cmd=str(cmd), timeout=60, expected=" 0% packet loss")

    def ping_flood(self):
        self.get_client_console()
        self.client_console.runcmd(
            cmd=f"ping -f {self.board_ip} -i 5 -c 5",
            timeout=60,
            expected=" 0% packet loss",
        )
        self.terminal.runcmd(
            cmd=f"ping {self.client_ip} -c 5", timeout=30, expected=" 0% packet loss"
        )

    def ifupdown(self):
        for count in self.updown_count:
            self.terminal.runcmd(cmd=f"ifconfig {self.eth_interface} down", timeout=15)
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} up;sleep 5",
                timeout=15,
                expected_failures="link is not ready",
            )
            self.ping_test()

    def eth_pktgen(self):
        commands = [
            "echo 'stop' > /proc/net/pktgen/pgctrl",
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_0",
            f"echo 'add_device {self.eth_interface}' > /proc/net/pktgen/kpktgend_0",
            f"echo 'count {self.pktgen_count}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'clone_skb 100' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'pkt_size {self.pktgen_size}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'burst {self.pktgen_burst}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'delay {self.pktgen_delay}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'vlan_id {self.pktgen_vlan_id}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'vlan_p 0' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'vlan_cfi 0' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'frags {self.pktgen_frags}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'dst {self.client_ip}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'dst_mac {self.client_mac}' > /proc/net/pktgen/{self.eth_interface}",
            "echo 'start' > /proc/net/pktgen/pgctrl",
            f"cat /proc/net/pktgen/{self.eth_interface}",
            "paramsCount=$(grep -E 'Params: count' /proc/net/pktgen/eth0 | awk '{print substr($3,1)}')",
            "pktSofar=$(grep -E 'pkts-sofar' /proc/net/pktgen/eth0 | awk '{print substr($2,1)}')",
            '[ "$paramsCount" -eq "$pktSofar" ]',
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)

    def eth_scp(self):
        self.terminal.runcmd(cmd="scp_file=$(mktemp scp.XXXXXXXXX)")
        self.terminal.runcmd(
            cmd=f"dd if=/dev/zero of=$scp_file bs=1 count=0 seek={self.file_size}"
        )
        scp_cmd = f"scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r $scp_file {self.client_user}@{self.client_ip}:/home/{self.client_user}"
        index = self.terminal.runcmd(
            cmd=scp_cmd,
            expected=["(y/n)", "password"],
            wait_for_prompt=False,
            timeout=120,
        )
        if index == "1":
            self.terminal.runcmd(cmd=f"{self.client_password}", timeout=120)
        else:
            self.terminal.runcmd(
                cmd="y", expected="password", wait_for_prompt=False, timeout=300
            )
            self.terminal.runcmd(cmd=f"{self.client_password}")
        self.terminal.runcmd(cmd="rm $scp_file")

    def iperf_tcp_host_client(self):
        self.log.info("Starting an iperf3 server on the client...")
        self.get_client_console()
        cmd = f"{self.iperf3_binary} -s &"
        self.client_console.runcmd(
            cmd=cmd, expected="Server listening", wait_for_prompt=False, timeout=60
        )
        self.log.info(f"Measuring {self.iperf3_binary} TCP throughput...")
        cmd = f"{self.iperf3_binary} -c {self.client_ip} -f m {self.extra_iperf3_args}"
        self.terminal.runcmd(cmd=cmd, timeout=60)
        time.sleep(5)
        self.client_console.runcmd(cmd=f"pkill {self.iperf3_binary}", timeout=60)

    def iperf_tcp_client_host(self):
        self.get_client_console()
        self.log.info("Starting an iperf3 server on the board...")
        self.terminal.runcmd(cmd=f"{self.iperf3_binary} -s &", timeout=60)
        time.sleep(15)
        self.log.info(f"Starting an iperf3 client...")
        self.client_console.runcmd(
            cmd=f"{self.iperf3_binary} -c {self.board_ip} -f m {self.extra_iperf3_args}",
            timeout=60,
        )
        time.sleep(5)
        self.terminal.runcmd(cmd=f"pkill {self.iperf3_binary}", timeout=60)

    def iperf_udp_host_client(self):
        self.log.info("Starting an iperf3 server on the client...")
        self.get_client_console()
        cmd = f"{self.iperf3_binary} -s &"
        self.client_console.runcmd(
            cmd=cmd, expected="Server listening", wait_for_prompt=False, timeout=60
        )
        time.sleep(15)
        self.log.info(f"Measuring {self.iperf3_binary} UDP throughput...")
        cmd = (
            f"{self.iperf3_binary} -c {self.client_ip} -f m -u {self.extra_iperf3_args}"
        )
        self.terminal.runcmd(cmd=cmd, timeout=60)
        time.sleep(5)
        self.client_console.runcmd(cmd=f"pkill {self.iperf3_binary}", timeout=60)

    def iperf_udp_client_host(self):
        self.get_client_console()
        self.log.info("Starting an iperf3 server on the board...")
        self.terminal.runcmd(cmd=f"{self.iperf3_binary} -s &", timeout=60)
        time.sleep(15)
        self.log.info(f"Starting an iperf3 client...")
        self.client_console.runcmd(
            cmd=f"{self.iperf3_binary} -c {self.board_ip} -f m -u {self.extra_iperf3_args}",
            timeout=60,
        )
        time.sleep(5)
        self.terminal.runcmd(cmd=f"pkill {self.iperf3_binary}", timeout=60)

    def netperf_tcp_host_client(self):
        self.log.info("Starting an netperf server on the client...")
        self.get_client_console()
        cmd = f"ps -ef | grep netserver || netserver -D -4 &"
        self.client_console.runcmd(cmd=cmd, timeout=20)
        if self.mtu != "1500":
            time.sleep(2)
            self.log.info(f"Updating MTU size on host and device... : {self.mtu}")
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu {self.mtu} up; ifconfig"
            )
            time.sleep(5)
            self.client_console.runcmd(
                cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu {self.mtu} up; ifconfig"
            )
            time.sleep(5)
            self.udp_mtu = f"{self.mtu} - 28"
            time.sleep(5)
        self.log.info(
            f"Device Netperf Output for TCP(Tx Mode) with MTU size {self.mtu}"
        )
        time.sleep(1)
        cmd = f"netperf -c -C -H {self.client_ip} -t TCP_STREAM"
        failures = ["No space left on device", "recv_response:"]
        self.terminal.runcmd(cmd=cmd, expected_failures=failures, timeout=60)
        time.sleep(5)

    def netperf_udp_host_client(self):
        self.log.info("Starting an netperf server on the client...")
        self.get_client_console()
        cmd = f"ps -ef | grep netserver || netserver -D -4 &"
        self.client_console.runcmd(cmd=cmd, timeout=20)
        if self.mtu != "1500":
            time.sleep(2)
            self.log.info(f"Updating MTU size on host and device... : {self.mtu}")
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu {self.mtu} up; ifconfig"
            )
            time.sleep(5)
            self.client_console.runcmd(
                cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu {self.mtu} up; ifconfig"
            )
            time.sleep(5)
            self.udp_mtu = f"{self.mtu} - 28"
            time.sleep(5)
        self.log.info(
            f"Device Netperf Output for UDP(Tx Mode) with MTU Size: {self.mtu}"
        )
        time.sleep(1)
        cmd = f"netperf -c -C -H {self.client_ip} -t UDP_STREAM"
        failures = ["No space left on device", "recv_response:"]
        self.terminal.runcmd(cmd=cmd, expected_failures=failures, timeout=60)
        time.sleep(5)

    def netperf_tcp_client_host(self):
        self.get_client_console()
        failures = ["No space left on device", "recv_response:"]
        cmd = f"ps -ef | grep netserver || netserver -D -4 &"
        self.terminal.runcmd(cmd=cmd, timeout=20)
        time.sleep(5)
        cmd = f"netperf -c -C -H {self.board_ip} -t TCP_STREAM -- -m {self.mtu} -M {self.mtu}"
        self.client_console.runcmd(cmd=cmd, expected_failures=failures, timeout=50)

    def netperf_udp_client_host(self):
        self.get_client_console()
        failures = ["No space left on device", "recv_response:"]
        cmd = f"ps -ef | grep netserver || netserver -D -4 &"
        self.terminal.runcmd(cmd=cmd, timeout=20)
        time.sleep(5)
        self.log.info(
            f"Host Netperf Output for UDP(Rx Mode) with MTU Size: {self.udp_mtu}"
        )
        cmd = f"netperf -c -C -H {self.board_ip} -t UDP_STREAM -- -m {self.mtu} -M {self.udp_mtu}"
        self.client_console.runcmd(cmd=cmd, timeout=50)
        time.sleep(5)

    def eth_dhcp(self):
        cmd = f"udhcpc -i {self.eth_interface}"
        self.terminal.runcmd(cmd=cmd, timeout=30, expected_failures=["not found"])
        self.ping_test()

    def eth_speed(self):

        for speed in [1000, 10, 100]:
            cmd = f"ethtool -s {self.eth_interface} speed {speed} duplex full; sleep 15"
            self.terminal.runcmd(cmd=cmd)
            self.terminal.sendline("\r\n")
            self.terminal.runcmd(cmd=f"ethtool {self.eth_interface}")
            self.ping_test()
        cmd = f"ethtool -s {self.eth_interface} autoneg on; sleep 15"
        self.terminal.runcmd(cmd=cmd)
        self.terminal.sendline("\r\n")
        self.terminal.runcmd(cmd=f"ethtool {self.eth_interface}")
        self.ping_test()

    def eth_tftp(self):
        failures = [
            "server error:",
            "(2) Access violation",
            "No such file or directory",
            "ERROR",
        ]
        tftp_file = "system.bit"
        cmdd = f"tftp -g -r {tftp_file} {self.client_ip}"
        self.terminal.runcmd(cmd=cmdd, timeout=300, expected_failures=failures)

    def eth_telnet(self):
        self.terminal.runcmd(cmd="telnetd", timeout=20)
        self.get_client_console()
        self.client_console.runcmd(
            cmd=f"telnet {self.board_ip}",
            timeout=20,
            expected="Peta",
            wait_for_prompt=False,
        )
        self.client_console.sendline("root")
        self.client_console.sendline("root")
        time.sleep(1)
        self.client_console.sendline("root")
        self.client_console.runcmd(
            cmd=f"ls", timeout=20, expected=":~# ", wait_for_prompt=False
        )

    def eth_gravcat(self, **kwargs):
        self.get_client_console()
        cmd = f"gravecat -l 9999 &"
        self.terminal.sync()
        self.terminal.runcmd(
            cmd=cmd, timeout=20, expected_failures=["ommand", "failed"]
        )
        self.client_console.runcmd(
            f"/usr/bin/gravecat_x86_64 -s {self.boardIp} 9999 4 1000 500",
            expected="using",
            timeout=10,
            wait_for_prompt=False,
        )
        time.sleep(600)
        self.client_console.sendline("\x03")
        self.client_console.runcmd(
            cmd="if pgrep gravecat;then kill -9 `pgrep -f gravecat`; fi"
        )
        self.terminal.sync()
        self.ifupdown()

    def suspend_resume_eth_wkp(self, platform):
        eth_nodes = ["ff0b0000", "ff0c0000", "ff0d0000", "ff0e0000"]
        self.log.info("Starting an netperf server on the client...")
        self.terminal.runcmd("cat /proc/cpuinfo")
        self.terminal.runcmd("ifconfig -a")
        self.terminal.runcmd("echo 8 > /proc/sys/kernel/printk")
        self.terminal.runcmd("echo 0 > /sys/module/printk/parameters/console_suspend")
        if platform == "versal":
            self.terminal.runcmd(
                f"echo disabled > {self.sys_axi}/ff000000.serial/tty/ttyAMA0/power/wakeup"
            )
            self.terminal.runcmd(
                f"echo enabled > {self.sys_axi}/ff0c0000.ethernet/net/eth0/power/wakeup"
            )
            self.terminal.runcmd(
                "echo mem > /sys/power/state",
                expected="CPU1 killed",
                wait_for_prompt=False,
            )
        else:
            self.terminal.runcmd(
                f"echo disabled > {self.sys_axi}/ff000000.serial/tty/ttyPS0/power/wakeup"
            )
            for node in eth_nodes:
                self.terminal.runcmd(
                    f"cat /proc/device-tree/axi/ethernet\@{node}/status",
                    expected="\r\n",
                )
                node_status = self.terminal.output()
                if node_status == "okay":
                    ethernet_node = node
            self.terminal.runcmd(
                f"echo enabled > {self.sys_axi}/{ethernet_node}.ethernet/net/eth0/power/wakeup"
            )
            self.terminal.runcmd(
                "echo mem > /sys/power/state",
                expected="CPU3 killed",
                wait_for_prompt=False,
            )
        self.get_client_console()
        self.client_console.runcmd(
            cmd=f"ping {self.board_ip} -c 5", expected_failures="0 received", retries=2
        )
        time.sleep(15)
        is_linux_cons(self.terminal)
        self.terminal.runcmd("pwd")
        if platform == "versal":
            self.terminal.runcmd(
                f"echo enabled > {self.sys_axi}/ff000000.serial/tty/ttyAMA0/power/wakeup"
            )
            self.terminal.runcmd('bootmode="sd_boot"')
        else:
            self.terminal.runcmd(
                f"echo enabled > {self.sys_axi}/ff000000.serial/tty/ttyPS0/power/wakeup"
            )

    def get_client_console(self):
        if self.config["eth_host_name"]:
            self.client_console = Xexpect(
                hostname=self.config["eth_host_name"],
                hostip=None,
                userid=None,
                password=None,
                non_interactive=False,
                log=log,
            )
        elif self.config["board_interface"] == "systest":
            client_ip = self.config["systest_host"]
            self.client_console = Xexpect(
                hostname=client_ip, non_interactive=False, log=log
            )
        else:
            client_ip = self.client_ip
            self.client_console = Xexpect(
                hostip=client_ip,
                userid=self.client_user,
                password=self.client_password,
                non_interactive=False,
                log=log,
            )
            self.client_console.prompt = "bash-"
            self.client_console.runcmd("/bin/bash --norc")

        def _sudo_login():
            self.client_console.prompt = r"root(.*?)# "
            self.client_console.sendline(cmd="sudo su -")
            index = self.client_console.expect(
                expected=["password", "root"],
                expected_failures="Permission denied",
                err_msg="fail to login with sudo",
                wait_for_prompt=False,
            )
            if index == 1:
                self.client_console.runcmd(
                    cmd=self.client_password,
                    expected="root",
                    expected_failures=["Permission denied", "Sorry", "not allowed"],
                    err_msg="fail to login with sudo",
                    wait_for_prompt=False,
                )

        def _set_status_init():
            self.client_console.sync()
            self.client_console._setup_init()
            self.client_console.exit_nzero_ret = True

        if self.client_sudo_login:
            _sudo_login()
        _set_status_init()

    def ifplugd(self):
        self.terminal.runcmd(cmd="ifplugd")
        cmd = f'pgrep -f ifplugd >/dev/null || echo "ifplugd demon not running"'
        self.terminal.runcmd(
            cmd=cmd, timeout=30, expected_failures=["ifplugd demon not running"]
        )
        self.ifupdown()
        cmd = f"ifconfig {self.eth_interface} {self.board_ip} netmask 255.255.255.0"
        self.terminal.runcmd(cmd=cmd, timeout=self.timeout)

    def eth_nfs(self):
        self.log.info("Output test files and clean up..")
        cmd_list = [
            "out_dir=/tmp/nfs_temp_output",
            "mkdir -p ${out_dir} > /dev/null 2>&1",
            "out_prefix=${out_dir}/nfs_test",
            "out_mount=${out_prefix}.mount",
            "out_mount_prefix=${out_mount}/nfs_test",
            "unmount ${out_mount} && rm -rf ${out_prefix}*",
        ]

        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=60)

        self.log.info("Mounting NFS...")
        cmd_list = [
            "mkdir -p ${out_mount}",
            f'rpcinfo "{self.client_ip}" | grep "nfs"',
            f"mount -o port=2049,nolock,proto=tcp,vers=2 {self.client_ip}:/exports/root $out_mount",
        ]
        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=200)

        self.log.info("Creating large pattern data files..")
        cmd_list = [
            " [ -c /dev/urandom ] || mknod -m 777 /dev/urandom c 1 9 > /dev/null 2>&1;",
            "dd if=/dev/urandom of=${out_prefix}.r2m-pattern.bin bs=1024 count=4096;",
            "dd if=/dev/urandom of=${out_mount_prefix}.m2r-pattern.bin bs=1024 count=4096;",
            "cp ${out_mount_prefix}.m2r-pattern.bin ${out_prefix}.m2r-pattern.bin;",
            "cp ${out_prefix}.r2m-pattern.bin ${out_mount_prefix}.r2m-pattern.bin;",
        ]

        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=200)
        self.log.info("Re-mounting the NFS.. Verifying the read back data...")
        cmd_list = [
            "umount ${out_mount};",
            f"mount -o port=2049,nolock,proto=tcp,vers=2 {self.client_ip}:/exports/root $out_mount;"
            "diff -q ${out_prefix}.m2r-pattern.bin ${out_mount_prefix}.m2r-pattern.bin",
            "diff -q ${out_mount_prefix}.r2m-pattern.bin ${out_prefix}.r2m-pattern.bin",
        ]
        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=200)

    def vlan_test(self):
        cmd = "board_mac=$(ifconfig eth0 | awk '/HWaddr/ {print substr($5,1)}')"
        self.terminal.runcmd(cmd=cmd, timeout=60)
        self.BoardMac = self.terminal.output()
        time.sleep(2)
        self.log.info(f"Board HWaddr : {self.BoardMac}... ")
        cmd = 'tcpdump -i {self.eth_interface} "vlan and icmp" and ip host 10.10.70.2 and ether host "$board_mac" -n -ev &'
        self.terminal.runcmd(cmd=cmd, timeout=60)
        time.sleep(2)
        cmd_list = [
            "ip link set dev eth2.5 down &",
            "ip link del eth2.5 &",
            "modprobe 8021q &",
            "ip link add link eth2 name eth2.5 type vlan id 5 &",
            "ip addr add 10.10.70.2 brd 10.10.70.255 dev eth2.5 &",
            "ip link set dev eth2.5 up &",
            f"arp -s {self.client_ip} $board_mac dev eth2.5 &",
            f"{self.client_ip} -I eth2.5 -c 3 &",
        ]
        self.get_client_console()
        self.client_console.runcmd(cmd=cmd_list, timeout=120)
        time.sleep(10)
        self.log.info("=================== rx output ===================")
        self.terminal.runcmd(cmd="killall -s INT tcpdump &", timeout=60)
        time.sleep(2)
        cmd_list = [
            "ip link set dev eth2.5 down &",
            "ip link del eth2.5 &",
            f"route del {self.client_ip} &",
            f"route add {self.client_ip} dev eth2 &",
            f"tcpdump -n -i eth2 dst port 9 and ip host {self.client_ip} -e -v > ~/tx_tcpdump_vlan.txt &",
        ]
        self.client_console.runcmd(cmd=cmd_list, timeout=120)
        time.sleep(10)
        self.client_console.runcmd(cmd="gettest_hostmac", timeout=20)
        time.sleep(1)
        commands = [
            "echo 'stop' > /proc/net/pktgen/pgctrl",
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_0",
            "echo 'add_device eth0' > /proc/net/pktgen/kpktgend_0",
            "echo 'count 1' > /proc/net/pktgen/eth0",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0",
            "echo 'pkt_size 200' > /proc/net/pktgen/eth0",
            "echo 'delay 0' > /proc/net/pktgen/eth0",
            "echo 'frags 4' > /proc/net/pktgen/eth0",
            "echo 'vlan_id 0' > /proc/net/pktgen/eth0",
            "echo 'vlan_p 0' > /proc/net/pktgen/eth0",
            "echo 'vlan_cfi 0' > /proc/net/pktgen/eth0",
            f"echo 'dst {self.board_ip}' > /proc/net/pktgen/eth0",
            f"echo 'dst_mac {self.client_mac}' > /proc/net/pktgen/eth0",
            "echo 'start' > /proc/net/pktgen/pgctrl",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(4)
        self.log.info("=================== tx output ===================")
        cmd_list = [
            "killall -s INT tcpdump &",
            "cat ~/tx_tcpdump_vlan.txt",
            "rm ~/tx_tcpdump_vlan.txt",
        ]
        self.client_console.runcmd(cmd=cmd_list, timeout=120)
        time.sleep(10)

    def update_mtu(self, **kwargs):
        self.get_client_console()
        self.log.info(f"Updating MTU size on host and device... : {self.mtu}")
        self.terminal.runcmd_list(
            cmd_list=[
                f"ifconfig {self.eth_interface} down",
                "sleep 10",
                f"ifconfig {self.eth_interface} mtu {self.mtu} {self.boardIp}  up",
                "sleep 5",
                "ifconfig",
            ]
        )
        time.sleep(5)
        self.client_console.runcmd_list(
            cmd_list=[
                f"sudo ifconfig {self.host_interface} down",
                "sleep 10",
                f"sudo ifconfig {self.host_interface} mtu {self.mtu} {self.clientIp} up",
                "sleep 5",
                "sudo ifconfig",
            ]
        )
        time.sleep(5)
        self.terminal.sync()

    def ping_jumbo_frame(self, **kwargs):
        self.get_client_console()
        for mtu in [1500, 2048, 4096, 8192]:
            self.log.info(f"Updating MTU size on device... : {mtu}")
            self.mtu = mtu
            self.update_mtu()
            self.terminal.sync()
            time.sleep(3)
            self.terminal.runcmd(
                cmd=f"ping {self.clientIp} -s {mtu-28} -c 5",
                timeout=30,
                expected=" 0% packet loss",
            )
            time.sleep(2)
        self.mtu = 1500
        self.update_mtu()

    def mii_test(self, **kwargs):
        self.terminal.runcmd(
            cmd=f"mii-tool -v {self.eth_interface}", expected="link ok"
        )
        self.terminal.runcmd(
            cmd=f"mii-tool --force 10baseT-FD {self.eth_interface}", expected=" "
        )
        self.terminal.runcmd(cmd=f"mii-tool {self.eth_interface}", expected=": 10 Mbit")
        self.terminal.runcmd(
            cmd=f"mii-tool --restart {self.eth_interface}", expected=" "
        )
        self.terminal.sync()
        time.sleep(10)
        self.ping_test()
        self.terminal.sync()

    def eth_pqueue(self):
        self.client_console.runcmd(cmd="gettest_hostmac", timeout=20)
        self.client_console.runcmd(cmd="killall -s INT tcpdump &", timeout=20)
        self.client_console.runcmd(cmd="rm ~/priority.txt &", timeout=20)
        self.client_console.runcmd(
            cmd=f"tcpdump -n -i {self.host_interface} ip host {self.board_ip} -ev > ~/priority.txt &",
            timeout=20,
        )
        time.sleep(5)
        self.log.info(f"targetMac = {self.client_mac}")
        commands = [
            "echo 'stop' > /proc/net/pktgen/pgctrl",
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_0",
            "echo 'add_device eth0@0' > /proc/net/pktgen/kpktgend_0",
            "echo 'count 500' > /proc/net/pktgen/eth0@0",
            "echo 'burst 50' > /proc/net/pktgen/eth0@0",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@0",
            "echo 'pkt_size 1500' > /proc/net/pktgen/eth0@0",
            "echo 'delay 0' > /proc/net/pktgen/eth0@0",
            "echo 'frags 0' > /proc/net/pktgen/eth0@0",
            f"echo 'dst {self.board_ip}' > /proc/net/pktgen/eth0@0",
            f"echo 'dst_mac {self.client_mac}' > /proc/net/pktgen/eth0@0",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@0",
            "echo 'queue_map_min 0' > /proc/net/pktgen/eth0@0",
            "echo 'queue_map_max 0' > /proc/net/pktgen/eth0@0",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        commands = [
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_1",
            "echo 'add_device eth0@1' > /proc/net/pktgen/kpktgend_1",
            "echo 'count 20' > /proc/net/pktgen/eth0@1",
            "echo 'burst 20' > /proc/net/pktgen/eth0@1",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@1",
            "echo 'pkt_size 1400' > /proc/net/pktgen/eth0@1",
            "echo 'delay 0' > /proc/net/pktgen/eth0@1",
            "echo 'frags 0' > /proc/net/pktgen/eth0@1",
            f"echo 'dst {self.board_ip}' > /proc/net/pktgen/eth0@1",
            f"echo 'dst_mac {self.client_mac}' > /proc/net/pktgen/eth0@1",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@1",
            "echo 'queue_map_min 1' > /proc/net/pktgen/eth0@1",
            "echo 'queue_map_max 1' > /proc/net/pktgen/eth0@1",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        commands = [
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_2",
            "echo 'add_device eth0@2' > /proc/net/pktgen/kpktgend_2",
            "echo 'count 500' > /proc/net/pktgen/eth0@2",
            "echo 'burst 50' > /proc/net/pktgen/eth0@2",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@2",
            "echo 'pkt_size 1200' > /proc/net/pktgen/eth0@2",
            "echo 'delay 0' > /proc/net/pktgen/eth0@2",
            "echo 'frags 0' > /proc/net/pktgen/eth0@2",
            f"echo 'dst {self.board_ip}' > /proc/net/pktgen/eth0@2",
            f"echo 'dst_mac {self.client_mac}' > /proc/net/pktgen/eth0@2",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@2",
            "echo 'queue_map_min 0' > /proc/net/pktgen/eth0@2",
            "echo 'queue_map_max 0' > /proc/net/pktgen/eth0@2",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        commands = [
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_3",
            "echo 'add_device eth0@3' > /proc/net/pktgen/kpktgend_3",
            "echo 'count 20' > /proc/net/pktgen/eth0@3",
            "echo 'burst 20' > /proc/net/pktgen/eth0@3",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@3",
            "echo 'pkt_size 1100' > /proc/net/pktgen/eth0@3",
            "echo 'delay 0' > /proc/net/pktgen/eth0@3",
            "echo 'frags 0' > /proc/net/pktgen/eth0@3",
            f"echo 'dst {self.board_ip}' > /proc/net/pktgen/eth0@3",
            f"echo 'dst_mac {self.client_mac}' > /proc/net/pktgen/eth0@3",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@3",
            "echo 'queue_map_min 1' > /proc/net/pktgen/eth0@3",
            "echo 'queue_map_max 1' > /proc/net/pktgen/eth0@3",
            "echo 'start' > /proc/net/pktgen/pgctrl &",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        self.client_console.runcmd(cmd="killall -s INT tcpdump &", timeout=20)
        self.client_console.runcmd(cmd="cat ~/priority.txt &", timeout=20)
