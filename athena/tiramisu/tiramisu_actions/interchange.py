from __future__ import annotations

import copy
import itertools
import re
from typing import TYPE_CHECKING, Dict, List, Tuple

from athena.tiramisu.tiramisu_iterator_node import IteratorIdentifier
from athena.tiramisu.tiramisu_tree import TiramisuTree

if TYPE_CHECKING:
    from athena.tiramisu.tiramisu_tree import TiramisuTree

from athena.tiramisu.tiramisu_actions.tiramisu_action import (
    TiramisuAction,
    TiramisuActionType,
)


class Interchange(TiramisuAction):
    """
    Interchange optimization command.
    """

    def __init__(
        self, params: List[IteratorIdentifier], comps: List[str] | None = None
    ):
        # Interchange takes 2 iterators to interchange as parameters
        assert len(params) == 2

        self.params = params
        self.comps = comps

        super().__init__(
            type=TiramisuActionType.INTERCHANGE, params=params, comps=comps
        )

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        self.tree = copy.deepcopy(tiramisu_tree)

        # if comps are none get them from the tree
        if self.comps is None:
            innermost_iterator_id = (
                self.params[1]
                if self.params[1][1] > self.params[0][1]
                else self.params[0]
            )
            innermost_iterator = self.tree.get_iterator_of_computation(
                innermost_iterator_id[0], innermost_iterator_id[1]
            )

            self.comps = self.tree.get_iterator_subtree_computations(
                innermost_iterator.name
            )

        self.set_string_representations(self.tree)

    def set_string_representations(self, tiramisu_tree: TiramisuTree):
        assert self.comps is not None
        assert len(self.params) == 2

        self.tiramisu_optim_str = ""
        levels = [param[1] for param in self.params]
        for comp in self.comps:
            self.tiramisu_optim_str += f"{comp}.interchange({levels[0]},{levels[1]});\n"
        self.str_representation = f"I(L{levels[0]},L{levels[1]},comps={self.comps})"

        self.legality_check_string = self.tiramisu_optim_str

    @classmethod
    def get_candidates(
        cls, program_tree: TiramisuTree
    ) -> Dict[str, List[Tuple[str, str]]]:
        candidates: Dict[str, List[Tuple[str, str]]] = {}

        candidate_sections = program_tree.get_candidate_sections()

        for root in candidate_sections:
            candidates[root] = []
            for section in candidate_sections[root]:
                # Only consider sections with more than one iterator
                if len(section) > 1:
                    # Get all possible combinations of 2 iterators
                    candidates[root].extend(list(itertools.combinations(section, 2)))

        return candidates
