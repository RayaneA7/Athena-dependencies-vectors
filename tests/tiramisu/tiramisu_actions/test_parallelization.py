import tests.utils as test_utils
from athena.tiramisu import tiramisu_actions
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.parallelization import Parallelization
from athena.utils.config import BaseConfig


def test_parallelization_init():
    t_tree = test_utils.tree_test_sample()
    parallelization = Parallelization([("comp01", 1)])
    assert parallelization.iterator_id == ("comp01", 1)
    assert parallelization.comps is None

    parallelization = Parallelization([("comp01", 1)], comps=["comp01"])
    assert parallelization.iterator_id == ("comp01", 1)
    assert parallelization.comps == ["comp01"]


def test_initialize_action_for_tree():
    t_tree = test_utils.tree_test_sample()
    parallelization = Parallelization([("comp01", 1)])
    parallelization.initialize_action_for_tree(t_tree)

    assert parallelization.iterator_id == ("comp01", 1)
    assert parallelization.comps == ["comp01"]


def test_set_string_representations():
    BaseConfig.init()   
    sample = test_utils.benchmark_program_test_sample()
    parallelization = Parallelization([("comp02", 0)])
    schedule = Schedule(sample)
    schedule.add_optimizations([parallelization])

    assert parallelization.tiramisu_optim_str == "comp02.tag_parallel_level(0);\n"


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.benchmark_program_test_sample()
    candidates = Parallelization.get_candidates(sample.tree)
    assert candidates == {"c1": [["c1"], ["c3"], ["c5"]]}


def test_legality_check():
    BaseConfig.init()

    sample = test_utils.benchmark_program_test_sample()
    schedule = Schedule(sample)
    assert schedule.tree
    parallelization = Parallelization([("comp02", 0)])

    schedule.add_optimizations([parallelization])
    legality_string = schedule.optims_list[0].legality_check_string
    assert (
        legality_string
        == "is_legal &= loop_parallelization_is_legal(0, {&comp02});\n    comp02.tag_parallel_level(0);\n"
    )

    # sample = test_utils.multiple_roots_sample()
    # schedule = Schedule(sample)
    # assert schedule.tree

    # schedule.add_optimizations(
    #     [
    #         tiramisu_actions.Interchange([("x_temp", 0), ("x_temp", 1)], schedule.tree),
    #         tiramisu_actions.Fusion(["i", "j_0"], schedule.tree),
    #     ]
    # )

    # parallelization = Parallelization(("A_hat", 0), schedule.tree)

    # schedule.add_optimizations([parallelization])

    # assert schedule.tree

    # legality_string = schedule.optims_list[2].legality_check_string

    # assert (
    #     legality_string
    #     == "is_legal &= loop_parallelization_is_legal(0, {&A_hat, &x_temp});\n    A_hat.tag_parallel_level(0);\n"
    # )
