from athena.search_methods.sequential_parallelization import (
    parallelize_first_legal_outermost,
)
from athena.tiramisu.tiramisu_actions.parallelization import Parallelization
from athena.utils.config import BaseConfig
from tests.utils import benchmark_program_test_sample


def test_sequential_parallelization():
    BaseConfig.init()
    test_program = benchmark_program_test_sample()

    schedule = parallelize_first_legal_outermost(test_program)
    optim = schedule.optims_list[0]
    assert isinstance(optim, Parallelization)
    assert optim.iterator_id == ("comp02", 0)
