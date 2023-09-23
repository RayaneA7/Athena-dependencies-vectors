from __future__ import annotations

import copy
import itertools
from typing import TYPE_CHECKING, Dict, List, Tuple

from athena.tiramisu.tiramisu_iterator_node import IteratorIdentifier
from athena.tiramisu.tiramisu_tree import TiramisuTree

if TYPE_CHECKING:
    from athena.tiramisu.tiramisu_tree import TiramisuTree

from athena.tiramisu.tiramisu_actions.tiramisu_action import (
    CannotApplyException,
    TiramisuAction,
    TiramisuActionType,
)


class Fusion(TiramisuAction):
    """
    Fusion optimization command.
    """

    def __init__(self, params: List[IteratorIdentifier]):
        # Fusion takes 2 parameters the iterators to be fused
        assert len(params) == 2
        assert isinstance(params[0], tuple) and isinstance(params[1], tuple)
        # same level for both iterators
        assert params[0][1] == params[1][1]

        self.params = params
        self.comps: List[str] | None = None
        self.main_fusion_level = params[0][1]

        super().__init__(type=TiramisuActionType.FUSION, params=params, comps=None)

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        # clone the tree to be able to restore it later
        self.tree = copy.deepcopy(tiramisu_tree)

        self.comps = []
        for iterator_id in self.params:
            iterator = tiramisu_tree.get_iterator_of_computation(
                iterator_id[0], iterator_id[1]
            )
            self.comps.extend(
                tiramisu_tree.get_iterator_subtree_computations(iterator.name)
            )

        # sort the comps by the absolute order of the tree
        self.comps.sort(
            key=lambda comp: tiramisu_tree.computations_absolute_order[comp]
        )

        self.set_string_representations(tiramisu_tree)

    def set_string_representations(self, tiramisu_tree: TiramisuTree):
        assert self.comps is not None
        assert len(self.comps) > 1

        self.tiramisu_optim_str = ""

        (
            ordered_computations,
            fusion_levels,
        ) = self.reorder_computations(
            tiramisu_tree=tiramisu_tree,
        )

        first_comp = ordered_computations[0]

        self.tiramisu_optim_str += f"clear_implicit_function_sched_graph();\n    {first_comp}{''.join([f'.then({comp},{fusion_level})' for comp, fusion_level in zip(ordered_computations[1:], fusion_levels)])};\n"
        self.str_representation = f"F(L{self.params[0][1]},comps={self.comps})"

        self.legality_check_string = self.tiramisu_optim_str

    @classmethod
    def get_candidates(cls, program_tree: TiramisuTree) -> List[Tuple[str, str]]:
        # We will try to fuse all possible nodes that have the same level
        candidates: List[Tuple[str, str]] = []

        #  Check if roots are fusionable
        if len(program_tree.roots) > 1:
            # get all the possible combinations of 2 of roots
            candidates.extend(itertools.combinations(program_tree.roots, 2))

        # Check the different levels of the iterators
        levels = set([iterator.level for iterator in program_tree.iterators.values()])

        # For each level, we will try to fuse all possible nodes that have the same level and have the same root
        for level in levels:
            # get all iterator nodes that have the same level
            iterators = [
                iterator
                for iterator in program_tree.iterators.values()
                if iterator.level == level
            ]

            # filter the iterators that have the same root into dict
            iterators_dict: Dict[str, List[str]] = {}
            for root in program_tree.roots:
                iterators_dict[root] = []
            for iterator in iterators:
                iterators_dict[program_tree.get_root_of_node(iterator.name)].append(
                    iterator.name
                )
            for root in iterators_dict:
                candidates.extend(itertools.combinations(iterators_dict[root], 2))

        return candidates

    def reorder_computations(
        self,
        tiramisu_tree: TiramisuTree,
    ):
        assert self.comps is not None
        assert len(self.comps) > 1
        assert self.main_fusion_level is not None
        assert isinstance(self.main_fusion_level, int)

        fused_computations = self.comps
        main_fusion_level = self.main_fusion_level

        new_absolute_order = tiramisu_tree.computations_absolute_order.copy()
        fused_in_iterator = tiramisu_tree.get_iterator_of_computation(
            fused_computations[0], self.main_fusion_level
        )
        comps_in_fused_iterator = tiramisu_tree.get_iterator_subtree_computations(
            fused_in_iterator.name
        )
        max_order = max(
            [
                tiramisu_tree.computations_absolute_order[comp]
                for comp in comps_in_fused_iterator
            ]
        )
        fusion_comps_to_move = [
            comp
            for comp in fused_computations
            if tiramisu_tree.computations_absolute_order[comp] > max_order
        ]

        # move the computations that are after the fused iterator and not included in fusion
        for comp in tiramisu_tree.computations_absolute_order:
            if (
                tiramisu_tree.computations_absolute_order[comp] > max_order
                and comp not in fused_computations
            ):
                new_absolute_order[comp] += len(fusion_comps_to_move)
        # move the computations that are in the fused iterator
        for index, comp in enumerate(fusion_comps_to_move):
            new_absolute_order[comp] = max_order + index + 1

        computations = tiramisu_tree.computations
        computations.sort(key=lambda x: new_absolute_order[x])

        fusion_levels: List[int] = []
        # for every pair of successive computations get the shared iterator level
        for comp1, comp2 in itertools.pairwise(computations):
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

            if comp1 in fused_computations and comp2 in fused_computations:
                if fusion_level <= main_fusion_level:
                    fusion_level = main_fusion_level

            fusion_levels.append(fusion_level)

        return computations, fusion_levels
