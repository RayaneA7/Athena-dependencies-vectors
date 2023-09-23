from __future__ import annotations

import copy
import itertools
from typing import TYPE_CHECKING, Dict, List, Tuple

from athena.tiramisu.tiramisu_iterator_node import IteratorIdentifier
from athena.tiramisu.tiramisu_tree import TiramisuTree

if TYPE_CHECKING:
    from athena.tiramisu.tiramisu_tree import TiramisuTree

from athena.tiramisu.tiramisu_actions.tiramisu_action import (
    TiramisuAction,
    TiramisuActionType,
)


class Unrolling(TiramisuAction):
    """
    Unrolling optimization command.
    """

    def __init__(
        self, params: List[IteratorIdentifier | int], comps: List[str] | None = None
    ):
        # Unrolling takes 2 parameters: the iterator to unroll and the unrolling factor
        assert len(params) == 2
        assert type(params[0]) is tuple and type(params[1]) is int
        self.iterator_id = params[0]
        self.unrolling_factor = params[1]

        self.params = params
        self.comps = comps

        super().__init__(type=TiramisuActionType.UNROLLING, params=params, comps=comps)

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        # clone the tree to be able to restore it later
        self.tree = copy.deepcopy(tiramisu_tree)

        if self.comps is None:
            iterator = tiramisu_tree.get_iterator_of_computation(*self.iterator_id)

            # Get the computations that are in the loop to be unrolled
            self.comps = tiramisu_tree.get_iterator_subtree_computations(iterator.name)
            # order the computations by their absolute order
            self.comps.sort(
                key=lambda comp: tiramisu_tree.computations_absolute_order[comp]
            )

        self.set_string_representations(tiramisu_tree)

    def set_string_representations(self, tiramisu_tree: TiramisuTree):
        assert self.iterator_id is not None
        assert self.unrolling_factor is not None
        assert self.comps is not None

        self.tiramisu_optim_str = ""
        loop_level = self.iterator_id[1]
        unrolling_factor = self.unrolling_factor
        # for comp in self.comps:
        self.tiramisu_optim_str = "\n    ".join(
            [f"{comp}.unroll({loop_level},{unrolling_factor});" for comp in self.comps]
        )
        self.str_representation = (
            f"U(L{str(loop_level)},{str(unrolling_factor)},comps={self.comps})"
        )

        self.legality_check_string = f"is_legal &= loop_unrolling_is_legal({loop_level}, {{{', '.join([f'&{comp}' for comp in self.comps])}}});\n    {self.tiramisu_optim_str}"

    @classmethod
    def get_candidates(cls, program_tree: TiramisuTree) -> List[str]:
        candidates: List[str] = []

        for iterator in program_tree.iterators:
            iterator_node = program_tree.iterators[iterator]
            if not iterator_node.child_iterators and iterator_node.computations_list:
                candidates.append(iterator)

        return candidates
