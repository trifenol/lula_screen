# Logo

O programa lê a logo de `assets/logo.png` (ou do arquivo indicado em `--logo`). **A logo não faz parte deste repositório** e esta pasta fica vazia depois do `git clone`.

## Por que a logo não está no repositório

A logo da campanha pertence aos seus titulares. No [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Lula_2026_logo.svg) ela está marcada como domínio público (`PD-textlogo`) pelo critério dos EUA, mas a mesma página avisa que:

- o limiar de originalidade no Brasil é bem mais alto, então essa classificação pode não valer aqui; e
- a obra pode estar protegida como marca.

Por isso o projeto não distribui o arquivo. Quem usa é responsável por confirmar que pode usá-lo.

## Como obter

**Opção 1: baixar do Wikimedia Commons** (PNG com fundo transparente), na raiz do projeto:

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force assets | Out-Null
Invoke-WebRequest "https://commons.wikimedia.org/wiki/Special:FilePath/Lula_2026_logo.svg?width=1000" -OutFile assets/logo.png
```

```bash
# macOS / Linux
mkdir -p assets
curl -L "https://commons.wikimedia.org/wiki/Special:FilePath/Lula_2026_logo.svg?width=1000" -o assets/logo.png
```

**Opção 2: baixar à mão** a partir da página do arquivo na [Wikipédia em português](https://pt.wikipedia.org/wiki/Ficheiro:Lula_2026_logo.png) (um espelho do arquivo do Commons, com o mesmo status de direitos e os mesmos avisos). Salve o PNG como `assets/logo.png`.

**Opção 3: usar a sua própria imagem.** Qualquer PNG com transparência serve:

```bash
python faz_o_l.py --logo caminho/para/minha_logo.png
```

## Requisitos do arquivo

- PNG com canal alfa (fundo transparente). Sem transparência, o retângulo da imagem inteira é desenhado.
- Qualquer tamanho. O programa corta as bordas transparentes sozinho. Algo entre 800 e 1500 px de largura é suficiente.
- Funciona melhor com formato horizontal (a logo é posicionada ao lado da mão).

## Se não houver logo

O programa avisa e usa uma logo provisória (o texto "LULA"), só para você conseguir testar o resto.
