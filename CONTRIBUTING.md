# Contribuindo

Obrigado por querer ajudar. Este projeto recebe muito acesso, então as regras abaixo existem para manter o código fácil de manter e o repositório seguro para todo mundo.

## Antes de começar

- Procure nas [issues](https://github.com/trifenol/lula_screen/issues) se já existe o que você quer fazer ou relatar.
- Para mudanças grandes, abra uma issue antes e converse. Isso evita trabalho perdido.

## Ambiente

```bash
git clone https://github.com/trifenol/lula_screen.git
cd lula_screen
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
```

Se o `pip` falhar com erro de certificado (proxy), use `uv pip install --native-tls -r requirements-dev.txt`. **Não desative a verificação de SSL.**

## Como contribuir com código

1. Crie uma branch a partir da `main`.
2. Faça a mudança e **escreva ou ajuste testes**. A lógica pura (gesto, posição, zoom, confete, desenho) tem testes em `tests/`, que não precisam de câmera.
3. Rode tudo antes de abrir o pull request:
   ```bash
   pytest
   ruff check faz_o_l.py tests --select F,E9
   ```
4. Se mudar o comportamento, atualize o README e os arquivos em `docs/`.
5. Abra o pull request explicando **o que** mudou e **por que**.

### Estilo

- Python 3.11. Comentários e mensagens para o usuário em português (como no restante do código) e identificadores em inglês.
- Parâmetros que alguém queira ajustar ficam como constantes no topo de `faz_o_l.py`, com um comentário curto.
- Prefira funções pequenas e puras (entrada → saída) para a lógica, para poder testar sem câmera.
- Não adicione dependências sem necessidade. Se for preciso, justifique no pull request e verifique a licença.

## Reportando problemas

Use o modelo de [bug report](https://github.com/trifenol/lula_screen/issues/new?template=bug_report.md). Inclua o sistema, a versão do Python, a câmera, o comando que rodou e a saída do terminal.

**Não anexe fotos ou vídeos com o seu rosto ou o de outras pessoas.** Para problemas de reconhecimento do gesto, as métricas do modo `--debug` (`idx`, `oth`, `thb`, `ang`) bastam.

## O que não entra neste repositório

- **Logos, imagens, vídeos ou músicas de terceiros.** A logo da campanha não é versionada (veja `assets/README.md`). Não faça commit de arquivos de mídia que você não tenha o direito de redistribuir.
- **Dados pessoais:** fotos de pessoas, chaves de API, tokens, senhas ou e-mails pessoais.
- **Conteúdo que se passe por outra pessoa, engane eleitores ou assedie.** Isso inclui personificação, conteúdo gerado para parecer real e que não seja, desinformação e ataques pessoais. O programa serve para uma brincadeira de apoio com uma sobreposição gráfica, não para enganar.
- **Funcionalidades que violem a legislação eleitoral brasileira** ou os termos de uso de plataformas.

Pull requests e issues que não seguirem essas regras podem ser fechados sem discussão.

## Licença

Ao contribuir, você concorda que o seu código será distribuído sob a [licença MIT](LICENSE) do projeto.
