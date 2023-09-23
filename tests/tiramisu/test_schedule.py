import tests.utils as test_utils
from athena.tiramisu import tiramisu_actions
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.parallelization import Parallelization
from athena.utils.config import BaseConfig
from tests.utils import benchmark_program_test_sample


def test_apply_schedule():
    BaseConfig.init()
    test_program = benchmark_program_test_sample()
    schedule = Schedule(test_program)
    assert schedule.tree
    schedule.add_optimizations([Parallelization(params=[("comp02", 0)])])
    results = schedule.apply_schedule(nb_exec_tiems=10)
    print(results)

    assert results is not None
    assert len(results) == 10


def test_is_legal():
    BaseConfig.init()
    test_program = benchmark_program_test_sample()

    schedule = Schedule(test_program)
    assert schedule.tree

    schedule.add_optimizations([Parallelization(params=[("comp02", 0)])])
    legality = schedule.is_legal()

    assert legality is True


def test_copy():
    BaseConfig.init()
    original = Schedule(benchmark_program_test_sample())
    assert original.tree

    original.add_optimizations([Parallelization(params=[("comp02", 0)])])

    copy = original.copy()

    assert original is not copy
    assert original.tiramisu_program is copy.tiramisu_program
    assert original.optims_list is not copy.optims_list
    assert len(original.optims_list) == len(copy.optims_list)
    for optim in original.optims_list:
        assert optim in copy.optims_list


def test_str_representation():
    BaseConfig.init()
    test_program = benchmark_program_test_sample()

    schedule = Schedule(test_program)
    assert schedule.tree

    schedule.add_optimizations([Parallelization(params=[("comp02", 0)])])

    assert str(schedule) == "P(L0,comps=['comp02'])"


def test_from_sched_str():
    BaseConfig.init()

    test_program = test_utils.multiple_roots_sample()

    schedule = Schedule(test_program)
    assert schedule.tree

    schedule.add_optimizations(
        [
            Parallelization(params=[("A_hat", 0)]),
            tiramisu_actions.Interchange(params=[("x_temp", 0), ("x_temp", 1)]),
            tiramisu_actions.Fusion(params=[("A_hat", 0), ("x_temp", 0)]),
            tiramisu_actions.Tiling2D(params=[("w", 0), ("w", 1), 4, 4]),
            tiramisu_actions.Unrolling(params=[("x", 0), 4]),
            tiramisu_actions.Reversal(params=[("x", 0)]),
        ]
    )

    sched_str = str(schedule)

    new_schedule = Schedule.from_sched_str(sched_str, test_program)

    assert new_schedule is not None

    assert len(new_schedule.optims_list) == len(schedule.optims_list)

    for idx, optim in enumerate(schedule.optims_list):
        assert optim == new_schedule.optims_list[idx]

    schedule = Schedule(test_program)
    assert schedule.tree

    schedule.add_optimizations(
        [
            tiramisu_actions.Skewing([("x_temp", 0), ("x_temp", 1), 1, 1]),
        ]
    )

    sched_str = str(schedule)

    new_schedule = Schedule.from_sched_str(sched_str, test_program)

    assert new_schedule is not None
    assert len(new_schedule.optims_list) == len(schedule.optims_list)

    for idx, optim in enumerate(schedule.optims_list):
        assert optim == new_schedule.optims_list[idx]

    test_program = test_utils.tiling_3d_sample()

    schedule = Schedule(test_program)
    assert schedule.tree

    schedule.add_optimizations(
        [
            tiramisu_actions.Tiling3D(
                [("comp00", 0), ("comp00", 1), ("comp00", 2), 4, 4, 4]
            ),
        ]
    )

    sched_str = str(schedule)

    new_schedule = Schedule.from_sched_str(sched_str, test_program)

    assert new_schedule is not None
    assert len(new_schedule.optims_list) == len(schedule.optims_list)

    for idx, optim in enumerate(schedule.optims_list):
        assert optim == new_schedule.optims_list[idx]


test_apply_schedule()


