import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.fusion import Fusion
from athena.tiramisu.tiramisu_actions.interchange import Interchange
from athena.utils.config import BaseConfig


def test_fusion_init():
    fusion = Fusion([("comp03", 3), ("comp04", 3)])

    assert fusion.params == [("comp03", 3), ("comp04", 3)]
    assert fusion.comps is None


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.fusion_sample()
    fusion = Fusion([("comp03", 3), ("comp04", 3)])
    fusion.initialize_action_for_tree(sample.tree)
    assert fusion.params == [("comp03", 3), ("comp04", 3)]
    assert fusion.comps == ["comp03", "comp04"]


def test_set_string_representations():
    BaseConfig.init()
    sample = test_utils.fusion_sample()
    fusion = Fusion([("comp03", 3), ("comp04", 3)])
    fusion.initialize_action_for_tree(sample.tree)
    assert (
        fusion.tiramisu_optim_str
        == "clear_implicit_function_sched_graph();\n    comp01.then(comp03,0).then(comp04,3);\n"
    )


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.fusion_sample()
    candidates = Fusion.get_candidates(sample.tree)
    assert candidates == [("i", "j"), ("l", "m")]


def test_reorder_computations():
    BaseConfig.init()
    sample = test_utils.fusion_sample()
    fusion = Fusion([("comp03", 3), ("comp04", 3)])
    fusion.initialize_action_for_tree(sample.tree)
    comps, fusion_levels = fusion.reorder_computations(sample.tree)

    assert comps == ["comp01", "comp03", "comp04"]
    assert fusion_levels == [0, 3]

    sample = test_utils.multiple_roots_sample()

    fusion = Fusion([("A_hat", 0), ("x_temp", 0)])
    fusion.initialize_action_for_tree(sample.tree)
    comps, fusion_levels = fusion.reorder_computations(sample.tree)

    assert comps == ["A_hat", "x_temp", "x", "w"]
    assert fusion_levels == [0, -1, -1]

    fusion = Fusion([("x", 0), ("w", 0)])
    fusion.initialize_action_for_tree(sample.tree)
    comps, fusion_levels = fusion.reorder_computations(sample.tree)
    assert comps == ["A_hat", "x_temp", "x", "w"]
    assert fusion_levels == [
        -1,
        -1,
        0,
    ]

    fusion = Fusion([("x_temp", 0), ("w", 0)])
    fusion.initialize_action_for_tree(sample.tree)

    comps, fusion_levels = fusion.reorder_computations(
        sample.tree,
    )

    assert fusion_levels == [
        -1,
        0,
        -1,
    ]

    fusion = Fusion([("x_temp", 1), ("w", 1)])
    fusion.initialize_action_for_tree(sample.tree)
    comps, fusion_levels = fusion.reorder_computations(sample.tree)

    assert fusion_levels == [
        -1,
        1,
        -1,
    ]


def test_fusion_application():
    BaseConfig.init()

    sample = test_utils.multiple_roots_sample()
    schedule = Schedule(sample)

    assert schedule.tree

    fusion = Fusion([("A_hat", 0), ("x_temp", 0)])

    schedule.add_optimizations([fusion])

    assert (
        fusion.tiramisu_optim_str
        == "clear_implicit_function_sched_graph();\n    A_hat.then(x_temp,0).then(x,-1).then(w,-1);\n"
    )
    assert not schedule.is_legal()

    schedule = Schedule(sample)
    assert schedule.tree

    schedule.add_optimizations(
        [
            Interchange(params=[("x_temp", 0), ("x_temp", 1)]),
        ]
    )

    fusion = Fusion([("A_hat", 0), ("x_temp", 0)])
    schedule.add_optimizations([fusion])

    assert (
        fusion.tiramisu_optim_str
        == "clear_implicit_function_sched_graph();\n    A_hat.then(x_temp,0).then(x,-1).then(w,-1);\n"
    )

    assert schedule.is_legal()

    assert schedule.apply_schedule()
