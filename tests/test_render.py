"""Carregamento e desenho da logo, e o confete."""
import cv2
import numpy as np
import pytest

import faz_o_l as f


@pytest.fixture
def logo_file(tmp_path):
    """PNG 100x60 com um retângulo vermelho opaco (60x20) cercado de transparência."""
    img = np.zeros((60, 100, 4), dtype=np.uint8)
    img[20:40, 20:80] = (0, 0, 255, 255)
    path = tmp_path / "logo.png"
    cv2.imwrite(str(path), img)
    return path


def blank(w=320, h=180):
    return np.full((h, w, 3), 50, dtype=np.uint8)


# ---------- carregamento da logo ----------

def test_load_logo_crops_transparent_margins(logo_file):
    logo = f.load_logo(logo_file)
    assert logo.shape == (20, 60, 4)
    assert (logo[..., 3] == 255).all()


def test_load_logo_premultiplies_alpha(tmp_path):
    img = np.zeros((10, 10, 4), dtype=np.uint8)
    img[..., :3] = 200
    img[..., 3] = 128
    path = tmp_path / "half.png"
    cv2.imwrite(str(path), img)
    logo = f.load_logo(path)
    assert logo[0, 0, 3] == 128
    assert logo[0, 0, 0] == pytest.approx(200 * 128 / 255, abs=1)


def test_load_logo_without_alpha_channel(tmp_path):
    path = tmp_path / "rgb.png"
    cv2.imwrite(str(path), np.full((8, 12, 3), 120, dtype=np.uint8))
    logo = f.load_logo(path)
    assert logo.shape == (8, 12, 4)
    assert (logo[..., 3] == 255).all()


def test_missing_logo_falls_back_to_placeholder(tmp_path, capsys):
    logo = f.load_logo(tmp_path / "nao_existe.png")
    assert logo.ndim == 3 and logo.shape[2] == 4 and logo.shape[1] > logo.shape[0]
    assert "provisória" in capsys.readouterr().out


# ---------- desenho da logo ----------

def test_draw_logo_changes_pixels(logo_file):
    frame, logo = blank(), f.load_logo(logo_file)
    f.draw_logo(frame, logo, 160, 90, 100)
    assert (frame[90, 160] == (0, 0, 255)).all()           # vermelho no centro
    assert (frame[5, 5] == 50).all()                        # o resto não muda


def test_draw_logo_alpha_blends(logo_file):
    frame, logo = blank(), f.load_logo(logo_file)
    f.draw_logo(frame, logo, 160, 90, 100, alpha=0.5)
    pixel = frame[90, 160].astype(int)
    assert 50 < pixel[2] < 255 and pixel[0] < 50            # mistura de vermelho com o fundo


def test_draw_logo_zero_alpha_is_noop(logo_file):
    frame, logo = blank(), f.load_logo(logo_file)
    before = frame.copy()
    f.draw_logo(frame, logo, 160, 90, 100, alpha=0)
    assert (frame == before).all()


@pytest.mark.parametrize("cx,cy", [(0, 0), (320, 180), (-500, 90), (160, 900), (319, 179)])
def test_draw_logo_clips_at_the_edges(logo_file, cx, cy):
    frame, logo = blank(), f.load_logo(logo_file)
    f.draw_logo(frame, logo, cx, cy, 120)                    # não pode lançar exceção
    assert frame.shape == (180, 320, 3)


def test_draw_logo_tiny_width_is_noop(logo_file):
    frame, logo = blank(), f.load_logo(logo_file)
    before = frame.copy()
    f.draw_logo(frame, logo, 160, 90, 1)
    assert (frame == before).all()


# ---------- confete ----------

def test_confetti_burst_creates_particles():
    c = f.Confetti(seed=1)
    assert len(c) == 0
    c.burst(160, 90, 100, 50, 320)
    assert len(c) == f.CONFETTI_COUNT


def test_confetti_burst_is_reproducible_with_seed():
    a, b = f.Confetti(seed=5), f.Confetti(seed=5)
    a.burst(160, 90, 100, 50, 320)
    b.burst(160, 90, 100, 50, 320)
    assert np.array_equal(a.p["pos"], b.p["pos"]) and np.array_equal(a.p["color"], b.p["color"])


def test_confetti_starts_inside_the_logo_area():
    c = f.Confetti(seed=2)
    c.burst(160, 90, 100, 50, 320)
    pos = c.p["pos"]
    assert pos[:, 0].min() >= 110 and pos[:, 0].max() <= 210
    assert pos[:, 1].min() >= 65 and pos[:, 1].max() <= 115


def test_confetti_uses_only_logo_colors_and_known_shapes():
    c = f.Confetti(seed=3)
    c.burst(160, 90, 100, 50, 320, count=500)
    assert set(c.p["color"]) <= set(range(len(f.CONFETTI_COLORS)))
    assert set(c.p["shape"]) <= set(range(len(f.CONFETTI_SHAPES)))
    # todas as cores e formas aparecem numa amostra grande
    assert len(set(c.p["color"])) == len(f.CONFETTI_COLORS)
    assert len(set(c.p["shape"])) == len(f.CONFETTI_SHAPES)


def test_confetti_red_is_the_rarest_logo_color():
    c = f.Confetti(seed=4)
    c.burst(160, 90, 100, 50, 320, count=5000)
    counts = np.bincount(c.p["color"], minlength=len(f.CONFETTI_COLORS))
    red = f.CONFETTI_COLORS.index((4, 4, 250))
    assert counts[red] == counts.min()


def test_confetti_falls_and_expires():
    c = f.Confetti(seed=6)
    c.burst(160, 90, 100, 50, 320)
    start_y = c.p["pos"][:, 1].mean()
    for _ in range(20):
        c.step(1 / 30, 320)
    assert len(c) == f.CONFETTI_COUNT                         # ainda vivos aos 0,66 s
    assert c.p["pos"][:, 1].mean() > start_y - 400            # (sanidade: não explodiu numericamente)
    for _ in range(int(f.CONFETTI_LIFE[1] * 30) + 5):
        c.step(1 / 30, 320)
    assert len(c) == 0                                        # todos expiraram


def test_confetti_step_on_empty_is_noop():
    c = f.Confetti()
    c.step(0.1, 320)
    assert len(c) == 0


def test_confetti_large_dt_is_clamped():
    c = f.Confetti(seed=7)
    c.burst(160, 90, 100, 50, 320)
    c.step(5.0, 320)                                          # um travamento longo não deve teleportar tudo
    assert np.isfinite(c.p["pos"]).all() if len(c) else True
    assert (c.p["age"] <= 0.1 + 1e-9).all() if len(c) else True


def test_confetti_bursts_accumulate():
    c = f.Confetti(seed=8)
    c.burst(100, 90, 100, 50, 320)
    c.burst(200, 90, 100, 50, 320)
    assert len(c) == 2 * f.CONFETTI_COUNT


def test_confetti_draw_paints_pixels_and_handles_offscreen():
    c = f.Confetti(seed=9)
    c.burst(160, 90, 100, 50, 320)
    frame = blank()
    before = frame.copy()
    c.draw(frame)
    assert (frame != before).any()

    far = f.Confetti(seed=10)
    far.burst(-900, -900, 100, 50, 320)                      # tudo fora do quadro
    far.draw(blank())                                         # não pode lançar exceção


def test_confetti_polygon_shapes():
    assert f.confetti_polygon("star", 0).shape == (10, 2)
    assert f.confetti_polygon("diamond", 0).shape == (4, 2)
    flat = f.confetti_polygon("rect", np.pi / 2)              # visto de lado: fino, mas não some
    wide = f.confetti_polygon("rect", 0)
    assert 0 < flat[:, 1].max() < wide[:, 1].max()
