---
name: Relatar um problema
about: O programa não funciona como esperado
title: ""
labels: bug
---

> **Privacidade:** não anexe fotos ou vídeos com o seu rosto ou o de outras pessoas.

## O que aconteceu

<!-- Descreva o problema e o que você esperava. -->

## Como reproduzir

Comando que você rodou:

```
python faz_o_l.py ...
```

## Ambiente

- Sistema operacional:
- Versão do Python (`python --version`):
- Câmera (modelo) e se é USB, integrada ou virtual:
- Versões das bibliotecas (`pip list | findstr -i "opencv mediapipe numpy pyvirtualcam"`, ou `grep -i` no macOS/Linux):

## Saída do terminal

```
<!-- cole aqui as mensagens de erro -->
```

## Se for sobre o reconhecimento do "L"

Rode com `--debug` (ou aperte `d`) e anote os valores que aparecem ao lado da mão quando você faz o gesto:

- `idx` (precisa ser maior ou igual a 1,6):
- `oth` (precisa ser menor ou igual a 1,5):
- `thb` (precisa ser maior ou igual a 0,7):
- `ang` (precisa estar entre 40 e 135):
