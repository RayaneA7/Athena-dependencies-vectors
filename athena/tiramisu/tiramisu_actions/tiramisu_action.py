from __future__ import annotations

from enum import Enum
from typing import List  # ,TYPE_CHECKING

from athena.tiramisu.tiramisu_tree import TiramisuTree

# if TYPE_CHECKING:


class TiramisuActionType(Enum):
    """The type of an optimization command."""

    INTERCHANGE = 0
    TILING_2D = 1
    PARALLELIZATION = 2
    SKEWING = 3
    UNROLLING = 4
    FUSION = 5
    REVERSAL = 6
    TILING_3D = 7
    DISTRIBUTION = 8
    EXPANSION = 9
    TILING_GENERAL = 10
    # WHENEVER YOU ADD AN ACTION GO EDIT THE NUMBER OF ACTIONS TEXT


class TiramisuAction:
    """
    Base class for all optimization commands.

    Attributes:
    ----------

    `type`: `TiramisuActionType`
        The type of the optimization command.

    `params`: `list`
        The parameters of the optimization command.

    `comps`: `list`
        The computations that are concerned by the optimization command.

    """

    def __init__(
        self,
        type: TiramisuActionType,
        params: list | dict,
        comps: List[str] | List[List[str]],
    ):
        self.params = params
        # A list of concerned computations of the actions
        self.comps = comps
        # The type of the action
        self.type = type
        # The tiramisu code that represents the action
        self.tiramisu_optim_str = ""
        # The str representation of the action
        self.str_representation = ""
        # The legality string of the action
        self.legality_check_string = ""

    def initialize_action_for_tree(self, tiramisu_tree: TiramisuTree):
        """Initialize the optimization command for the Tiramisu program."""
        raise NotImplementedError

    def set_string_representations(self, tiramisu_tree: TiramisuTree) -> str:
        """Convert the optimization command into Tiramisu code.
        Returns:
            str: The tiramisu snippet that represents the optimization command.
        """
        raise NotImplementedError

    def is_interchange(self) -> bool:
        return self.type == TiramisuActionType.INTERCHANGE

    def is_tiling_2d(self) -> bool:
        return self.type == TiramisuActionType.TILING_2D

    def is_tiling_3d(self) -> bool:
        return self.type == TiramisuActionType.TILING_3D

    def is_parallelization(self) -> bool:
        return self.type == TiramisuActionType.PARALLELIZATION

    def is_skewing(self) -> bool:
        return self.type == TiramisuActionType.SKEWING

    def is_unrolling(self) -> bool:
        return self.type == TiramisuActionType.UNROLLING

    def is_fusion(self) -> bool:
        return self.type == TiramisuActionType.FUSION

    def is_reversal(self) -> bool:
        return self.type == TiramisuActionType.REVERSAL

    def is_distribution(self) -> bool:
        return self.type == TiramisuActionType.DISTRIBUTION

    def is_tiling_general(self) -> bool:
        return self.type == TiramisuActionType.TILING_GENERAL

    @classmethod
    def get_candidates(cls, program_tree: TiramisuTree) -> list:
        raise NotImplementedError

    @classmethod
    def get_types(cls) -> List[TiramisuActionType]:
        return [e for e in TiramisuActionType]

    def __str__(self) -> str:
        return self.str_representation

    def __repr__(self) -> str:
        return f"Action(type={self.type}, params={self.params}, comps={self.comps})"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, TiramisuAction):
            return False
        return (
            self.type == __value.type
            and self.params == __value.params
            and self.comps == __value.comps
        )


class CannotApplyException(Exception):
    pass
