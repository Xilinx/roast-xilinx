#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.testlibs.linux.baselinux import BaseLinux
from roast.testlibs.linux.fileops import FileOps
import re


class Tpm2(BaseLinux, FileOps):
    """
    Trusted Platform Module is international standard for a secure cryptoprocessor
    a driver designed to secure hardware through integrated cryptographic keys.
    """

    def __init__(self, console, config):
        super().__init__(console, config)

    def isUp(self, cmd="tpm2"):
        """This Function is to check tpm2 binary"""
        self.is_bin_exist(cmd, silent_discard=False)

    def getcap(self, cmd="tpm2_getcap -l", expected_list=("algorithms", "pcrs")):
        """
        This function is to list all capabilities/properties and print them on console.
        Arguments:
            cmd {string} -- To print all properties/capabilities of tpm2
            expected_list {list} -- list of expected values from printed output.
        """
        self.console.runcmd(cmd, expected="\r\n")
        getcap_output = self.console.output()
        if not getcap_output:
            assert getcap_output, f"failed to read tpm2 getcap list"
        if not all(x in getcap_output for x in expected_list):
            assert False, f"failed to found all expected list from tpm2_getcap"

    def readcap(self):
        """This function to read each capability/property of tpm2"""
        self.getcap()
        cap_list = self.console.output().split("\n")
        cap_list = [re.sub(r"^\W+", "", i.strip()) for i in cap_list]
        for command in cap_list:
            self.console.runcmd(f"tpm2_getcap {command}")

    def random(self, data_bytes=30, iterations=10):
        """
        This function is to generate random hash key for each itteration.
        Arguments:
            data_bytes {int} -- To generate size of hash key in bytes
                                Ex: data_bytes=8, data_bytes=30 etc...
            iterations {int} -- number of itterations to generate random hash key
                                Ex: iterations=10, iterations=20 etc...
        """
        random_data, i = [], 1
        while i <= int(iterations):
            self.console.runcmd(
                cmd=f"tpm2_getrandom --hex {data_bytes}", expected="\r\n"
            )
            random_data.append(self.console.output())
            i += 1
        if not random_data:
            assert random_data, f"failed to generate value using tpm2_getrandom"
        matches = list(set([x for x in random_data if random_data.count(x) > 1]))
        if matches:
            assert False, f"failed to generate random data, match found:{matches}"

    def pcrread(self, hash_algorithm=1, pcr_banks=(0, 1, 2, 3, 4)):
        """
        This function is to read locked pcr banks.
        Arguments:
            hash_algorithm {int} -- Ex: 1 or 256
            pcr_banks {list} -- (0 to 16)
        """
        banks = ",".join(map(str, pcr_banks))
        self.console.runcmd(
            f"tpm2_pcrread sha{str(hash_algorithm)}:{banks}", expected="\r\n"
        )
        pcr_data = self.console.output().split("\n")
        pcr_data = [
            int(re.sub(".*: ", "", i.strip()), 16) for i in pcr_data if "0x" in i
        ]
        if len(pcr_data) != len(pcr_banks):
            assert False, f"failed to read all pcr_banks:{pcr_banks}"
        if not all(i == 0 for i in pcr_data):
            assert (
                False
            ), f"pcr banks buffer contains sha:{hash_algorithm} data: {pcr_data}"

    def hashcheck(self, hash_file, hashkey):
        """
        This function is to check hash key of fixed file.
        Arguments:
            hash_file {string} -- file which you want to check
            hashkey {string} -- hash key of file which you want to check
        """
        self.console.runcmd(cmd=f"tpm2_hash {hash_file} --hex", expected="\r\n")
        readkey = self.console.output().split("\n")[0]
        self.console.sync()
        if readkey != hashkey:
            assert False, f"failed to match hashkey for static file {hash_file}"

    def pcrextend(
        self,
        pcr_bank=23,
        hash_algorithm=1,
        sha_data="ac3478d69a3c81fa62e60f5c3696165a4e5e6ac4",
    ):
        """
        This function is to write sha data into unlocked pcr banks.
        Arguments:
            pcr_bank {int} -- unlocked pcr banks (17 to 23)
            hash_algorithm {int} -- 1 or 256
            sha_data {string} -- pass 20 bytes data for hash_algorithm 1, 32 bytes for 256
        """
        read_data, i = [], 1
        while i <= 3:
            self.console.runcmd(
                cmd=f"tpm2_pcrextend {pcr_bank}:sha{str(hash_algorithm)}={sha_data}",
                expected_failures=["ERROR: Algorithm"],
            )
            self.console.runcmd(
                f"tpm2_pcrread sha{str(hash_algorithm)}:{pcr_bank}", expected="\r\n"
            )
            read_data.append(
                re.sub(".*: ", "", self.console.output().split("\n")[-1].strip())
            )
            i += 1
        if not read_data:
            assert False, f"failed to read data from pcr_bank:{pcr_bank}"
        matches = list(set([x for x in read_data if read_data.count(x) > 1]))
        if matches:
            assert False, f"failed to extend data on pcr_bank:{pcr_bank}"

    def pcrreset(self, pcr_bank=23, hash_algorithm=1):
        """
        This function is to clear data in unlocked pcr banks.
        Arguments:
            pcr_bank {int} -- unlocked pcr banks (17 to 23)
            hash_algorithm {int} -- 1 or 256
        """
        self.console.runcmd(
            cmd=f"tpm2_pcrreset {pcr_bank}",
            expected_failures=[
                "bad locality",
                "ERROR: Could not reset PCR index",
                "ERROR: Unable to run tpm2_pcrreset",
            ],
        )
        self.console.runcmd(
            f"tpm2_pcrread sha{str(hash_algorithm)}:{pcr_bank}", expected="\r\n"
        )
        if (
            int(re.sub(".*: ", "", self.console.output().split("\n")[-1].strip()), 16)
            != 0
        ):
            assert False, f"failed to reset pcr_bank:{pcr_bank}"
