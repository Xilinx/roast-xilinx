#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import math
import logging
from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps

log = logging.getLogger(__name__)


class Benchmark(BaseLinux, FileOps):
    """This benchmark class contains test library api's for all benchmark test cases"""

    def __init__(self, console, config):
        super().__init__(console, config)

    def linpack(self, cmd, arraysize, quit_cmd, timeout):
        """This function executes linpack command,

        Parameters:
        cmd       : Linpack command to execute
        arraysize : Array size to test
        quit_cmd  : Quit command
        timeout   : Timeout for executing that command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(cmd, expected="Enter array size", wait_for_prompt=False)
        self.console.runcmd(
            f"{arraysize}",
            expected="Enter array size",
            wait_for_prompt=False,
            timeout=timeout,
        )
        self.console.runcmd(quit_cmd)

    def dhrystone(self, cmd, number_runs, timeout):
        """This function executes dhrystone command,

        Parameters:
        cmd         : dhrystone command
        number_runs : Number of runs through benchmark
        timeout     : Timeout for executing that command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(cmd, expected="benchmark:", wait_for_prompt=False)
        self.console.runcmd(
            f"{number_runs}",
            timeout=timeout,
        )

    def whetstone(self, cmd, duration, timeout):
        """This function executes whetstone command,

        Parameters:
        cmd         : whetstone command
        duration    : duration through benchmark
        timeout     : Timeout for executing that command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} {duration}", timeout=timeout)

    def w_test(self, cmd, user):
        """This function executes w command,

        Parameters:
        cmd  : w_test command to exeute
        user : user name to validate
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} | grep {user}")

    def top_test(self, cmd):
        """This function executes top command,

        Parameters:
        cmd         : top_test command to execute
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -n 1 | grep -w init")

    def vm_stat(self, cmd):
        """This function executes vmstat command on target and
        compares free memory from command and meminfo file,

        Parameters:
        cmd         : vmstat command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd}")
        free_mem_cmd = self.console.output().split()[27]
        self.console.runcmd("cat /proc/meminfo | grep -w '[M]emFree'")
        free_mem_file = self.console.output().split()[7]
        diff = abs(int(free_mem_cmd) - int(free_mem_file))
        if diff > 5000:
            assert False, "free memory difference is greater than 5000 kb"

    def bw_mem(self, cmd, size, operation):
        """This function executes time memory bandwidth with
        different operations like rd, wr, cp etc.

        Parameters:
        cmd         : time memory bandwidth command
        size        : Memory size
        operation   : Operation to perform like rd, wr etc.
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} {size} {operation}")

    def benchmark_cmd_exec(self, cmd):
        """This function executes benchmark command,

        Parameters:
        cmd         : benchmark command to execute
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd}")

    def benchmark_cmd_oper_exec(self, cmd, operation):
        """This function executes benchmark command with operation,

        Parameters:
        cmd         : benchmark command to execute
        operation   : Operation to perform
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} {operation}")

    def lat_ctx(self, cmd, mem_size, number_pros):
        """This function executes context switching
        benchmark command,

        Parameters:
        cmd         : lat_ctx command to execute
        mem_size    : Memory size
        number_pros : Number of processes
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -s {mem_size} processes {number_pros}")

    def lat_dram_page(self, cmd, mem_size, timeout):
        """This function executes DRAM page latency command,

        Parameters:
        cmd         : DRAM page latency command to execute
        mem_size    : Memory size
        timeout     : Timeout for executing the command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -M {mem_size}", timeout=timeout)

    def lat_mem_rd(self, cmd, mem_size):
        """This function executes memory read latency command,

        Parameters:
        cmd         : Memory read latency command to execute
        mem_size    : Memory size
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} {mem_size}")

    def lat_pagefault(self, cmd, filename):
        """This function finds page fault latency
        of a file,

        Parameters:
        cmd         : Page fault command to execute
        filename    : On file to run command(optional)
        """
        self.is_bin_exist(cmd, silent_discard=False)
        if not self.is_file_exist(filename):
            filename = "test.jpg"
            self.createfile(filename, 100000, 256)
            self.console.runcmd(f"{cmd} {filename}")
            self.console.runcmd(f"rm {filename}")
        else:
            self.console.runcmd(f"{cmd} {filename}")

    def lat_sig_prot(self, cmd, filename):
        """This function finds protection fault latency
        of a file,

        Parameters:
        cmd         : protection fault latency command to execute
        filename    : On file to run command(optional)
        """
        self.is_bin_exist(cmd, silent_discard=False)
        if not self.is_file_exist(filename):
            filename = "test.pdf"
            self.createfile(filename, 1, 256)
            self.console.runcmd(f"{cmd} prot {filename}")
            self.console.runcmd(f"rm {filename}")
        else:
            self.console.runcmd(f"{cmd} prot {filename}")

    def lat_syscall(self, cmd, filename, operations):
        """This function executes lantency of system calls commands
        on,

        Parameters:
        cmd         : system calls latency command to execute
        filename    : On file to run command(optional)
        operations  : Operations to perform
        """
        self.is_bin_exist(cmd, silent_discard=False)
        if not self.is_file_exist(filename):
            filename = "test.pdf"
            self.createfile(filename, 1, 256)
            for operation in operations:
                self.console.runcmd(f"{cmd} {operation} {filename}")
            self.console.runcmd(f"rm {filename}")
        else:
            for operation in operations:
                self.console.runcmd(f"{cmd} {operation} {filename}")

    def lat_usleep(self, cmd, operation, time, timeout):
        """This function finds latency of usleep with different
        operations,

        Parameters:
        cmd         : latency usleep command to execute
        operation   : Operation to perform
        time        : time for sleep
        timeout     : Timeout for executing the command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        if not time:
            self.console.runcmd(f"{cmd} {operation}", timeout=timeout)
        else:
            self.console.runcmd(f"{cmd} -u {operation} {time}", timeout=timeout)

    def cache(self, cmd, mem_size):
        """This function executes cache command with specific
        memory size,

        Parameters:
        cmd         : cache command to execute
        mem_size    : memory size
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -M {mem_size}")

    def msleep(self, cmd, time):
        """This function executes msleep command,

        Parameters:
        cmd         : msleep command to execute
        time        : time for sleep
        """
        self.is_bin_exist(cmd, silent_discard=False)
        if time:
            self.console.runcmd(f"{cmd} {time}")
        else:
            self.console.exit_nzero_ret = False
            self.console.runcmd(f"{cmd}", expected="Segmentation fault")
            self.console.exit_nzero_ret = True

    def par_mem(self, cmd, mem_size):
        """This function par_mem measures the available parallelism
        in the memory hierarchy,

        Parameters:
        cmd         : msleep command to execute
        mem_size    : memory size
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -M {mem_size}")

    def stream(self, cmd, mem_size):
        """This function stream command with memory size,

        Parameters:
        cmd         : stream command to execute
        mem_size    : memory size
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -M {mem_size}")

    def tlb(self, cmd, mem_size):
        """This function measures tlb performance of memory size,

        Parameters:
        cmd         : tlb command to execute
        mem_size    : memory size
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -M {mem_size}")

    def iotop(self, cmd, device, bs_size, count):
        """This function executes input/output top commands,

        Parameters:
        cmd         : input/output top command to execute
        device      : device on which dd command should execute
        bs_size     : block size
        count       : count
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.runcmd(f"{cmd} -oq -n 1")
        self.console.runcmd(
            f"dd if={device} of=/dev/null bs={bs_size} count={count} & sleep 5"
        )
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} -oq -n 1")
        total_disk_read = round(int(float(self.console.output().split()[7])))
        pid = self.console.output().split()[36]
        self.console.exit_nzero_ret = True
        self.console.runcmd(f"kill -9 {pid}")
        if total_disk_read != 0:
            log.info(f"Total disk_read rate for system: {total_disk_read} M/s")
            assert True
        else:
            assert False, "Total disk_read for system is zero"

    def mpstat(self, cmd, device, bs_size, count):
        """This function executes mpstat commands,

        Parameters:
        cmd         : mpstat command to execute
        device      : device on which dd command should execute
        bs_size     : block size
        count       : count
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd}")
        idle1 = float(self.console.output().split()[-1])
        idle1_fract, idle1_dec = math.modf(idle1)
        log.info(f"{idle1} cpu is idle")
        self.console.exit_nzero_ret = True
        self.console.runcmd(
            f"dd if={device} of=/dev/null bs={bs_size} count={count} & sleep 20"
        )
        log.info("mpstat output after starting io")
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd}")
        idle2 = float(self.console.output().split()[-1])
        idle2_fract, idle2_dec = math.modf(idle2)

        log.info(f"{idle2} cpu is idle")
        log.info(f"cpu idle percentage, without IO activity in the system: {idle1}")
        log.info(
            f"cpu idle percentage, with IO activity executing on {device}: {idle2}"
        )
        self.console.exit_nzero_ret = True

        if idle1_dec >= idle2_dec:
            if idle1_dec == idle2_dec:
                if idle1_fract >= idle2_fract:
                    assert True, "TEST PASS:mpstat"
                else:
                    assert False, "TEST FAIL:mpstat"
            else:
                assert True, "TEST PASS:mpstat"
        else:
            assert False, "TEST FAIL:mpstat"

    def swap(self, swap_device):
        """This function executes input/output top commands,

        Parameters:
        swap_device : device on which swap command will run
        """
        self.console.runcmd("cat /proc/meminfo")
        self.console.runcmd(f"mkswap {swap_device}")
        log.info("/proc/meminfo After swithing turning swap ON")
        self.console.runcmd(f"swapon {swap_device}")
        self.console.exit_nzero_ret = False
        self.console.runcmd("cat /proc/meminfo | grep SwapTotal")
        swap_total = int(self.console.output().split()[6])
        if swap_total == 0:
            assert False, "Total swap is zero. Swap test is failed"
        else:
            log.info("swap created sucessfully")
        self.console.exit_nzero_ret = True
        self.console.runcmd(f"swapoff {swap_device}")
        self.console.exit_nzero_ret = False
        self.console.runcmd("cat /proc/meminfo | grep SwapTotal")
        swap_total = int(self.console.output().split()[6])
        if swap_total == 0:
            log.info("swap turned OFF sucessfully")
            assert True
        else:
            assert False, "Swap test failed"

    def slabtop(self, cmd):
        """This function executes slab top command,
        Parameters:
        cmd : slab top command
        """
        self.is_bin_exist(cmd, silent_discard=False)
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} -o | grep -w 'kmalloc-256'")
        slabobj1 = int(self.console.output().split()[6])
        log.info("Slab info from /proc/slabinfo file")
        self.console.runcmd("cat /proc/slabinfo | grep -w '^kmalloc-256'")
        slabobj2 = int(self.console.output().split()[8])
        log.info(f"slab objects allocated to kmalloc-256: {slabobj2}")
        if slabobj1 == slabobj2:
            log.info("TEST PASS:slabtop_test")
            assert True
        else:
            assert False, "TEST FAIL:slabtop_test"

    def sar(self, cmd, interval, iterations, device, bs_size, count):
        """This function executes sar cmmand to monitor
        system performance,

        Parameters:
        cmd        : sar command to execute
        interval   : interval
        iterations : iterations to run
        device     : device
        bs_size    : block size
        count      : count
        """
        self.is_bin_exist(cmd, silent_discard=False)
        log.info("cpu statics before starting IO on SD")

        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} {interval} {iterations}")
        usage = self.console.output().split()[-3]
        log.info(f"CPU usage for IO is {usage} percent")

        log.info("cpu statics after starting IO on SD")
        self.console.exit_nzero_ret = True
        self.console.runcmd(f"dd if={device} of=/dev/null bs={bs_size} count={count} &")
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} {interval} {iterations}")
        usage = self.console.output().split()[-3]
        log.info(f"CPU usage for IO is {usage} percent")
        if usage == 0:
            assert False, "TEST FAIL: cpu usage is zero"

        self.console.runcmd("ps | grep -w '[d]d'")
        pid = self.console.output().split()[-4]
        self.console.exit_nzero_ret = True
        self.console.runcmd(f"kill -9 {pid}")

        log.info(f"DISK IO stats before starting IO on {device}")
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} -b {interval} {iterations}")

        rtps = self.console.output().split()[-6]
        wtps = self.console.output().split()[-5]
        bread = self.console.output().split()[-3]
        bwrtn = self.console.output().split()[-2]

        log.info(f"Read transactions per second: {rtps}")
        log.info(f"Write transactions  per second: {wtps}")
        log.info(f"Bytes read per second: {bread}")
        log.info(f"Bytes written per second: {bwrtn}")

        self.console.runcmd("dd if=/dev/zero of=file.out bs=1M count=500")

        log.info("Disk IO stats After starting IO on SD")
        self.console.exit_nzero_ret = True
        self.console.runcmd(f"dd if={device} of=/dev/null bs={bs_size} count={count} &")
        log.info("Stats for Read IO")
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} -b {interval} {iterations}")

        rtps = self.console.output().split()[-6]
        bread = self.console.output().split()[-3]

        self.console.runcmd("ps | grep -w '[d]d'")
        pid = self.console.output().split()[-4]
        self.console.runcmd(f"kill -9 {pid}")

        self.console.exit_nzero_ret = True
        self.console.runcmd(f"dd if=file.out of={device} bs=1M count=500 &")
        log.info("Stats for Write IO")
        self.console.exit_nzero_ret = False
        self.console.runcmd(f"{cmd} -b {interval} {iterations}")

        wtps = self.console.output().split()[-12]
        bwrtn = self.console.output().split()[-9]

        self.console.exit_nzero_ret = True
        log.info(f"Disk IO stats After starting IO on {device}")
        log.info(f"Read transactions per second: {rtps}")
        log.info(f"Write transactions  per second: {wtps}")
        log.info(f"Bytes read per second: {bread}")
        log.info(f"Bytes written per second: {bwrtn}")

        self.console.runcmd("rm -rf file.out")
        if rtps == 0 or wtps == 0:
            assert False, "TEST FAIL:sar_test"
