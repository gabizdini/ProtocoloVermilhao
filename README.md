# PROTOCOLO VERMILHÃO — OPERAÇÃO ÚLTIMA ENERGIA

Trabalho Prático 1 — Computação Gráfica · IFSULDEMINAS, Campus Machado · Prof. Renan · entrega: 11/11/2026
(Python + Pygame + PyOpenGL, API clássica).

**Integrantes:** Gabrieli Diniz e _[nome da dupla — preencher]_

## Objetivo do jogo
A estação espacial perdeu sua fonte principal de energia. Pilote o drone de manutenção, **colete os 5 núcleos
vermelhos**, desvie dos obstáculos e **entre no portal** quando ele for reativado. A iluminação faz parte da
história: a estação começa escura, com luz de emergência vermelha, e **se restaura aos poucos a cada núcleo coletado**.

## Como instalar
```bash
python -m pip install -r requirements.txt
```
(O jogo usa `pygame` **ou** `pygame-ce` — o código funciona com os dois. `opencv-python` só é necessário para
regerar as texturas.)

## Como executar
```bash
python main.py
```
Na tela inicial, pressione **ENTER**.

## Controles
| Tecla | Ação |
|---|---|
| W / S | avançar / recuar (em relação à câmera) |
| A / D | mover para a esquerda / direita |
| SETAS | girar e inclinar a câmera (opcional) |
| L | liga/desliga a **luz principal** (funciona em qualquer etapa da missão) |
| R | reinicia a missão sem fechar o programa |
| ESC | encerra |

## Iluminação progressiva
| Núcleos | O que acontece |
|---|---|
| 0/5 | estação escura; luzes de **emergência vermelhas** pulsando; luz principal fraca |
| 1–2 | painéis e indicadores começam a acender (luzes reais de painel nas paredes) |
| 3–4 | a iluminação geral aumenta gradualmente; a emergência vermelha enfraquece |
| 5/5 | energia principal restaurada: luz intensa, todos os painéis ativos, portal iluminado e aberto |

As transições usam `dt` (suaves e independentes de FPS). A tecla **L** só controla a luz principal (GL_LIGHT0);
as luzes de emergência, de painel e do portal são outros sistemas da estação.
Para mudar a posição da luz na apresentação: `POSICAO_LUZ_PRINCIPAL` em `config.py`.

## Organização dos arquivos
| Arquivo | Conteúdo |
|---|---|
| `main.py` | janela, loop principal (`dt`), eventos de teclado, reinício |
| `config.py` | todas as constantes: paleta, mapa, obstáculos, núcleos, luzes |
| `estado.py` | lógica do jogo (movimento, colisão, coleta, portal) — **sem OpenGL** |
| `iluminacao.py` | sistema de iluminação progressiva (calcula as 8 luzes) — **sem OpenGL** |
| `cena.py` | configuração do OpenGL, câmera, projeção em perspectiva, envio das luzes |
| `objetos.py` | desenho do cenário, drone, núcleos, portal, painéis |
| `primitivas.py` | caixa, prisma, esfera, octaedro, toro, grade, linhas (com normais e UVs) |
| `texturas.py` / `gerar_texturas.py` | carregamento e geração procedural das texturas |
| `hud.py` | menu, HUD e tela de vitória |
| `assets/texturas/` | 4 texturas PNG (geradas por código) |
| `testes/` | testes automáticos e script de capturas |
| `docs/` | relatório técnico e roteiro de apresentação |
| `capturas/` | capturas de tela reais do jogo |

## Texturas (origem)
Todas geradas por `gerar_texturas.py` (NumPy + OpenCV), autoria própria; nenhuma imagem externa.
`piso_metalico.png` (repete 10×10 no piso), `parede_painel.png`, `caixa_manutencao.png`, `painel_energia.png`.

## Testes
```bash
python testes/teste_logica.py        # lógica: colisão, coleta, portal, reinício, dt, iluminação (sem janela)
python testes/teste_integracao.py    # abre a janela: teclas, erros de OpenGL, hélices, tecla L
python testes/capturar_telas.py      # joga a missão com piloto automático e salva capturas em capturas/
```

## Tecnologias
Python 3 · Pygame/Pygame-CE (janela, teclado, fonte) · PyOpenGL (OpenGL clássico: `glBegin/glEnd`,
`glPushMatrix/glPopMatrix`, iluminação fixa, texturas 2D, display lists) · NumPy e OpenCV (texturas).
Sem shaders, sem engines externas.
