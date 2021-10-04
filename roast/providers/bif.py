#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from roast.providers.randomizer import Randomizer
from roast.utils import read_json
from box import Box


class BifProvider(Randomizer):
    """Class that contains bif file randomizer."""

    def __init__(self, randomize=True, *args, **kwargs) -> None:
        """Initialize attributes lazily.

        :param args: Arguments.
        :param kwargs: Keyword arguments.
        """
        super().__init__(randomize=randomize, *args, **kwargs)

    class Meta:
        name = "bif"

    def shuffle_sections(self, bif, constraints):
        if self.randomize:
            bif_random = tuple()
            blocks = {i: block.header.name for i, block in enumerate(bif)}
            blocks_mod = blocks.copy()

            # add locked blocks
            for b_index, name in blocks.items():
                if constraints.get(f"{name}.locked", False):
                    block = bif[b_index]
                    if bif_random:
                        bif_random = bif_random + (block,)
                    else:
                        bif_random = (block,)
                    del blocks_mod[b_index]
                    dependents = constraints.get(f"{name}.dependents", [])
                    for dependent in dependents:
                        d_index = list(blocks.keys())[
                            list(blocks.values()).index(dependent)
                        ]
                        bif_random = bif_random + (bif[d_index],)
                        del blocks_mod[d_index]

            blocks = blocks_mod.copy()

            # shuffle blocks
            keys = list(blocks_mod.items())
            self.random.shuffle(keys)
            blocks_mod = dict(keys)

            # add required blocks
            for b_index, name in blocks.items():
                if constraints.get(f"{name}.required", False):
                    block = bif[b_index]
                    self.random.shuffle(block.components)
                    if bif_random:
                        bif_random = bif_random + (block,)
                    else:
                        bif_random = (block,)
                    del blocks_mod[b_index]
                    dependents = constraints.get(f"{name}.dependents", [])
                    for dependent in dependents:
                        d_index = list(blocks.keys())[
                            list(blocks.values()).index(dependent)
                        ]
                        block = bif[d_index]
                        self.random.shuffle(block.components)
                        bif_random = bif_random + (block,)
                        del blocks_mod[d_index]

            blocks = blocks_mod.copy()

            # randomly select remaining blocks
            for b_index, name in blocks.items():
                if self.boolean():
                    block = bif[b_index]
                    self.random.shuffle(block.components)
                    if bif_random:
                        bif_random = bif_random + (block,)
                    else:
                        bif_random = (block,)
                    del blocks_mod[b_index]
                    dependents = constraints.get(f"{name}.dependents", [])
                    for dependent in dependents:
                        d_index = list(blocks.keys())[
                            list(blocks.values()).index(dependent)
                        ]
                        block = bif[d_index]
                        self.random.shuffle(block.components)
                        bif_random = bif_random + (block,)
                        del blocks_mod[d_index]
                else:
                    del blocks_mod[b_index]

            return bif_random
        else:
            return bif
