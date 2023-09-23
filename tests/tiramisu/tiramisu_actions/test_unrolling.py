import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.unrolling import Unrolling
from athena.utils.config import BaseConfig


def test_reversal_init():
    reversal = Unrolling([("comp00", 0), 4])
    assert reversal.iterator_id == ("comp00", 0)
    assert reversal.unrolling_factor == 4
    assert reversal.comps is None

    reversal = Unrolling([("comp00", 0), 4], ["comp00"])
    assert reversal.iterator_id == ("comp00", 0)
    assert reversal.unrolling_factor == 4
    assert reversal.comps == ["comp00"]


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.unrolling_sample()
    reversal = Unrolling([("comp00", 0), 4])
    reversal.initialize_action_for_tree(sample.tree)
    assert reversal.iterator_id == ("comp00", 0)
    assert reversal.unrolling_factor == 4
    assert reversal.comps == ["comp00"]


def test_set_string_representations():
    BaseConfig.init()
    sample = test_utils.unrolling_sample()
    reversal = Unrolling([("comp00", 0), 4])
    schedule = Schedule(sample)
    schedule.add_optimizations([reversal])
    assert reversal.tiramisu_optim_str == "comp00.unroll(0,4);"
    assert (
        reversal.legality_check_string
        == "is_legal &= loop_unrolling_is_legal(0, {&comp00});\n    comp00.unroll(0,4);"
    )


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.unrolling_sample()
    candidates = Unrolling.get_candidates(sample.tree)
    assert candidates == ["i1"]

    candidates = Unrolling.get_candidates(test_utils.tree_test_sample())
    assert candidates == ["i", "l", "m"]
