"""Regra do gesto do "L" (analyze_hand)."""
import pytest

import faz_o_l as f
from hands import l_hand, make_hand, transform


def test_l_hand_is_detected():
    shape = f.analyze_hand(l_hand())
    assert shape.is_l
    assert shape.index_reach >= f.INDEX_MIN_REACH
    assert shape.others_reach <= f.OTHERS_MAX_REACH
    assert shape.thumb_open >= f.THUMB_MIN_OPEN
    assert f.ANGLE_RANGE[0] <= shape.angle <= f.ANGLE_RANGE[1]


@pytest.mark.parametrize("angle", [-60, -30, 0, 30, 90, 180])
def test_l_is_rotation_invariant(angle):
    assert f.analyze_hand(transform(l_hand(), angle_deg=angle)).is_l


@pytest.mark.parametrize("scale", [0.3, 1.0, 3.0])
def test_l_is_scale_invariant(scale):
    assert f.analyze_hand(transform(l_hand(), scale=scale)).is_l


def test_l_with_mirrored_hand():
    assert f.analyze_hand(transform(l_hand(), flip=True)).is_l


@pytest.mark.parametrize("name,hand", [
    ("mão aberta", make_hand(index=True, middle=True, ring=True, pinky=True, thumb="up")),
    ("punho", make_hand(index=False, thumb="tucked")),
    ("apontando", make_hand(index=True, thumb="tucked")),
    ("polegar para cima", make_hand(index=False, thumb="up")),
    ("paz e amor", make_hand(index=True, middle=True, thumb="tucked")),
    ("indicador e mindinho", make_hand(index=True, pinky=True, thumb="tucked")),
])
def test_other_gestures_are_not_l(name, hand):
    assert not f.analyze_hand(hand).is_l, name


def test_thumb_parallel_to_index_is_not_l():
    # polegar esticado para cima, junto do indicador: ângulo pequeno entre os dois
    hand = make_hand(index=True, thumb="up")
    shape = f.analyze_hand(hand)
    assert shape.angle < f.ANGLE_RANGE[0]
    assert not shape.is_l


def test_degenerate_hand_does_not_crash():
    import numpy as np

    shape = f.analyze_hand(np.zeros((21, 2), dtype=np.float32))
    assert not shape.is_l
