# Lula Screen: "Faz o L"

[![CI](https://github.com/trifenol/lula_screen/actions/workflows/ci.yml/badge.svg)](https://github.com/trifenol/lula_screen/actions/workflows/ci.yml)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)

Faça o **"L"** com a mão na frente da webcam e a **logo da campanha** aparece ao lado dela, com uma **explosão de confete** nas cores da logo. Quanto mais perto da câmera a sua mão está, maior a logo fica (**zoom**).

Funciona em tempo real, roda 100% no seu computador e pode ser enviado para o **Zoom, Meet, Teams** ou qualquer app de vídeo pela câmera virtual do OBS.

- [Como funciona](#como-funciona)
- [Instalação](#instalação)
- [Uso](#uso)
- [Usar em videochamadas](#usar-em-videochamadas)
- [Opções](#opções)
- [Ajustes finos](#ajustes-finos)
- [Solução de problemas](#solução-de-problemas)
- [Privacidade](#privacidade)
- [Desenvolvimento](#desenvolvimento)
- [Documentação](#documentação)
- [Créditos e licenças](#créditos-e-licenças)
- [Aviso legal](#aviso-legal)

## Como funciona

```
webcam → detecção da mão (MediaPipe) → é um "L"? → logo ao lado da mão + zoom + confete → tela / câmera virtual
```

1. O [MediaPipe](https://ai.google.dev/edge/mediapipe) acha as mãos no vídeo e devolve 21 pontos de cada uma.
2. Uma regra geométrica decide se a mão forma um "L": indicador esticado, polegar aberto num ângulo de 40° a 135° com o indicador, e os outros três dedos dobrados. A regra não depende da rotação, do tamanho nem de qual mão é.
3. Se o "L" se mantém por 3 quadros seguidos, a logo surge com uma animação de "pop", do lado para onde o polegar aponta, e o confete explode.
4. O tamanho da logo acompanha a **palma da mão**, que mede a distância até a câmera: mão perto, logo grande; mão longe, logo pequena.
5. Quando você abaixa a mão (6 quadros sem o "L"), a logo some.

Os detalhes técnicos estão em [docs/COMO_FUNCIONA.md](docs/COMO_FUNCIONA.md).

## Instalação

### Requisitos

- **Python 3.11** (testado). Versões próximas devem funcionar.
- Uma webcam.
- Windows 11 (único sistema em que foi testado). Em macOS e Linux o código deve funcionar, mas não foi verificado.

### Passo a passo

```bash
git clone https://github.com/trifenol/lula_screen.git
cd lula_screen

python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# macOS / Linux:         source .venv/bin/activate

pip install -r requirements.txt
```

Na primeira execução o programa baixa o modelo de mãos do MediaPipe (cerca de 7,5 MB) para a pasta `models/`.

### A logo

**A logo não vem no repositório**, por questões de direitos. Siga [assets/README.md](assets/README.md) para baixá-la (um comando) ou usar a sua. Sem ela, o programa usa um "LULA" provisório, só para você testar.

## Uso

```bash
python faz_o_l.py
```

Uma janela abre com a imagem da câmera. Faça o "L". Para sair, aperte `q` ou `ESC`. Aperte `d` para ver os pontos da mão e as métricas do gesto (útil para ajustar).

Outros exemplos:

```bash
python faz_o_l.py --zoom 1.5                 # exagera o zoom
python faz_o_l.py --no-confetti              # sem confete
python faz_o_l.py --logo minha_logo.png      # outra logo
python faz_o_l.py --camera 1                 # outra câmera
python faz_o_l.py --image foto.png --out saida.png                       # testa numa foto
python faz_o_l.py --video entrada.mp4 --save saida.mp4 --no-preview      # processa um vídeo
```

## Usar em videochamadas

O programa pode enviar o vídeo para uma câmera virtual, que o Zoom, o Meet e o Teams enxergam como uma webcam comum.

1. Instale o [OBS Studio](https://obsproject.com/) (ele fornece a "OBS Virtual Camera"). No Windows: `winget install OBSProject.OBSStudio`.
2. Instale a dependência opcional: `pip install -r requirements-virtualcam.txt`.
3. Rode o programa:
   ```bash
   python faz_o_l.py --virtual-cam --no-mirror
   ```
4. No app de vídeo, escolha **OBS Virtual Camera** como câmera. O programa precisa estar rodando antes de você abrir ou trocar a câmera.

Use `--no-mirror` para quem está na chamada ver você como os outros veem (sem o efeito de espelho de selfie).

> A câmera virtual foi testada no Windows com o OBS 32. O pyvirtualcam também suporta macOS (via OBS) e Linux (via `v4l2loopback`), mas esses caminhos não foram testados.

## Opções

| Opção | Padrão | O que faz |
|---|---|---|
| `--camera N` | `0` | Índice da webcam. |
| `--width`, `--height` | `640`, `360` | Resolução pedida à câmera. Veja [Quadros por segundo baixos](#quadros-por-segundo-baixos). |
| `--logo ARQUIVO` | `assets/logo.png` | PNG da logo, com transparência. |
| `--zoom N` | `1.0` | Força do zoom. `1` = proporcional à proximidade da mão; maior exagera, menor suaviza. |
| `--logo-scale N` | `1.0` | Multiplica o tamanho da logo. |
| `--confetti` / `--no-confetti` | ligado | Explosão de confete quando a logo surge. |
| `--seed N` | | Semente do confete no modo `--image` (resultado repetível). |
| `--mirror` / `--no-mirror` | ligado | Espelha a imagem como um selfie. |
| `--virtual-cam` | | Envia o vídeo para a OBS Virtual Camera. |
| `--no-preview` | | Não abre a janela de preview. |
| `--video ARQUIVO` | | Usa um vídeo em vez da webcam. |
| `--save ARQUIVO` | | Grava o resultado em um `.mp4`. |
| `--image ARQUIVO` | | Analisa uma imagem em vez da webcam. |
| `--out ARQUIVO` | `saida.png` | Arquivo de saída do modo `--image`. |
| `--max-seconds N` | | Encerra sozinho depois de N segundos. |
| `--debug` | | Mostra os pontos da mão e as métricas. |

Teclas na janela: `q` ou `ESC` sai; `d` liga e desliga o modo debug.

`--save` e `--out` recusam o mesmo arquivo de `--video` e `--image`, para você não sobrescrever o original por engano.

## Ajustes finos

As constantes ficam no topo de [faz_o_l.py](faz_o_l.py):

| Constante | O que controla |
|---|---|
| `INDEX_MIN_REACH`, `OTHERS_MAX_REACH`, `THUMB_MIN_OPEN`, `ANGLE_RANGE` | Quão rígida é a regra do "L". Use `--debug` para ver os valores da sua mão. |
| `SHOW_AFTER_FRAMES`, `HIDE_AFTER_FRAMES` | Quantos quadros seguidos até a logo aparecer ou sumir. |
| `ZOOM_REF_PALM`, `ZOOM_REF_LOGO` | Calibração do zoom: a palma ocupa 8,2% do quadro quando a logo ocupa 27%. |
| `LOGO_WIDTH_LIMITS` | Tamanho mínimo e máximo da logo (10% a 65% da largura do quadro). |
| `LOGO_OVERLAP`, `LOGO_HEIGHT_AT`, `LOGO_BOTTOM_MAX` | Posição da logo em relação à mão. |
| `SMOOTHING` | Suavização do movimento da logo (mais alto = mais rápido, mais tremido). |
| `CONFETTI_*` | Quantidade, cores, proporção das cores, formas, duração, velocidade e gravidade do confete. |

## Solução de problemas

### O "L" não é reconhecido

- Mostre a palma da mão para a câmera, com o indicador para cima e o polegar para o lado.
- Dobre bem os outros três dedos.
- Melhore a luz e afaste a mão da câmera (mãos muito pequenas ou muito cortadas pela borda da imagem não são detectadas).
- Aperte `d` e veja as métricas: `idx` (indicador), `oth` (outros dedos), `thb` (polegar) e `ang` (ângulo). Compare com os limites e ajuste as constantes.

### Abre a câmera errada

Use `--camera 1`, `--camera 2`... A ordem do OpenCV pode incluir câmeras virtuais. No Windows, para listar os nomes:

```bash
ffmpeg -list_devices true -f dshow -i dummy
```

### Quadros por segundo baixos

Muitas webcams só chegam a 30 fps em resoluções menores. Numa Logitech C922, 1280x720 dá 10 fps e 640x360 em MJPG dá 30 fps. Por isso o padrão é 640x360. Teste outras resoluções com `--width` e `--height`.

### Erro de certificado SSL ao instalar (`CERTIFICATE_VERIFY_FAILED`)

Acontece atrás de proxies que interceptam HTTPS. **Não desative a verificação.** Instale com o [uv](https://docs.astral.sh/uv/), que usa o repositório de certificados do sistema:

```bash
uv pip install --native-tls -r requirements.txt
```

### `Não consegui abrir a câmera virtual`

- Confirme que o OBS Studio está instalado.
- Se o erro persistir, abra o OBS, inicie a "Câmera Virtual" uma vez e feche-o. Em algumas instalações isso é preciso para registrar o driver (no teste feito no Windows, funcionou logo depois de instalar o OBS).
- Feche outros programas que estejam usando a câmera virtual.

### `A câmera virtual precisa do pyvirtualcam`

Rode `pip install -r requirements-virtualcam.txt`.

### Não consegui baixar o modelo

Baixe [hand_landmarker.task](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task) e coloque em `models/hand_landmarker.task`.

### `AttributeError: module 'mediapipe' has no attribute 'solutions'`

O código usa a API nova do MediaPipe (`HandLandmarker`, da Tasks API), não a antiga `mp.solutions`. Esse erro vem de outro programa ou de uma versão incompatível instalada no mesmo ambiente.

## Privacidade

- **O vídeo é processado só no seu computador.** O programa não envia imagens da câmera para nenhum servidor.
- A única conexão de rede é o download do modelo de mãos (cerca de 7,5 MB) de `storage.googleapis.com`, na primeira execução.
- Ao abrir uma câmera virtual, quem está na chamada vê o que o programa envia (a sua imagem com a logo e o confete).

## Desenvolvimento

```bash
pip install -r requirements-dev.txt
pytest                                      # testes (não precisam de câmera nem do modelo)
ruff check faz_o_l.py tests --select F,E9   # lint
```

Estrutura:

```
faz_o_l.py                 programa (detecção, gesto, logo, confete, saídas)
tests/                     testes automatizados (mãos sintéticas, sem câmera)
docs/COMO_FUNCIONA.md      explicação técnica e decisões de projeto
docs/IDENTIDADE_VISUAL.md  pesquisa sobre a identidade visual e a paleta usada
assets/                    onde fica a logo (não versionada)
requirements*.txt          dependências (execução, câmera virtual, desenvolvimento)
```

Contribuições são bem-vindas. Leia o [CONTRIBUTING.md](CONTRIBUTING.md) antes.

## Documentação

- [Como funciona](docs/COMO_FUNCIONA.md): pipeline, regra do gesto, zoom, confete, desempenho e decisões de projeto.
- [Identidade visual](docs/IDENTIDADE_VISUAL.md): pesquisa sobre a comunicação da campanha e a paleta medida na logo.
- [Logo](assets/README.md): como obter e usar a logo.
- [Contribuindo](CONTRIBUTING.md).

## Créditos e licenças

O código deste repositório é distribuído sob a [licença MIT](LICENSE). Ela **não cobre a logo** nem outros materiais de terceiros.

Dependências e ferramentas:

| Projeto | Licença | Uso |
|---|---|---|
| [MediaPipe](https://github.com/google-ai-edge/mediapipe) (Google) | Apache-2.0 | Detecção das mãos. O modelo baixado tem model card próprio. |
| [OpenCV](https://opencv.org/) | Apache-2.0 | Captura, desenho e vídeo. |
| [NumPy](https://numpy.org/) | BSD-3-Clause | Cálculos. |
| [pyvirtualcam](https://github.com/letmaik/pyvirtualcam) | GPL-2.0 | **Opcional**, instalado à parte, só para `--virtual-cam`. |
| [OBS Studio](https://obsproject.com/) | GPL-2.0 | **Opcional**, instalado à parte, fornece a câmera virtual. |

## Aviso legal

- Este é um projeto de código aberto, **independente e não oficial**. Nomes, marcas e a logo citados pertencem aos respectivos titulares.
- O programa apenas sobrepõe uma imagem (logo) e partículas (confete) ao vídeo da câmera. Ele não gera nem altera rostos, vozes ou falas.
- O uso em material de propaganda eleitoral está sujeito à legislação eleitoral brasileira (Lei nº 9.504/1997 e resoluções do TSE). Cada pessoa é responsável pelo uso que faz do programa e pelo conteúdo que produz com ele.
- O software é fornecido "como está", sem garantias (veja a [licença](LICENSE)).
