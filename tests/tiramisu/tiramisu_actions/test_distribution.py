import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.distribution import Distribution
from athena.utils.config import BaseConfig


def test_distribution_init():
    distribution = Distribution([("comp05", 1)])

    assert distribution.iterator_id == ("comp05", 1)
    assert distribution.children is None

    distribution = Distribution(
        [("comp05", 1)], [["comp05"], ["comp06"], ["comp07"], [("comp03", 2)]]
    )
    assert distribution.iterator_id == ("comp05", 1)
    assert distribution.children == [
        ["comp05"],
        ["comp06"],
        ["comp07"],
        [("comp03", 2)],
    ]


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.tree_test_sample_2()

    distribution = Distribution([("comp05", 1)])
    distribution.initialize_action_for_tree(sample)

    assert distribution.iterator_id == ("comp05", 1)
    expected_children = [
        ["comp05"],
        ["comp06"],
        ["comp07"],
        ["comp03", "comp04"],
    ]
    assert len(distribution.children) == len(expected_children)
    for child_list in distribution.children:
        assert child_list in expected_children

    distribution = Distribution([("comp03", 2)], [[("comp03", 3)], [("comp04", 3)]])
    distribution.initialize_action_for_tree(sample)
    assert distribution.iterator_id == ("comp03", 2)
    expected_children = [["comp03"], ["comp04"]]
    assert len(distribution.children) == len(expected_children)
    for child_list in distribution.children:
        assert child_list in expected_children


def test_set_string_representations():
    BaseConfig.init()
    sample = test_utils.gramschmidt_sample()
    distribution = Distribution([("R_up_init", 1)])
    schedule = Schedule(sample)
    schedule.add_optimizations([distribution])
    assert (
        distribution.tiramisu_optim_str
        == "clear_implicit_function_sched_graph();\n    nrm_init.then(nrm_comp,0).then(R_diag,0).then(Q_out,0).then(R_up_init,0).then(R_up,0).then(A_out,0);\n"
    )


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.gramschmidt_sample()
    candidates = Distribution.get_candidates(sample.tree)
    assert candidates == ["c1", "c3_2"]


def test_get_fusion_levels():
    BaseConfig.init()
    sample = test_utils.gramschmidt_sample()
    distribution = Distribution([("R_up_init", 1)])
    distribution.initialize_action_for_tree(sample.tree)
    ordered_computations = sample.tree.computations
    ordered_computations.sort(key=lambda x: sample.tree.computations_absolute_order[x])
    assert distribution.get_fusion_levels(ordered_computations, sample.tree) == [
        0,
        0,
        0,
        0,
        0,
        0,
    ]

    t_tree = test_utils.tree_test_sample_2()
    distribution = Distribution([("comp05", 1)])
    distribution.initialize_action_for_tree(t_tree)
    ordered_computations = t_tree.computations
    ordered_computations.sort(key=lambda x: t_tree.computations_absolute_order[x])
    assert distribution.get_fusion_levels(ordered_computations, t_tree) == [
        0,
        0,
        0,
        0,
        2,
    ]

    t_tree = test_utils.tree_test_sample_2()
    distribution = Distribution(
        [("comp05", 1)], [["comp05", "comp06"], ["comp07", ("comp03", 2)]]
    )
    distribution.initialize_action_for_tree(t_tree)
    ordered_computations = t_tree.computations
    ordered_computations.sort(key=lambda x: t_tree.computations_absolute_order[x])
    assert distribution.get_fusion_levels(ordered_computations, t_tree) == [
        0,
        1,
        0,
        1,
        2,
    ]


def test_distribution_application():
    BaseConfig.init()

    sample = test_utils.gramschmidt_sample()
    schedule = Schedule(sample)

    assert schedule.tree

    distribution = Distribution([("nrm_init", 0)])

    schedule.add_optimizations([distribution])

    assert (
        distribution.tiramisu_optim_str
        == "clear_implicit_function_sched_graph();\n    nrm_init.then(nrm_comp,-1).then(R_diag,-1).then(Q_out,-1).then(R_up_init,-1).then(R_up,1).then(A_out,1);\n"
    )
    assert not schedule.is_legal()

    sample = test_utils.gramschmidt_sample()
    schedule = Schedule(sample)
    assert schedule.tree

    schedule.add_optimizations(
        [
            Distribution(params=[("R_up_init", 1)]),
        ]
    )

    distribution = schedule.optims_list[0]

    assert (
        distribution.tiramisu_optim_str
        == "clear_implicit_function_sched_graph();\n    nrm_init.then(nrm_comp,0).then(R_diag,0).then(Q_out,0).then(R_up_init,0).then(R_up,0).then(A_out,0);\n"
    )

    assert schedule.is_legal()

    assert schedule.apply_schedule()
