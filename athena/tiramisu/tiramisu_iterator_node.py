from typing import List, Tuple

IteratorIdentifier = Tuple[str, int]


class IteratorNode:
    def __init__(
        self,
        name: str,
        parent_iterator: str | None,
        lower_bound: int | str,
        upper_bound: int | str,
        child_iterators: List[str],
        computations_list: List[str],
        level: int,
    ):
        self.name = name
        self.parent_iterator = parent_iterator
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.child_iterators = child_iterators
        self.computations_list = computations_list
        self.level = level

    def add_child(self, child: str) -> None:
        self.child_iterators.append(child)

    def add_computation(self, comp: str) -> None:
        self.computations_list.append(comp)

    def has_non_rectangular(self) -> bool:
        return (type(self.lower_bound) is str or type(self.upper_bound) is str) and (
            self.lower_bound != "UNK" and self.upper_bound != "UNK"
        )

    def has_unkown_bounds(self) -> bool:
        return self.lower_bound == "UNK" or self.upper_bound == "UNK"

    def has_integer_bounds(self) -> bool:
        return type(self.lower_bound) is int and type(self.upper_bound) is int

    def clone(self, suffix: str | None) -> "IteratorNode":
        if suffix is None:
            suffix = ""

        return IteratorNode(
            name=self.name + suffix,
            parent_iterator=self.parent_iterator + suffix
            if self.parent_iterator
            else None,
            lower_bound=self.lower_bound,
            upper_bound=self.upper_bound,
            child_iterators=[child + suffix for child in self.child_iterators],
            computations_list=[comp + suffix for comp in self.computations_list],
            level=self.level,
        )

    def __str__(self) -> str:
        return f"{self.name}(lower_bound={self.lower_bound}, upper_bound={self.upper_bound}, child_iterators={self.child_iterators}, computations_list={self.computations_list}, level={self.level})"

    def __repr__(self) -> str:
        return self.__str__()
