# Identidade visual

Notas da pesquisa feita para escolher as **cores e as formas do confete**. Parte vem de reportagens e parte foi **medida diretamente na logo**. A pesquisa foi feita em 11/10/2026, e a campanha segue em andamento, então alguns pontos podem mudar.

> **Limites desta pesquisa.** Não foi encontrado manual de marca oficial, tipografia documentada nem a autoria da logo. As informações de imprensa vieram de resumos de páginas e algumas reportagens são de 2025 e falam de planos, não de peças finais. Trate o que está na seção "Comunicação da campanha" como contexto, não como especificação.

## Paleta medida na logo

Medida nos pixels opacos do arquivo da logo (valor mediano de cada grupo de cor). Estas são as cores do confete.

| Cor | Hex | RGB | BGR (OpenCV) | Parte da logo |
|---|---|---|---|---|
| Vermelho | `#FA0404` | 250, 4, 4 | 4, 4, 250 | 39% dos pixels (a placa de "LULA") |
| Branco | `#FFFFFF` | 255, 255, 255 | 255, 255, 255 | 23% (as letras) |
| Amarelo | `#FBD401` | 251, 212, 1 | 1, 212, 251 | 12% (a placa do "13" e o losango da bandeira) |
| Azul | `#0034D0` | 0, 52, 208 | 208, 52, 0 | 9% (a placa de "VICE ALCKMIN" e o disco da bandeira) |
| Verde | `#02B824` | 2, 184, 36 | 36, 184, 2 | 8% (a placa de "PRESIDENTE" e o campo da bandeira) |

No confete as cores têm pesos diferentes (amarelo 0,28; verde 0,28; azul 0,22; branco 0,12; vermelho 0,10). O vermelho aparece menos que as demais porque a diretriz de comunicação divulgada foi usar mais verde, amarelo, azul e branco (veja abaixo), apesar de o vermelho ser a cor dominante da logo.

## Linguagem gráfica da logo

Observada no arquivo:

- **Placas coloridas** de cantos cortados (como retângulos chanfrados), cada uma com uma informação: "PRESIDENTE" em verde, a estrela vermelha numa placa branca, "13" em amarelo, "VICE ALCKMIN" em azul e a bandeira do Brasil numa placa verde.
- **Perspectiva e extrusão em 3D**: o bloco vermelho de "LULA" é inclinado e tem profundidade.
- **Estrela de cinco pontas** vermelha (o símbolo do partido), numa placa de cinza muito claro, e a **bandeira do Brasil** (campo verde, losango amarelo e disco azul) numa placa verde.
- **Tipografia** de display, pesada. "LULA" e "13" em fontes largas e extrapesadas; "PRESIDENTE", "VICE" e "ALCKMIN" condensadas.

Daí saíram as três formas do confete: retângulo (confete clássico), estrela e losango (o da bandeira).

## Comunicação da campanha

### Slogan e coligação

- O slogan é **"O Brasil Pronto Para Mais!"**, também nome da coligação de 7 partidos que apoia a chapa Lula–Alckmin ([PT](https://pt.org.br/o-brasil-pronto-pra-mais-lula-e-alckmin-defendem-legado-e-projetam-o-futuro/)).
- A secretária adjunta de Comunicação do PT, Camila Moreno, descreve o Brasil da campanha como um país "com energia, com esperança" e resume: "se muito vale o que foi feito, mais vale o que será" (mesma fonte).
- Uma frase usada em peças e figurinhas: "o Brasil é dos brasileiros".

### Cores: verde, amarelo, azul e branco

- Em setembro de 2025, o secretário de Comunicação do PT, Éden Valadares, disse sobre o programa de TV: "Nosso programa terá muito verde, amarelo, azul e branco. Vamos mostrar as cores e as caras do Brasil". A matéria diz que o partido buscava "desavermelhar" a imagem e que o conteúdo mostraria a Amazônia, o sertão, os pampas e os grandes centros urbanos ([InfoMoney / Estadão Conteúdo, 27/09/2025](https://www.infomoney.com.br/?p=3041963)).
- Em junho de 2026 a linha continuou: retomar as cores da bandeira, com o tema inicial da Copa do Mundo. Lula disse que a esquerda precisa "aprender a usar" o verde e amarelo ([Folha de Pernambuco, 10/06/2026](https://www.folhape.com.br/politica/pt-aposta-em-verde-amarelo-e-traca-estrategia-para-ampliar-presenca-de/492940/)).

### Tom e canais

- **Popular e festivo.** O jingle lançado em 26/07/2026 adapta o "Rap do Silva", um funk dos anos 90, e conta a trajetória de Lula como a de um brasileiro comum ([Correio Braziliense](https://www.correiobraziliense.com.br/politica/2026/07/amp/7468483-presidente-lula-lanca-jingle-de-campanha-inspirado-em-rap-do-silva.html)). Reportagens também citam um remake do "Lula Lá" planejado.
- **Redes e militância.** O PT montou uma rede de grupos em aplicativos de mensagem para distribuir conteúdo à militância, com a ideia de usar uma linguagem mais direta e uma produção mais rápida ([Folha de Pernambuco](https://www.folhape.com.br/politica/pt-aposta-em-verde-amarelo-e-traca-estrategia-para-ampliar-presenca-de/492940/)).
- **Figurinhas de WhatsApp** inspiradas na identidade visual da campanha, com a bandeira do Brasil, o chapéu e **emoticons de Lula fazendo o gesto do "L"** ([Metrópoles](https://www.metropoles.com/colunas/milena-teixeira/campanha-de-lula-lanca-pacotao-de-figurinhas-para-zap-veja)). Essa é a ligação direta com o gesto que este programa reconhece, mas vem de uma única matéria.

## Para atualizar o confete

As cores e formas ficam no topo de [faz_o_l.py](../faz_o_l.py):

```python
CONFETTI_COLORS = ((1, 212, 251), (36, 184, 2), (208, 52, 0), (255, 255, 255), (4, 4, 250))  # BGR
CONFETTI_COLOR_WEIGHTS = (0.28, 0.28, 0.22, 0.12, 0.10)
CONFETTI_SHAPES = ("rect", "star", "diamond")
```

Se você usar outra logo, meça a paleta dela e troque esses valores. O trecho abaixo lista as cores dominantes de um PNG com transparência:

```python
import cv2, numpy as np

img = cv2.imread("assets/logo.png", cv2.IMREAD_UNCHANGED)
pixels = img[..., :3][img[..., 3] > 250][:, ::-1]          # RGB dos pixels opacos
bins = (pixels // 8) * 8 + 4                                 # agrupa tons parecidos
colors, counts = np.unique(bins, axis=0, return_counts=True)
for i in np.argsort(-counts)[:8]:
    r, g, b = colors[i]
    print(f"#{r:02X}{g:02X}{b:02X}  {100 * counts[i] / counts.sum():.1f}%")
```
