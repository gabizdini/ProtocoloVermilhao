# -*- coding: utf-8 -*-
"""
config.py — Todas as constantes do jogo em um único lugar.

Por que isso é útil na apresentação?  Se o professor pedir "mude a velocidade do drone",
"mude a posição da luz" ou "mude a escala de um objeto", basta alterar um valor aqui.

Convenção de eixos (a mesma usada em todo o projeto):
    X -> direita        Y -> para cima        Z -> em direção ao jogador (sul)
    O portal fica no norte (Z negativo) e o drone começa no sul (Z positivo).
"""

# ----------------------------------------------------------------------------
# JANELA
# ----------------------------------------------------------------------------
LARGURA, ALTURA = 1280, 720
TITULO = "PROTOCOLO VERMILHÃO — OPERAÇÃO ÚLTIMA ENERGIA"
FPS_ALVO = 60
DT_MAXIMO = 0.05          # evita "saltos" se o jogo travar por um instante (segundos)

# ----------------------------------------------------------------------------
# PALETA (a do enunciado, convertida de #RRGGBB para floats 0..1 que a OpenGL usa)
# ----------------------------------------------------------------------------
def hex_para_rgb(h):
    """'#E63946' -> (0.90, 0.22, 0.27)"""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

VERMELHO        = hex_para_rgb("#E63946")   # destaque: núcleos, alertas, portal
VERMELHO_ESCURO = hex_para_rgb("#8B1E2D")   # detalhes e sombras
PRETO_AZULADO   = hex_para_rgb("#10141D")   # fundo e áreas escuras
CINZA_METAL     = hex_para_rgb("#596273")   # estruturas e obstáculos
CINZA_CLARO     = hex_para_rgb("#D8DEE9")   # textos e detalhes
BRANCO          = (1.0, 1.0, 1.0)           # informações importantes

# ----------------------------------------------------------------------------
# ESTAÇÃO (a arena é um quadrado de lado 2*METADE_ARENA)
# ----------------------------------------------------------------------------
METADE_ARENA = 20.0       # a estação vai de -20 a +20 em X e em Z
ALTURA_PAREDE = 6.0
ESPESSURA_PAREDE = 1.0
CELULA_PISO = 1.0         # tamanho de cada quadradinho da malha do piso (importante p/ a luz por vértice)
METROS_POR_TEXTURA = 4.0  # o piso repete a textura a cada 4 m  -> 10 x 10 repetições

# ----------------------------------------------------------------------------
# DRONE
# ----------------------------------------------------------------------------
POSICAO_INICIAL_DRONE = (0.0, 12.5)   # (x, z)
ALTURA_VOO = 1.9                       # y médio do drone (altura ~constante, como permite o enunciado)
RAIO_DRONE = 0.9                       # raio do "círculo" usado nas colisões
VELOCIDADE_DRONE = 7.0                 # metros por segundo
SUAVIDADE_ACELERACAO = 8.0             # quanto maior, mais "seco" é o início/fim do movimento
VELOCIDADE_HELICE_PARADO = 900.0       # graus por segundo
VELOCIDADE_HELICE_MOVENDO = 1700.0     # graus por segundo

# ----------------------------------------------------------------------------
# CÂMERA (terceira pessoa, elevada)
# ----------------------------------------------------------------------------
CAMERA_DISTANCIA = 10.5
CAMERA_ELEVACAO_INICIAL = 40.0         # graus acima do horizonte
CAMERA_ELEVACAO_MIN, CAMERA_ELEVACAO_MAX = 18.0, 65.0
CAMERA_VEL_ROTACAO = 80.0              # graus por segundo (setas)
CAMERA_SUAVIDADE = 6.0                 # "atraso" confortável ao seguir o drone
FOV_VERTICAL = 60.0

# ----------------------------------------------------------------------------
# NÚCLEOS DE ENERGIA
# ----------------------------------------------------------------------------
POSICOES_NUCLEOS = [          # (x, z)
    (-13.5, 11.5),
    (14.5, 3.0),
    (-14.5, -9.5),
    (13.0, -13.5),
    (0.0, -8.0),
]
NUCLEO_ALTURA_BASE = 2.1
NUCLEO_AMPLITUDE_FLUTUACAO = 0.28     # metros
NUCLEO_VEL_FLUTUACAO = 2.2            # rad/s
NUCLEO_VEL_GIRO = 95.0                # graus por segundo
NUCLEO_RAIO_COLETA = 1.35
NUCLEO_DURACAO_COLETA = 0.5           # segundos que o núcleo leva encolhendo até sumir

# ----------------------------------------------------------------------------
# PORTAL
# ----------------------------------------------------------------------------
POSICAO_PORTAL = (0.0, -17.4)         # (x, z)
PORTAL_RAIO_ANEL = 2.6
PORTAL_ALTURA_CENTRO = 3.0
PORTAL_DURACAO_ABERTURA = 2.6         # segundos da animação de abertura
PORTAL_RAIO_ENTRADA = 2.3             # distância (no plano XZ) para "entrar" no portal ativo

# ----------------------------------------------------------------------------
# OBSTÁCULOS  (tipo, x, z, meia_largura_x, meia_largura_z, altura)
#   "caixa"     -> caixa de manutenção (textura de caixa)
#   "container" -> caixa comprida
#   "pilar"     -> prisma octogonal (meia_largura_x = raio)
#   "torre"     -> torre de iluminação principal (a lâmpada da luz L fica no topo)
# A colisão usa a caixa delimitadora (AABB) no plano XZ.
# ----------------------------------------------------------------------------
OBSTACULOS = [
    ("caixa",     -8.0,  10.0, 1.6, 1.6, 3.2),
    ("caixa",     -5.4,  11.4, 1.0, 1.0, 2.0),
    ("container",  9.0,   9.0, 2.6, 1.3, 3.0),
    ("pilar",     -6.0,   3.5, 0.9, 0.9, 6.5),
    ("pilar",      6.0,   3.5, 0.9, 0.9, 6.5),
    ("torre",      0.0,   0.0, 1.2, 1.2, 8.4),
    ("container", 13.5,  -4.0, 1.3, 3.0, 3.0),
    ("pilar",    -11.0,  -5.0, 0.7, 0.7, 6.0),     # pórtico de manutenção (2 pilares + viga)
    ("pilar",    -11.0, -13.0, 0.7, 0.7, 6.0),
    ("caixa",     -3.0,  -9.0, 1.1, 2.4, 3.0),     # "U" de caixas que protege o 5º núcleo
    ("caixa",      3.0,  -9.0, 1.1, 2.4, 3.0),
    ("caixa",      0.0, -11.8, 2.0, 0.9, 3.0),
    ("pilar",     10.0,  -9.0, 0.9, 0.9, 6.5),
    ("caixa",      5.5, -15.0, 1.4, 1.4, 2.4),
    ("caixa",    -16.0,   0.0, 1.2, 2.0, 2.6),
    ("caixa",     16.5,  14.0, 1.5, 1.5, 2.8),
    ("caixa",    -17.2,  16.8, 1.4, 1.4, 2.6),
    ("pilar",     -4.5, -17.6, 0.9, 0.9, 5.5),     # pilares que enquadram o portal
    ("pilar",      4.5, -17.6, 0.9, 0.9, 5.5),
]

# ----------------------------------------------------------------------------
# ILUMINAÇÃO
# ----------------------------------------------------------------------------
# >>> Para mudar a posição da luz principal na apresentação, altere esta linha <<<
POSICAO_LUZ_PRINCIPAL = (0.0, 8.8, 0.0)               # (x, y, z) — no topo da torre central
POSICOES_LUZ_EMERGENCIA = [(-18.0, 4.6, 8.0), (18.0, 4.6, -8.0)]   # luminárias vermelhas nas paredes
POSICAO_LUZ_PORTAL = (0.0, 3.2, -15.6)
# painéis que acendem com a coleta: (posição da luz, centro do grupo de painéis, parede)
ZONAS_PAINEIS = [
    {"luz": (-17.6, 3.4, -3.0), "parede": "oeste", "centro": -3.0},
    {"luz": (17.6, 3.4, 5.0),   "parede": "leste", "centro": 5.0},
    {"luz": (6.0, 3.4, 17.6),   "parede": "sul",   "centro": 6.0},
    {"luz": (-10.0, 3.4, -17.6), "parede": "norte", "centro": -10.0},
]
# nível de restauração desejado para cada contagem de núcleos coletados (0..5)
NIVEL_POR_COLETA = [0.0, 0.12, 0.25, 0.50, 0.75, 1.0]
VELOCIDADE_TRANSICAO_LUZ = 2.2        # quanto maior, mais rápida a transição (usa dt)
