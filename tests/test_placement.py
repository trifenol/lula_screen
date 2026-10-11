"""Posição e tamanho da logo em relação à mão (logo_placement) e o zoom."""
import numpy as np
import pytest

import faz_o_l as f
from hands import l_hand, transform

W, H = 640, 360
ASPECT = 0.5  # altura / largura da logo


def hand_at(x, y, **kwargs):
    return transform(l_hand(), offset=(x, y), **kwargs)


def hand_box(pts):
    return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()


def test_logo_goes_to_the_side_the_thumb_points():
    # l_hand() tem o polegar à esquerda do indicador
    left_thumb = hand_at(400, 300)
    cx, _, width = f.logo_placement(left_thumb, W, H, ASPECT)
    assert cx + width / 2 <= hand_box(left_thumb)[0] + 0.5 * width  # fica à esquerda da mão

    right_thumb = hand_at(200, 300, flip=True)
    cx, _, width = f.logo_placement(right_thumb, W, H, ASPECT)
    assert cx - width / 2 >= hand_box(right_thumb)[0]  # começa depois do início da mão


def test_logo_flips_side_when_there_is_no_room():
    # polegar à esquerda, mas a mão está encostada na borda esquerda: a logo vai para a direita
    pts = hand_at(120, 300)
    box = hand_box(pts)
    cx, _, width = f.logo_placement(pts, W, H, ASPECT)
    assert cx - width / 2 >= 0
    assert cx > (box[0] + box[2]) / 2


@pytest.mark.parametrize("x,y,scale", [(20, 20, 1), (620, 340, 1), (320, 180, 8), (320, 180, 0.05), (-50, 400, 2)])
def test_logo_always_inside_the_frame(x, y, scale):
    pts = hand_at(x, y, scale=scale)
    cx, cy, width = f.logo_placement(pts, W, H, ASPECT)
    height = width * ASPECT
    assert cx - width / 2 >= -1e-6 and cx + width / 2 <= W + 1e-6
    assert cy - height / 2 >= -1e-6 and cy + height / 2 <= H + 1e-6


def test_zoom_logo_grows_as_the_hand_gets_closer():
    widths = [f.logo_placement(hand_at(300, 300, scale=s), W, H, ASPECT)[2] for s in (0.6, 0.9, 1.2, 1.5)]
    assert widths == sorted(widths)
    assert widths[-1] > widths[0]


def test_zoom_matches_the_reference_calibration():
    palm = f.palm_size(hand_at(300, 300))
    scale = (f.ZOOM_REF_PALM * W) / palm  # leva a palma ao tamanho de referência
    width = f.logo_placement(hand_at(300, 300, scale=scale), W, H, ASPECT)[2]
    assert width == pytest.approx(f.ZOOM_REF_LOGO * W, rel=0.02)


def test_zoom_width_respects_limits():
    lo, hi = f.LOGO_WIDTH_LIMITS
    tiny = f.logo_placement(hand_at(300, 300, scale=0.05), W, H, ASPECT)[2]
    huge = f.logo_placement(hand_at(300, 300, scale=20), W, H, ASPECT)[2]
    assert tiny == pytest.approx(lo * W)
    assert huge == pytest.approx(hi * W)


def test_zoom_exponent_exaggerates_the_effect():
    # tamanhos escolhidos para ficar dentro dos limites de largura (senão o clamp distorce a razão)
    near = hand_at(300, 300, scale=0.7)
    far = hand_at(300, 300, scale=0.4)

    def ratio(zoom):
        return (f.logo_placement(near, W, H, ASPECT, zoom=zoom)[2]
                / f.logo_placement(far, W, H, ASPECT, zoom=zoom)[2])

    assert ratio(1.5) > ratio(1.0) > ratio(0.5) > 1.0


def test_logo_scale_multiplier():
    pts = hand_at(300, 300)
    base = f.logo_placement(pts, W, H, ASPECT)[2]
    assert f.logo_placement(pts, W, H, ASPECT, scale_mul=0.5)[2] == pytest.approx(base * 0.5, rel=0.01)


def test_logo_sits_above_the_thumb():
    # com zoom forte a logo fica grande (65% do quadro): a base dela não pode passar do limite
    # acima do polegar, então ela cresce para cima
    pts = hand_at(300, 300)
    _, cy, width = f.logo_placement(pts, W, H, ASPECT, zoom=1.5)
    top = pts[:, 1].min()
    size = max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
    assert width == pytest.approx(f.LOGO_WIDTH_LIMITS[1] * W)
    assert cy + width * ASPECT / 2 == pytest.approx(top + size * f.LOGO_BOTTOM_MAX, abs=0.5)


def test_palm_size_is_rigid_across_gestures():
    from hands import make_hand

    assert f.palm_size(make_hand(index=True, thumb="side")) == pytest.approx(
        f.palm_size(make_hand(index=True, middle=True, ring=True, pinky=True, thumb="up")))
