import pytest

import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.tiling_general import TilingGeneral
from athena.tiramisu.tiramisu_actions.tiramisu_action import CannotApplyException
from athena.utils.config import BaseConfig


def test_tiling_general_init():
    tiling_general = TilingGeneral([("comp00", 0), ("comp00", 1), 32, 32])
    assert tiling_general.iterators == [("comp00", 0), ("comp00", 1)]
    assert tiling_general.tile_sizes == [32, 32]
    assert tiling_general.comps is None

    tiling_general = TilingGeneral([("comp00", 0), ("comp00", 1), 32, 32], ["comp00"])
    assert tiling_general.iterators == [("comp00", 0), ("comp00", 1)]
    assert tiling_general.tile_sizes == [32, 32]
    assert tiling_general.comps == ["comp00"]


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.gramschmidt_sample()
    tiling_general = TilingGeneral(
        [("R_up_init", 1), ("R_up", 2), ("A_out", 2), 10, 10, 10]
    )
    tiling_general.initialize_action_for_tree(sample.tree)
    assert tiling_general.iterators == [
        ("R_up_init", 1),
        ("R_up", 2),
        ("A_out", 2),
    ]
    assert tiling_general.tile_sizes_dict == {
        "c3_2": 10,
        "c5": 10,
        "c5_1": 10,
    }
    assert tiling_general.comps == ["R_up_init", "R_up", "A_out"]
    assert tiling_general.tiled_iterator_names == ["c3_2", "c5", "c5_1"]


def test_set_string_representations():
    BaseConfig.init()
    sample = test_utils.gramschmidt_sample()
    tiling_general = TilingGeneral(
        [("R_up_init", 1), ("R_up", 2), ("A_out", 2), 10, 5, 2]
    )
    tiling_general.initialize_action_for_tree(sample.tree)
    assert tiling_general.iterators == [
        ("R_up_init", 1),
        ("R_up", 2),
        ("A_out", 2),
    ]

    assert (
        tiling_general.tiramisu_optim_str
        == "R_up_init.tile(1, 10);\nR_up.tile(1, 2, 10, 5);\nA_out.tile(1, 2, 10, 2);\n"
        # clear_implicit_function_sched_graph();\n    nrm_init.then(nrm_comp,0).then(R_diag,0).then(Q_out,0).then(R_up_init,0).then(R_up,2).then(A_out,2);\n"
    )

    assert (
        tiling_general.str_representation
        == "TG(L1,L2,L2,10,5,2,comps=['R_up_init', 'R_up', 'A_out'])"
    )


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.gramschmidt_sample()
    candidates = TilingGeneral.get_candidates(sample.tree)
    assert candidates == {
        "c1": [("c1", "c3", "c3_1", "c3_2", "c5", "c5_1"), ("c3_2", "c5", "c5_1")]
    }

    candidates = TilingGeneral.get_candidates(test_utils.tree_test_sample())
    assert candidates == {"root": [("root", "i", "j", "k", "l", "m")]}

    t_tree = test_utils.tree_test_sample_imperfect_loops()
    candidates = TilingGeneral.get_candidates(t_tree)
    assert candidates == {
        "root": [
            ("root", "i", "i_1", "j", "j_1", "k"),
            ("i", "j"),
            ("j", "k"),
            ("i", "j", "k"),
            ("i_1", "j_1"),
        ]
    }
