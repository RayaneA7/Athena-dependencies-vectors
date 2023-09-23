from __future__ import annotations

import copy
import itertools
from typing import TYPE_CHECKING, Dict, List, Tuple

from athena.tiramisu.tiramisu_iterator_node import IteratorIdentifier, IteratorNode
from athena.tiramisu.tiramisu_tree import TiramisuTree

if TYPE_CHECKING:
    from athena.tiramisu.tiramisu_tree import TiramisuTree

from athena.tiramisu.tiramisu_actions.tiramisu_action import (
    CannotApplyException,
    TiramisuAction,
    TiramisuActionType,
)


class Distribution(TiramisuAction):
    """
    Distribution optimization command.
    """

    def __init__(
        self,
        params: List[IteratorIdentifier],
        children: List[List[IteratorIdentifier | str]] | None = None,
    ):
        # Distribution takes 1 parameters the iterator to be distributed
        assert len(params) == 1
        assert isinstance(params[0], tuple)

        self.iterator_id = params[0]

        self.children = children
        super().__init__(
            type=TiramisuActionType.DISTRIBUTION, params=params, comps=children
        )

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        # clone the tree to be able to restore it later
        self.tree = copy.deepcopy(tiramisu_tree)

        if self.children is None:
            self.children = []
            iterator = tiramisu_tree.get_iterator_of_computation(*self.iterator_id)
            # For each iterator get its comps and add them
            for child_iterator in iterator.child_iterators:
                child_iterator_comps = tiramisu_tree.get_iterator_subtree_computations(
                    child_iterator
                )
                self.children.append(child_iterator_comps)
            # Add the computation of the iterator itself
            for comp in iterator.computations_list:
                self.children.append([comp])
        else:
            for child_list in self.children:
                for index, child in enumerate(child_list):
                    # convert an iterator into its comps
                    if isinstance(child, tuple):
                        tmp_iterator = tiramisu_tree.get_iterator_of_computation(*child)
                        tmp_iterator_comps = (
                            tiramisu_tree.get_iterator_subtree_computations(
                                tmp_iterator.name
                            )
                        )
                        child_list.pop(index)
                        child_list.extend(tmp_iterator_comps)

        self.set_string_representations(tiramisu_tree)

    def set_string_representations(self, tiramisu_tree: TiramisuTree):
        self.tiramisu_optim_str = ""

        ordered_computations = tiramisu_tree.computations
        ordered_computations.sort(
            key=lambda x: tiramisu_tree.computations_absolute_order[x]
        )

        fusion_levels = self.get_fusion_levels(
            ordered_computations=ordered_computations, tiramisu_tree=tiramisu_tree
        )

        first_comp = ordered_computations[0]
        self.tiramisu_optim_str += f"clear_implicit_function_sched_graph();\n    {first_comp}{''.join([f'.then({comp},{fusion_level})' for comp, fusion_level in zip(ordered_computations[1:], fusion_levels)])};\n"
        self.str_representation = f"D(L{self.iterator_id[1]},comps=[{self.iterator_id[0]}],distribution={self.children})"

        self.legality_check_string = self.tiramisu_optim_str

    @classmethod
    def get_candidates(cls, program_tree: TiramisuTree) -> List[str]:
        # We will try to distribute all the iterators with more than one computation
        candidates: List[str] = []

        for iterator in program_tree.iterators.values():
            if len(iterator.computations_list) + len(iterator.child_iterators) > 1:
                candidates.append(iterator.name)

        return candidates

    def get_fusion_levels(
        self,
        ordered_computations: List[str],
        tiramisu_tree: TiramisuTree,
    ):
        assert self.children is not None

        distributed_iterator = tiramisu_tree.get_iterator_of_computation(
            *self.iterator_id
        )

        fusion_levels: List[int] = []
        # for every pair of successive computations get the shared iterator level
        for comp1, comp2 in itertools.pairwise(ordered_computations):
            # get the shared iterator level
            iter_comp_1 = tiramisu_tree.get_iterator_of_computation(comp1)
            iter_comp_2 = tiramisu_tree.get_iterator_of_computation(comp2)
            fusion_level: int | None = None

            # get the shared iterator level
            while iter_comp_1.name != iter_comp_2.name:
                if iter_comp_1.level > iter_comp_2.level:
                    # if parent is None then the iterators don't have a common parent
                    if iter_comp_1.parent_iterator is None:
                        fusion_level = -1
                        break
                    else:
                        iter_comp_1 = tiramisu_tree.iterators[
                            iter_comp_1.parent_iterator
                        ]
                else:
                    if iter_comp_2.parent_iterator is None:
                        fusion_level = -1
                        break
                    else:
                        iter_comp_2 = tiramisu_tree.iterators[
                            iter_comp_2.parent_iterator
                        ]

            # same iterator
            if fusion_level is None:
                fusion_level = iter_comp_1.level

            if (
                fusion_level == distributed_iterator.level
                and iter_comp_1.name == distributed_iterator.name
            ):
                no_distribution = False
                for child_list in self.children:
                    if comp1 in child_list and comp2 in child_list:
                        no_distribution = True
                        break

                if not no_distribution:
                    fusion_level -= 1

            fusion_levels.append(fusion_level)

        return fusion_levels
