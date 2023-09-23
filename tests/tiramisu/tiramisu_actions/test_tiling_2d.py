import pytest

import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.tiling_2d import Tiling2D
from athena.tiramisu.tiramisu_actions.tiramisu_action import CannotApplyException
from athena.utils.config import BaseConfig


def test_tiling_2d_init():
    tiling_2d = Tiling2D([("comp00", 0), ("comp00", 1), 32, 32])
    assert tiling_2d.iterators == [("comp00", 0), ("comp00", 1)]
    assert tiling_2d.tile_sizes == [32, 32]
    assert tiling_2d.comps is None

    tiling_2d = Tiling2D([("comp00", 0), ("comp00", 1), 32, 32], ["comp00"])
    assert tiling_2d.iterators == [("comp00", 0), ("comp00", 1)]
    assert tiling_2d.tile_sizes == [32, 32]
    assert tiling_2d.comps == ["comp00"]


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.tiling_2d_sample()
    tiling_2d = Tiling2D([("comp00", 0), ("comp00", 1), 32, 32])
    tiling_2d.initialize_action_for_tree(sample.tree)
    assert tiling_2d.iterators == [("comp00", 0), ("comp00", 1)]
    assert tiling_2d.tile_sizes == [32, 32]
    assert tiling_2d.comps == ["comp00"]


def test_set_string_representations():
    BaseConfig.init()
    sample = test_utils.tiling_2d_sample()
    tiling_2d = Tiling2D([("comp00", 0), ("comp00", 1), 32, 32])
    schedule = Schedule(sample)
    schedule.add_optimizations([tiling_2d])
    assert tiling_2d.tiramisu_optim_str == "comp00.tile(0, 1, 32, 32);\n"


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.tiling_2d_sample()
    candidates = Tiling2D.get_candidates(sample.tree)
    assert candidates == {"i0": [("i0", "i1")]}

    candidates = Tiling2D.get_candidates(test_utils.tree_test_sample())
    assert candidates == {"root": [("j", "k")]}


def test_fusion_levels():
    t_tree = test_utils.tree_test_sample_3()

    action = Tiling2D([("comp03", 2), ("comp03", 3), 32, 32])
    action.initialize_action_for_tree(t_tree)
    assert (
        action.tiramisu_optim_str.split("\n")[-2]
        == "    comp01.then(comp05,0).then(comp06,1).then(comp07,1).then(comp03,1).then(comp04,6);"
    )
