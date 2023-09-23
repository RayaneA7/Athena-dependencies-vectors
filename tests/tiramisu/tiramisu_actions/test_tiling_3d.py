import pytest

import tests.utils as test_utils
from athena.tiramisu.schedule import Schedule
from athena.tiramisu.tiramisu_actions.tiling_3d import Tiling3D
from athena.tiramisu.tiramisu_actions.tiramisu_action import CannotApplyException
from athena.utils.config import BaseConfig


def test_tiling_3d_init():
    BaseConfig.init()
    sample = test_utils.tiling_3d_sample()
    tiling_3d = Tiling3D(
        [
            ("comp00", 0),
            ("comp00", 1),
            ("comp00", 2),
            32,
            32,
            32,
        ]
    )
    assert tiling_3d.iterators == [("comp00", 0), ("comp00", 1), ("comp00", 2)]
    assert tiling_3d.tile_sizes == [32, 32, 32]
    assert tiling_3d.comps is None

    tiling_3d = Tiling3D(
        [
            ("comp00", 0),
            ("comp00", 1),
            ("comp00", 2),
            32,
            32,
            32,
        ],
        ["comp00"],
    )

    assert tiling_3d.iterators == [("comp00", 0), ("comp00", 1), ("comp00", 2)]
    assert tiling_3d.tile_sizes == [32, 32, 32]
    assert tiling_3d.comps == ["comp00"]


def test_initialize_action_for_tree():
    BaseConfig.init()
    sample = test_utils.tiling_3d_sample()
    tiling_3d = Tiling3D(
        [
            ("comp00", 0),
            ("comp00", 1),
            ("comp00", 2),
            32,
            32,
            32,
        ]
    )
    tiling_3d.initialize_action_for_tree(sample.tree)
    assert tiling_3d.iterators == [("comp00", 0), ("comp00", 1), ("comp00", 2)]
    assert tiling_3d.tile_sizes == [32, 32, 32]
    assert tiling_3d.comps == ["comp00"]


def test_set_string_representations():
    BaseConfig.init()
    sample = test_utils.tiling_3d_sample()
    tiling_3d = Tiling3D(
        [
            ("comp00", 0),
            ("comp00", 1),
            ("comp00", 2),
            32,
            32,
            32,
        ]
    )
    schedule = Schedule(sample)
    schedule.add_optimizations([tiling_3d])
    assert tiling_3d.tiramisu_optim_str == "comp00.tile(0, 1, 2, 32, 32, 32);\n"


def test_get_candidates():
    BaseConfig.init()
    sample = test_utils.tiling_3d_sample()
    candidates = Tiling3D.get_candidates(sample.tree)
    assert candidates == {"i0": [("i0", "i1", "i2")]}

    candidates = Tiling3D.get_candidates(test_utils.tiling_3d_tree_sample())
    assert candidates == {"root": [("root", "j", "k"), ("j", "k", "l")]}


def test_fusion_levels():
    t_tree = test_utils.tree_test_sample_3()

    action = Tiling3D([("comp03", 2), ("comp03", 3), ("comp03", 4), 32, 32, 32])
    action.initialize_action_for_tree(t_tree)
    assert (
        action.tiramisu_optim_str.split("\n")[-2]
        == "    comp01.then(comp05,0).then(comp06,1).then(comp07,1).then(comp03,1).then(comp04,7);"
    )
