"""Faz o L: quando a pessoa faz o "L" com a mão, a logo aparece ao lado da mão na webcam,
com uma explosão de confete nas cores da campanha.

Uso:
    python faz_o_l.py                  # webcam + janela de preview
    python faz_o_l.py --virtual-cam    # também envia para a OBS Virtual Camera (Zoom/Meet/Teams)
    python faz_o_l.py --image foto.png --out saida.png   # testa a detecção numa imagem
    python faz_o_l.py --video entrada.mp4 --save saida.mp4 --no-preview   # processa um vídeo

Teclas na janela: q/ESC sai, d liga/desliga o modo debug (landmarks e métricas).
A logo é lida de assets/logo.png (PNG com transparência) ou do arquivo dado em --logo.
Veja o README.md e a pasta docs/ para a documentação completa.
"""
import argparse
import math
import os
import sys
import time
import urllib.request
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
LOGO_PATH = ROOT / "assets" / "logo.png"
WINDOW = "Faz o L"

# índices dos landmarks da mão no MediaPipe
WRIST, THUMB_MCP, THUMB_TIP = 0, 2, 4
INDEX_MCP, INDEX_TIP = 5, 8
MIDDLE_MCP, MIDDLE_TIP = 9, 12
RING_TIP, PINKY_TIP = 16, 20
PINKY_MCP = 17

# limites da regra do "L" (distâncias normalizadas pelo tamanho da palma)
INDEX_MIN_REACH = 1.6    # indicador esticado
OTHERS_MAX_REACH = 1.5   # médio, anelar e mindinho dobrados
THUMB_MIN_OPEN = 0.7     # polegar afastado da palma
ANGLE_RANGE = (40.0, 135.0)  # ângulo entre polegar e indicador

# zoom: a logo cresce com a mão (a palma mede a distância até a câmera, pois é rígida)
ZOOM_REF_PALM = 0.082    # palma, em fração da largura do quadro, na foto de referência
ZOOM_REF_LOGO = 0.27     # largura da logo, em fração do quadro, nessa distância
LOGO_WIDTH_LIMITS = (0.10, 0.65)  # largura mínima e máxima da logo, em fração do quadro

# posição da logo em relação à mão (proporções do tamanho da caixa da mão)
LOGO_OVERLAP = 0.2       # quanto a logo avança sobre a borda da mão
LOGO_HEIGHT_AT = 0.4     # centro vertical da logo, contado do topo da mão
LOGO_BOTTOM_MAX = 0.82   # a base da logo não passa daqui (acima do polegar): logos grandes crescem para cima
SMOOTHING = (0.5, 0.5, 0.3)  # peso do valor novo na suavização de x, y e largura

# confete nas cores da logo (BGR), com peso: o vermelho aparece menos que as outras cores
CONFETTI_COLORS = ((1, 212, 251), (36, 184, 2), (208, 52, 0), (255, 255, 255), (4, 4, 250))  # amarelo, verde, azul, branco, vermelho
CONFETTI_COLOR_WEIGHTS = (0.28, 0.28, 0.22, 0.12, 0.10)
CONFETTI_SHAPES = ("rect", "star", "diamond")      # retângulo, estrela da logo, losango da bandeira
CONFETTI_SHAPE_WEIGHTS = (0.5, 0.3, 0.2)
CONFETTI_COUNT = 120
CONFETTI_LIFE = (1.2, 2.0)       # segundos de vida de cada pedaço
CONFETTI_SPEED = (220, 640)      # px/s, num quadro de 640 px de largura
CONFETTI_GRAVITY = 900           # px/s²
CONFETTI_DRAG = 1.3              # fração da velocidade perdida por segundo
CONFETTI_FADE = 0.35             # segundos finais em que o pedaço encolhe até sumir
_STAR = np.array([[math.cos(math.radians(-90 + 36 * i)) * (1.0 if i % 2 == 0 else 0.42),
                   math.sin(math.radians(-90 + 36 * i)) * (1.0 if i % 2 == 0 else 0.42)] for i in range(10)])
_DIAMOND = np.array([[-1.15, 0.0], [0.0, -0.75], [1.15, 0.0], [0.0, 0.75]])

DETECT_WIDTH = 640       # largura máxima da cópia usada na detecção (mais rápido)
SHOW_AFTER_FRAMES = 3    # frames seguidos com "L" para a logo aparecer
HIDE_AFTER_FRAMES = 6    # frames seguidos sem "L" para a logo sumir


@dataclass
class LShape:
    is_l: bool
    index_reach: float
    others_reach: float
    thumb_open: float
    angle: float


def _dist(a, b):
    return float(np.linalg.norm(a - b))


def analyze_hand(pts):
    """Decide se a mão (21 pontos em pixels) está fazendo o "L"."""
    palm = max(_dist(pts[WRIST], pts[MIDDLE_MCP]), 1e-6)
    index_reach = _dist(pts[INDEX_TIP], pts[WRIST]) / palm
    others_reach = max(_dist(pts[t], pts[WRIST]) for t in (MIDDLE_TIP, RING_TIP, PINKY_TIP)) / palm
    thumb_open = _dist(pts[THUMB_TIP], pts[INDEX_MCP]) / palm

    v_index = pts[INDEX_TIP] - pts[INDEX_MCP]
    v_thumb = pts[THUMB_TIP] - pts[THUMB_MCP]
    cos = float(np.dot(v_index, v_thumb)) / max(np.linalg.norm(v_index) * np.linalg.norm(v_thumb), 1e-6)
    angle = math.degrees(math.acos(max(-1.0, min(1.0, cos))))

    is_l = (
        index_reach >= INDEX_MIN_REACH
        and others_reach <= OTHERS_MAX_REACH
        and thumb_open >= THUMB_MIN_OPEN
        and ANGLE_RANGE[0] <= angle <= ANGLE_RANGE[1]
    )
    return LShape(is_l, index_reach, others_reach, thumb_open, angle)


def hand_points(landmarks, width, height):
    return np.array([[lm.x * width, lm.y * height] for lm in landmarks], dtype=np.float32)


def ensure_model():
    if MODEL_PATH.exists():
        return
    print("Baixando o modelo de mãos do MediaPipe (uma vez só)...")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)


def make_landmarker(running_mode):
    options = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=running_mode,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.HandLandmarker.create_from_options(options)


def load_logo(path=None):
    """Lê a logo (padrão: assets/logo.png), sem as bordas transparentes e com a cor já multiplicada
    pelo alfa (BGRA). Se o arquivo não existir, gera uma logo provisória.
    """
    path = Path(path) if path else LOGO_PATH
    if path.exists():
        bgra = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if bgra is None:
            sys.exit(f"Não consegui ler a logo em {path}")
        if bgra.ndim == 2:
            bgra = cv2.cvtColor(bgra, cv2.COLOR_GRAY2BGRA)
        elif bgra.shape[2] == 3:
            bgra = cv2.cvtColor(bgra, cv2.COLOR_BGR2BGRA)
    else:
        print(f"Logo não encontrada em {path} - usando uma logo provisória (veja assets/README.md).")
        bgra = np.zeros((300, 640, 4), dtype=np.uint8)
        font, text, origin = cv2.FONT_HERSHEY_TRIPLEX, "LULA", (30, 230)
        cv2.putText(bgra, text, origin, font, 6.0, (255, 255, 255, 255), 26, cv2.LINE_AA)
        cv2.putText(bgra, text, origin, font, 6.0, (30, 30, 220, 255), 12, cv2.LINE_AA)

    ys, xs = np.nonzero(bgra[..., 3] > 10)
    bgra = bgra[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    bgra[..., :3] = (bgra[..., :3].astype(np.uint16) * bgra[..., 3:4] // 255).astype(np.uint8)
    return bgra


def palm_size(pts):
    """Tamanho da palma (pulso e base do indicador e do mindinho): quanto maior, mais perto da câmera."""
    return float(np.mean([_dist(pts[WRIST], pts[INDEX_MCP]), _dist(pts[WRIST], pts[PINKY_MCP]),
                          _dist(pts[INDEX_MCP], pts[PINKY_MCP])]))


def logo_placement(pts, frame_w, frame_h, logo_aspect, scale_mul=1.0, zoom=1.0):
    """Retorna (cx, cy, largura) da logo: ao lado da mão, do lado para onde o polegar aponta.

    A largura acompanha a palma elevada a `zoom` (1 = proporcional à proximidade da câmera).
    """
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    size = float(max(x1 - x0, y1 - y0))
    lo, hi = LOGO_WIDTH_LIMITS
    palm_fraction = palm_size(pts) / frame_w
    width_fraction = ZOOM_REF_LOGO * (palm_fraction / ZOOM_REF_PALM) ** zoom * scale_mul
    width = float(np.clip(width_fraction, lo, hi)) * frame_w
    height = width * logo_aspect

    def center_x(on_right):
        if on_right:
            return x1 - size * LOGO_OVERLAP + width / 2
        return x0 + size * LOGO_OVERLAP - width / 2

    on_right = bool(pts[THUMB_TIP][0] > pts[INDEX_MCP][0])
    cx = center_x(on_right)
    if cx - width / 2 < 0 or cx + width / 2 > frame_w:  # não cabe desse lado: tenta o outro
        other = center_x(not on_right)
        if 0 <= other - width / 2 and other + width / 2 <= frame_w:
            cx = other
    cx = float(np.clip(cx, width / 2, frame_w - width / 2))
    cy = y0 + size * min(LOGO_HEIGHT_AT, LOGO_BOTTOM_MAX - height / 2 / size)
    cy = float(np.clip(cy, height / 2, frame_h - height / 2))
    return cx, cy, width


def draw_logo(frame, logo, cx, cy, width, alpha=1.0):
    """Cola a logo (BGRA pré-multiplicada) no frame (BGR), centrada em (cx, cy) com a largura dada."""
    if width < 2 or alpha <= 0:
        return
    h0, w0 = logo.shape[:2]
    w = int(round(width))
    h = max(1, int(round(w * h0 / w0)))
    resized = cv2.resize(logo, (w, h), interpolation=cv2.INTER_AREA if w < w0 else cv2.INTER_LINEAR)

    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    fx0, fy0 = max(x0, 0), max(y0, 0)
    fx1, fy1 = min(x0 + w, frame.shape[1]), min(y0 + h, frame.shape[0])
    if fx1 <= fx0 or fy1 <= fy0:
        return

    crop = resized[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    cover = cv2.convertScaleAbs(crop[..., 3], alpha=alpha)
    color = cv2.convertScaleAbs(crop[..., :3], alpha=alpha)
    roi = frame[fy0:fy1, fx0:fx1]
    behind = cv2.multiply(roi, cv2.bitwise_not(cv2.merge([cover] * 3)), scale=1 / 255)
    roi[:] = cv2.add(behind, color)


def confetti_polygon(shape, flip):
    """Contorno de um pedaço de confete de raio 1; `flip` simula o giro em 3D do retângulo."""
    if shape == "star":
        return _STAR
    if shape == "diamond":
        return _DIAMOND
    half_height = 0.5 * (abs(math.cos(flip)) * 0.85 + 0.15)
    return np.array([[-1.2, -half_height], [1.2, -half_height], [1.2, half_height], [-1.2, half_height]])


class Confetti:
    """Explosão de confete: os pedaços giram, caem e encolhem até sumir."""

    def __init__(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.p = {}

    def __len__(self):
        return len(self.p.get("age", ()))

    def burst(self, cx, cy, width, height, frame_w, count=CONFETTI_COUNT):
        """Solta o confete a partir da logo (centro cx, cy), espalhado pela área dela."""
        rng = self.rng
        scale = frame_w / 640
        size_mul = float(np.clip((width / frame_w / ZOOM_REF_LOGO) ** 0.5, 0.8, 1.5))  # logo maior, confete maior
        pos = np.stack([cx + rng.uniform(-0.5, 0.5, count) * width,
                        cy + rng.uniform(-0.5, 0.5, count) * height], axis=1)

        # sai do centro para fora, com um pouco de aleatoriedade e um empurrão para cima
        direction = pos - [cx, cy] + rng.normal(0, 0.35 * width / 2, (count, 2))
        direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-6)
        vel = direction * (rng.uniform(*CONFETTI_SPEED, count) * scale)[:, None]
        vel[:, 1] -= 160 * scale

        new = {
            "pos": pos, "vel": vel,
            "angle": rng.uniform(0, 2 * math.pi, count), "spin": rng.uniform(-10, 10, count),
            "flip": rng.uniform(0, 2 * math.pi, count), "flip_speed": rng.uniform(4, 12, count),
            "size": rng.uniform(6, 13, count) * scale * size_mul,
            "age": np.zeros(count), "life": rng.uniform(*CONFETTI_LIFE, count),
            "color": rng.choice(len(CONFETTI_COLORS), count, p=CONFETTI_COLOR_WEIGHTS),
            "shape": rng.choice(len(CONFETTI_SHAPES), count, p=CONFETTI_SHAPE_WEIGHTS),
        }
        for key, value in new.items():
            self.p[key] = np.concatenate([self.p[key], value]) if key in self.p else value

    def step(self, dt, frame_w):
        if not len(self):
            return
        p, dt = self.p, min(dt, 0.1)
        p["vel"][:, 1] += CONFETTI_GRAVITY * (frame_w / 640) * dt
        p["vel"] *= math.exp(-CONFETTI_DRAG * dt)
        p["pos"] += p["vel"] * dt
        p["angle"] += p["spin"] * dt
        p["flip"] += p["flip_speed"] * dt
        p["age"] += dt
        alive = p["age"] < p["life"]
        if not alive.all():
            for key in p:
                p[key] = p[key][alive]

    def draw(self, frame):
        p = self.p
        for i in range(len(self)):
            radius = p["size"][i] * min(1.0, (p["life"][i] - p["age"][i]) / CONFETTI_FADE)
            if radius < 1.0:
                continue
            c, s = math.cos(p["angle"][i]), math.sin(p["angle"][i])
            outline = confetti_polygon(CONFETTI_SHAPES[p["shape"][i]], p["flip"][i]) * radius
            poly = (outline @ np.array([[c, s], [-s, c]]) + p["pos"][i]).round().astype(np.int32)
            color = CONFETTI_COLORS[p["color"][i]]
            cv2.fillPoly(frame, [poly], color, cv2.LINE_AA)
            cv2.polylines(frame, [poly], True, tuple(int(v * 0.55) for v in color), 1, cv2.LINE_AA)


def draw_debug(frame, pts, shape):
    color = (0, 200, 0) if shape.is_l else (0, 140, 255)
    for x, y in pts:
        cv2.circle(frame, (int(x), int(y)), 3, color, -1, cv2.LINE_AA)
    x0, y0 = pts.min(axis=0)
    label = (
        f"{'L' if shape.is_l else '-'} idx={shape.index_reach:.2f} oth={shape.others_reach:.2f} "
        f"thb={shape.thumb_open:.2f} ang={shape.angle:.0f}"
    )
    cv2.putText(frame, label, (int(x0), max(int(y0) - 8, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)


def reject_same_file(input_path, output_path, input_flag, output_flag):
    """Encerra o programa se a saída apontar para o mesmo arquivo da entrada (que seria sobrescrito).

    Compara pelo arquivo de verdade (os.path.samefile), então pega caminhos escritos de outro jeito,
    maiúsculas/minúsculas diferentes no Windows, links simbólicos e hard links.
    """
    if not input_path or not output_path:
        return
    if os.path.exists(input_path) and os.path.exists(output_path) and os.path.samefile(input_path, output_path):
        sys.exit(f"{output_flag} aponta para o mesmo arquivo de {input_flag} ({input_path}). "
                 "Escolha outro nome, para não sobrescrever o original.")


def run_image(args):
    reject_same_file(args.image, args.out, "--image", "--out")
    frame = cv2.imread(args.image)
    if frame is None:
        sys.exit(f"Não consegui ler a imagem {args.image}")
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    with make_landmarker(vision.RunningMode.IMAGE) as landmarker:
        result = landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

    logo = load_logo(args.logo)
    aspect = logo.shape[0] / logo.shape[1]
    hands, shapes, first_l = [], [], None
    print(f"{len(result.hand_landmarks)} mão(s) detectada(s) em {args.image}")
    for i, landmarks in enumerate(result.hand_landmarks):
        pts = hand_points(landmarks, w, h)
        shape = analyze_hand(pts)
        print(f"  mão {i}: L={shape.is_l}  index={shape.index_reach:.2f} others={shape.others_reach:.2f} "
              f"thumb={shape.thumb_open:.2f} angle={shape.angle:.0f}")
        hands.append(pts)
        shapes.append(shape)
        if shape.is_l and first_l is None:
            first_l = pts

    if first_l is not None:
        cx, cy, width = logo_placement(first_l, w, h, aspect, args.logo_scale, args.zoom)
        draw_logo(frame, logo, cx, cy, width)
        if args.confetti:
            confetti = Confetti(seed=args.seed)
            confetti.burst(cx, cy, width, width * aspect, w)
            confetti.step(0.45, w)  # um instante depois da explosão
            confetti.draw(frame)
    if args.debug:
        for pts, shape in zip(hands, shapes):
            draw_debug(frame, pts, shape)
    cv2.imwrite(args.out, frame)
    print(f"Salvo em {args.out}")


def open_source(args):
    if args.video:
        cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            sys.exit(f"Não consegui abrir o vídeo {args.video}")
        return cap
    index = args.camera
    api = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, api)
    if not cap.isOpened():
        sys.exit(f"Não consegui abrir a câmera {index}. Tente outro número com --camera.")
    # MJPG + resolução baixa: muitas webcams só chegam a 30 fps assim (a C922 faz 10 fps em 720p)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap


def open_writer(args, width, height):
    """Abre o .mp4 de saída (--save), recusando sobrescrever o vídeo de entrada (--video)."""
    reject_same_file(args.video, args.save, "--video", "--save")
    return cv2.VideoWriter(args.save, cv2.VideoWriter_fourcc(*"mp4v"), 30, (width, height))


def run_webcam(args):
    logo = load_logo(args.logo)
    aspect = logo.shape[0] / logo.shape[1]

    with ExitStack() as stack:
        cap = open_source(args)
        stack.callback(cap.release)
        landmarker = stack.enter_context(make_landmarker(vision.RunningMode.VIDEO))
        stack.callback(cv2.destroyAllWindows)

        vcam = writer = None
        debug = args.debug
        l_frames = lost_frames = processed = 0
        visible = 0.0           # 0 = escondida, 1 = totalmente visível
        target = 0.0
        placement = None        # (cx, cy, largura) suavizado
        confetti = Confetti() if args.confetti else None
        start = last = time.perf_counter()
        last_ts = -1

        while True:
            ok, frame = cap.read()
            if not ok:
                print("Fim do vídeo." if args.video else "A câmera parou de enviar imagens.")
                break
            if args.mirror:
                frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            if args.virtual_cam and vcam is None:
                try:
                    import pyvirtualcam
                except ImportError:
                    sys.exit("A câmera virtual precisa do pyvirtualcam: pip install -r requirements-virtualcam.txt")
                try:
                    vcam = stack.enter_context(
                        pyvirtualcam.Camera(w, h, 30, fmt=pyvirtualcam.PixelFormat.BGR)
                    )
                except Exception as exc:
                    sys.exit(f"Não consegui abrir a câmera virtual (o OBS está instalado?): {exc}")
                print(f"Enviando para a câmera virtual: {vcam.device}")

            now = time.perf_counter()
            if args.max_seconds and now - start > args.max_seconds:
                break
            ts = max(int((now - start) * 1000), last_ts + 1)
            last_ts = ts
            small = frame if w <= DETECT_WIDTH else cv2.resize(frame, (DETECT_WIDTH, round(h * DETECT_WIDTH / w)))
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            result = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)

            processed += 1
            hands, shapes, l_hand = [], [], None
            for landmarks in result.hand_landmarks:
                pts = hand_points(landmarks, w, h)
                shape = analyze_hand(pts)
                hands.append(pts)
                shapes.append(shape)
                if shape.is_l and l_hand is None:
                    l_hand = pts

            if l_hand is not None:
                l_frames += 1
                lost_frames = 0
                if l_frames >= SHOW_AFTER_FRAMES:
                    new = logo_placement(l_hand, w, h, aspect, args.logo_scale, args.zoom)
                    if target == 0.0 and confetti is not None:  # a logo está surgindo
                        confetti.burst(new[0], new[1], new[2], new[2] * aspect, w)
                    target = 1.0
                    if placement is None or visible < 0.05:
                        placement = new
                    else:
                        placement = tuple(p + k * (n - p) for p, n, k in zip(placement, new, SMOOTHING))
            else:
                l_frames = 0
                lost_frames += 1
                if lost_frames >= HIDE_AFTER_FRAMES:
                    target = 0.0

            # animação de "pop": aproxima de target e dá um leve overshoot no tamanho
            dt = now - last
            last = now
            visible += (target - visible) * (1.0 - math.exp(-dt * 14.0))
            if visible > 0.01 and placement is not None:
                cx, cy, width = placement
                scale = visible * (1.0 + 0.18 * math.sin(math.pi * visible))
                draw_logo(frame, logo, cx, cy, width * scale, alpha=min(1.0, visible * 1.5))
            if confetti is not None:
                confetti.step(dt, w)
                confetti.draw(frame)
            if debug:
                for pts, shape in zip(hands, shapes):
                    draw_debug(frame, pts, shape)

            if args.save:
                if writer is None:
                    writer = open_writer(args, w, h)
                    stack.callback(writer.release)
                writer.write(frame)
            if vcam is not None:
                vcam.send(frame)
            if not args.no_preview:
                cv2.imshow(WINDOW, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break
                if key == ord("d"):
                    debug = not debug
            elif vcam is not None:
                vcam.sleep_until_next_frame()

        elapsed = time.perf_counter() - start
        print(f"{processed} frames em {elapsed:.1f}s ({processed / max(elapsed, 1e-6):.1f} fps)")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--camera", type=int, default=0, help="índice da webcam (padrão: 0)")
    p.add_argument("--width", type=int, default=640, help="largura pedida à webcam (padrão: 640)")
    p.add_argument("--height", type=int, default=360, help="altura pedida à webcam (padrão: 360)")
    p.add_argument("--logo", help="PNG da logo, com transparência (padrão: assets/logo.png)")
    p.add_argument("--zoom", type=float, default=1.0,
                   help="força do zoom: 1 = logo proporcional à proximidade da mão; maior exagera (padrão: 1)")
    p.add_argument("--logo-scale", type=float, default=1.0, help="multiplica o tamanho da logo (padrão: 1)")
    p.add_argument("--confetti", action=argparse.BooleanOptionalAction, default=True,
                   help="explosão de confete quando a logo surge (padrão: ligado)")
    p.add_argument("--seed", type=int, help="semente do confete no modo --image (resultado repetível)")
    p.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=True,
                   help="espelha a imagem como um selfie (padrão: ligado)")
    p.add_argument("--video", help="usa um arquivo de vídeo em vez da webcam")
    p.add_argument("--save", help="grava o resultado em um arquivo mp4")
    p.add_argument("--virtual-cam", action="store_true", help="envia o vídeo para a OBS Virtual Camera")
    p.add_argument("--no-preview", action="store_true", help="não abre a janela de preview")
    p.add_argument("--max-seconds", type=float, help="encerra sozinho depois de N segundos")
    p.add_argument("--debug", action="store_true", help="mostra landmarks e métricas")
    p.add_argument("--image", help="analisa uma imagem em vez da webcam")
    p.add_argument("--out", default="saida.png", help="arquivo de saída do modo --image")
    return p.parse_args()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    ensure_model()
    if args.image:
        run_image(args)
    else:
        run_webcam(args)


if __name__ == "__main__":
    main()
