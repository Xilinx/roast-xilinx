#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import pytest
from roast.providers.bif import BifProvider
from roast.confParser import generate_conf
from roast.component.bif.generate import Block, Header, Component


@pytest.fixture
def b():
    def _b(seed=12345, randomize=True):
        b_rand = BifProvider(seed=seed, randomize=randomize)
        return b_rand

    return _b


def reconstruct_bif(bif):
    named_bif = tuple()
    headers, l_components = zip(*bif)
    for header, components in zip(headers, l_components):
        # config library returns list so cast back to namedtuple
        header = Header(*header)
        components = [Component(*component) for component in components]
        named_bif = named_bif + (Block(header, components),)
    return named_bif


def test_bif_shuffle(b):
    config = generate_conf()
    bif = reconstruct_bif(config["bif"])
    bpro = b(seed=1234589)
    bif_shuffled = bpro.shuffle_sections(bif, config.get("block_constraints", {}))
    assert bif_shuffled == reconstruct_bif(config["bif_shuffled"])


def test_bif_shuffle_no_randomization(b):
    config = generate_conf()
    bif = reconstruct_bif(config["bif"])
    bpro = b(randomize=False)
    bif_shuffled = bpro.shuffle_sections(bif, config.get("block_constraints", {}))
    assert bif == bif_shuffled
