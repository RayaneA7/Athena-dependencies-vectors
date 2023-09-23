from __future__ import annotations

import copy
import itertools
import os
from typing import TYPE_CHECKING, Dict, List, Tuple

from athena.tiramisu.compiling_service import CompilingService
from athena.tiramisu.tiramisu_tree import TiramisuTree
from athena.utils.config import BaseConfig

if TYPE_CHECKING:
    from athena.tiramisu.tiramisu_tree import TiramisuTree
    from athena.tiramisu.schedule import Schedule

from athena.tiramisu.tiramisu_actions.tiramisu_action import (
    CannotApplyException,
    TiramisuAction,
    TiramisuActionType,
)


class Expansion(TiramisuAction):
    """
    Expansion optimization command.
    """

    def __init__(self, params: List[str]):
        # Expansion takes as a parameter the computation to expand
        assert len(params) == 1
        assert isinstance(params[0], str)
        self.computation = params[0]

        super().__init__(type=TiramisuActionType.EXPANSION, params=params, comps=None)

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        # clone the tree to be able to restore it later
        self.tree = copy.deepcopy(tiramisu_tree)

        self.set_string_representations(tiramisu_tree)

    def set_string_representations(self, tiramisu_tree: TiramisuTree):
        assert self.computation is not None

        self.tiramisu_optim_str = ""

        self.tiramisu_optim_str += f"{self.computation}.expand(true);\n"
        self.str_representation = f"E(comps={[self.computation]})"

        self.legality_check_string = self.tiramisu_optim_str

    @classmethod
    def get_candidates(cls, schedule: Schedule) -> List[str]:
        candidates = []
        candidates_code = ""

        for optim in schedule.optims_list:
            candidates_code += "    " + optim.tiramisu_optim_str

        for comp in schedule.tree.computations:
            candidates_code += (
                f'    std::cout << "{comp}|" << {comp}.expandable() << std::endl;\n'
            )

        cpp_code = schedule.tiramisu_program.original_str.replace(
            schedule.tiramisu_program.code_gen_line, candidates_code
        )

        output_path = os.path.join(
            BaseConfig.base_config.workspace,
            f"{schedule.tiramisu_program.name}_expansion_candidates",
        )

        candidates_results_str = CompilingService.run_cpp_code(
            cpp_code=cpp_code, output_path=output_path
        )
        for str_line in candidates_results_str.split("\n"):
            if str_line:
                computation_name, is_expandable = str_line.split("|")
                if is_expandable == "1":
                    candidates.append(computation_name)
        return candidates
