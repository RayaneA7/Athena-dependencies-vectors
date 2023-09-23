import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions import Expansion, Parallelization
from athena.utils.config import BaseConfig


def test_expansion_init():
    expansion = Expansion(["comp"])
    assert expansion.computation == "comp"


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.expansion_sample()
    expansion = Expansion(["addition"])
    expansion.initialize_action_for_tree(sample.tree)
    assert expansion.computation == "addition"
    assert expansion.tree is not None


def test_set_string_representation():
    BaseConfig.init()
    sample = test_utils.expansion_sample()
    expansion = Expansion(["addition"])
    expansion.initialize_action_for_tree(sample.tree)
    assert expansion.tiramisu_optim_str == "addition.expand(true);\n"


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.expansion_sample()
    schedule = Schedule(sample)
    candidates = Expansion.get_candidates(schedule)
    assert candidates == ["addition"]


def test_expansion_application():
    BaseConfig.init()
    sample = test_utils.expansion_sample()
    schedule = Schedule(sample)
    schedule.add_optimizations([Parallelization([("addition", 1)])])

    assert not schedule.is_legal()

    schedule = Schedule(sample)
    schedule.add_optimizations(
        [Expansion(["addition"]), Parallelization([("addition", 1)])]
    )
    assert schedule.is_legal()
