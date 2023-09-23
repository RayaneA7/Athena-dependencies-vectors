import pytest

import athena.tiramisu.tiramisu_actions as tiramisu_actions
from athena.tiramisu.tiramisu_actions import TiramisuAction, TiramisuActionType


def test_initialize_action_for_tree():
    tiramisu_action = TiramisuAction(type=None, params=[1, 2, 3], comps=["a", "b", "c"])
    with pytest.raises(NotImplementedError) as e_info:
        tiramisu_action.initialize_action_for_tree(tiramisu_tree=None)


def test_set_string_representations():
    tiramisu_action = TiramisuAction(type=None, params=[1, 2, 3], comps=["a", "b", "c"])
    with pytest.raises(NotImplementedError) as e_info:
        tiramisu_action.set_string_representations(tiramisu_tree=None)


def test_is_interchange():
    t_action = tiramisu_actions.Interchange([(), ()])

    assert t_action.is_interchange()


def test_is_tiling_2d():
    t_action = tiramisu_actions.Tiling2D([(), (), 1, 1])

    assert t_action.is_tiling_2d()


def test_is_tiling_3d():
    t_action = tiramisu_actions.Tiling3D([(), (), (), 1, 1, 1])

    assert t_action.is_tiling_3d()


def test_is_parallelization():
    t_action = tiramisu_actions.Parallelization([()])

    assert t_action.is_parallelization()


def test_is_skewing():
    t_action = tiramisu_actions.Skewing([(), (), 1, 1])
    assert t_action.is_skewing()


def test_is_unrolling():
    t_action = tiramisu_actions.Unrolling([(), 1])
    assert t_action.is_unrolling()


def test_is_fusion():
    t_action = tiramisu_actions.Fusion([("", 1), ("", 1)])
    assert t_action.is_fusion()


def test_is_reversal():
    t_action = tiramisu_actions.Reversal([()])
    assert t_action.is_reversal()


def test_is_distribution():
    t_action = tiramisu_actions.Distribution([()])
    assert t_action.is_distribution()


def test_get_candidates():
    with pytest.raises(NotImplementedError) as e_info:
        TiramisuAction.get_candidates(program_tree=None)


def test_get_types():
    assert len(TiramisuAction.get_types()) == 11


def test_str():
    t_action = tiramisu_actions.Interchange(
        [("comp00", 0), ("comp00", 1)], comps=["comp00"]
    )
    t_action.set_string_representations(None)
    assert str(t_action) == "I(L0,L1,comps=['comp00'])"


def test_repr():
    t_action = tiramisu_actions.Interchange(
        [("comp00", 0), ("comp00", 1)], comps=["comp00"]
    )
    assert (
        repr(t_action)
        == f"Action(type={TiramisuActionType.INTERCHANGE}, params={t_action.params}, comps={t_action.comps})"
    )


def test_eq():
    t_action = tiramisu_actions.Interchange(
        [("comp00", 0), ("comp00", 1)], comps=["comp00"]
    )
    t_action2 = tiramisu_actions.Interchange(
        [("comp00", 0), ("comp00", 1)], comps=["comp00"]
    )
    assert t_action == t_action2

    t_action2 = tiramisu_actions.Interchange(
        [("comp00", 0), ("comp00", 1)], comps=["comp01"]
    )

    assert t_action != t_action2
