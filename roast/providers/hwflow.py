#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import os
import inspect
import pkgutil
from mimesis import BaseDataProvider
import roast
from box import Box
from roast.providers.randomizer import Randomizer
from roast.utils import read_json


class HWFlowProvider(BaseDataProvider):
    def __init__(self, seed, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.seed = seed
        self.r = Randomizer(seed=self.seed)

    class Meta:
        name = "hwflow_provider"

    @property
    def parameter_file(self):
        return self._parameter_file

    @parameter_file.setter
    def parameter_file(self, file):
        providers_dir = os.path.dirname(inspect.getsourcefile(roast.providers.hwflow))
        self._parameter_file = os.path.join(providers_dir, file)
        _parameters = read_json(self._parameter_file)
        self.parameters = Box(_parameters, box_dots=True)

    def pick_parameter_value(self, parameter):
        parameter_choices = self.parameters[parameter]
        return self.r.choice(parameter_choices)
