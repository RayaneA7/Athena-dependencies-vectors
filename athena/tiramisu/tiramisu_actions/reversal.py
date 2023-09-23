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


class Reversal(TiramisuAction):
    """
    Reversal optimization command.
    """

    def __init__(
        self, params: List[IteratorIdentifier], comps: List[str] | None = None
    ):
        # Reversal takes one parameter of the loop to reverse
        assert len(params) == 1

        self.iterator_id = params[0]
        self.params = params
        self.comps = comps
        super().__init__(type=TiramisuActionType.REVERSAL, params=params, comps=comps)

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        # clone the tree to be able to restore it later
        self.tree = copy.deepcopy(tiramisu_tree)

        if self.comps is None:
            iterator = tiramisu_tree.get_iterator_of_computation(
                self.iterator_id[0], self.iterator_id[1]
            )

            self.comps = tiramisu_tree.get_iterator_subtree_computations(iterator.name)
            # order the computations by their absolute order
            self.comps.sort(
                key=lambda comp: tiramisu_tree.computations_absolute_order[comp]
            )

        self.set_string_representations(tiramisu_tree)

    def set_string_representations(self, tiramisu_tree: TiramisuTree):
        assert self.iterator_id is not None
        assert self.comps is not None

        self.tiramisu_optim_str = ""
        level = self.iterator_id[1]
        for comp in self.comps:
            self.tiramisu_optim_str += f"{comp}.loop_reversal({level});\n"

        self.str_representation = f"R(L{level},comps={self.comps})"

        self.legality_check_string = self.tiramisu_optim_str

    @classmethod
    def get_candidates(cls, program_tree: TiramisuTree) -> Dict[str, List[str]]:
        candidates: Dict[str, List[str]] = {}
        for root in program_tree.roots:
            candidates[root] = [root] + program_tree.iterators[root].child_iterators
            nodes_to_visit = program_tree.iterators[root].child_iterators.copy()

            while nodes_to_visit:
                node = nodes_to_visit.pop(0)
                node_children = program_tree.iterators[node].child_iterators
                nodes_to_visit.extend(node_children)
                candidates[root].extend(node_children)

        return candidates

    def transform_tree(self, program_tree: TiramisuTree):
        node = program_tree.iterators[self.params[0]]

        # Reverse the loop bounds
        if type(node.lower_bound) == int and type(node.upper_bound) == int:
            # Halide way of reversing to keep increment 1
            node.lower_bound, node.upper_bound = -node.upper_bound, -node.lower_bound
        else:
            node.lower_bound, node.upper_bound = node.upper_bound, node.lower_bound
