"""Mãos sintéticas (21 landmarks no formato do MediaPipe) para os testes.

O desenho é de uma mão com a palma para a câmera e os dedos para cima, em pixels (y cresce para
baixo). O pulso fica em (0, 0) e a palma (pulso -> base do dedo médio) mede 100 px.
"""
import math

import numpy as np

# base de cada dedo (MCP) e direção em que ele aponta quando está esticado
_MCP = {"index": (-30, -95), "middle": (0, -100), "ring": (30, -95), "pinky": (55, -80)}
_LENGTHS = {"index": (40, 25, 20), "middle": (45, 27, 23), "ring": (40, 25, 20), "pinky": (30, 18, 16)}


def make_hand(index=True, middle=False, ring=False, pinky=False, thumb="side"):
    """Monta uma mão. Cada dedo está esticado (True) ou dobrado (False).

    thumb: "side" (afastado, formando um L com o indicador), "up" (esticado ao lado do indicador)
    ou "tucked" (dobrado sobre a palma).
    """
    pts = np.zeros((21, 2), dtype=np.float32)
    pts[0] = (0, 0)

    extended = {"index": index, "middle": middle, "ring": ring, "pinky": pinky}
    first = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}
    for name, start in first.items():
        mcp = np.array(_MCP[name], dtype=np.float32)
        pts[start] = mcp
        seg = _LENGTHS[name]
        if extended[name]:
            pos = mcp.copy()
            for i, length in enumerate(seg):
                pos = pos + (0, -length)
                pts[start + 1 + i] = pos
        else:  # dobrado: sobe até a primeira junta e volta para a palma
            pts[start + 1] = mcp + (0, -seg[0])
            pts[start + 2] = mcp + (0, -seg[0] * 0.5)
            pts[start + 3] = mcp + (0, seg[0] * 0.1)

    pts[1] = (-40, -20)
    if thumb == "side":
        pts[2], pts[3], pts[4] = (-45, -35), (-80, -45), (-110, -50)
    elif thumb == "up":
        pts[2], pts[3], pts[4] = (-60, -55), (-75, -85), (-85, -115)
    else:  # tucked
        pts[2], pts[3], pts[4] = (-45, -45), (-35, -65), (-25, -75)
    return pts


def l_hand():
    """Indicador esticado, polegar aberto para o lado, resto dobrado."""
    return make_hand(index=True, thumb="side")


def transform(pts, angle_deg=0.0, scale=1.0, flip=False, offset=(0.0, 0.0)):
    """Gira (em torno do pulso), escala, espelha na horizontal e desloca os pontos."""
    out = pts.copy()
    if flip:
        out[:, 0] = -out[:, 0]
    a = math.radians(angle_deg)
    rot = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]], dtype=np.float32)
    return (out @ rot.T) * scale + np.array(offset, dtype=np.float32)
