# -*- coding: utf-8 -*-
"""
cena.py — configuração do OpenGL, CÂMERA, PROJEÇÃO, ILUMINAÇÃO e montagem do quadro 3D.

PIPELINE DE COORDENADAS (como um vértice vira pixel):
    coord. LOCAL do objeto   (ex.: um vértice da caixa, centrado na origem do próprio objeto)
        --glTranslatef/glRotatef/glScalef-->  coord. do MUNDO   (matriz de modelo)
        --gluLookAt-->                        coord. da CÂMERA  (matriz de vista)
        --gluPerspective-->                   coord. de RECORTE (projeção em perspectiva)
        --divisão por w + viewport-->         PIXEL na janela
O teste de profundidade (GL_DEPTH_TEST) guarda o ponto mais próximo de cada pixel: é ele que faz a
caixa esconder o drone quando o drone passa atrás dela.
"""
import math
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt
import config as cfg


def configurar_opengl():
    """Liga os recursos do OpenGL usados no jogo (feito uma vez, na inicialização)."""
    glClearColor(*cfg.PRETO_AZULADO, 1.0)
    glViewport(0, 0, cfg.LARGURA, cfg.ALTURA)
    glEnable(GL_DEPTH_TEST)             # oclusão correta entre objetos
    glShadeModel(GL_SMOOTH)             # cores/luz interpoladas entre vértices

    glEnable(GL_LIGHTING)               # liga o cálculo de iluminação da OpenGL
    glEnable(GL_NORMALIZE)              # renormaliza normais (necessário porque usamos glScalef)
    glEnable(GL_COLOR_MATERIAL)         # glColor passa a definir a cor ambiente+difusa do material
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)        # especular correto: usa a posição REAL da câmera
    glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)  # brilho aparece também sobre texturas
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)  # textura x iluminação
    try:
        glEnable(GL_MULTISAMPLE)
    except Exception:
        pass


# ----------------------------------------------------------------------------- câmera
def posicao_camera(estado):
    """Câmera em 3ª pessoa: gira ao redor do foco (drone) com ângulos yaw/elevação e distância fixa."""
    e, a = math.radians(estado.cam_elev), math.radians(estado.cam_yaw)
    fx, fy, fz = estado.cam_foco
    d = cfg.CAMERA_DISTANCIA
    cx = fx + d * math.cos(e) * math.sin(a)
    cy = fy + d * math.sin(e)
    cz = fz + d * math.cos(e) * math.cos(a)
    lim = cfg.METADE_ARENA - 1.2                    # a câmera fica dentro da estação (acima da altura das paredes)
    cx, cz = max(-lim, min(lim, cx)), max(-lim, min(lim, cz))
    return (cx, cy, cz), (fx, fy + 0.4, fz)


def posicao_camera_menu(tempo):
    """Tela inicial: câmera orbitando lentamente a estação."""
    a = math.radians(tempo * 9.0 + 20.0)
    return (17.0 * math.sin(a), 11.5, 17.0 * math.cos(a)), (0.0, 2.0, 0.0)


def aplicar_camera(olho, alvo):
    # PROJEÇÃO em perspectiva: objetos distantes parecem menores
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(cfg.FOV_VERTICAL, cfg.LARGURA / cfg.ALTURA, 0.5, 400.0)
    # VISTA: posiciona/orienta a câmera olhando para o alvo
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(olho[0], olho[1], olho[2], alvo[0], alvo[1], alvo[2], 0, 1, 0)


# ----------------------------------------------------------------------------- iluminação
def aplicar_iluminacao(sis):
    """
    Envia à OpenGL os parâmetros calculados por SistemaIluminacao.
    IMPORTANTE: deve ser chamada DEPOIS de gluLookAt, pois a posição da luz também passa pela
    matriz de vista — assim a luz fica fixa no MUNDO e não "grudada" na câmera.
    """
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (*sis.ambiente_global, 1.0))      # luz ambiente geral
    for f in sis.fontes():
        luz = GL_LIGHT0 + f.indice
        if not f.ligada:
            glDisable(luz)
            continue
        glEnable(luz)
        glLightfv(luz, GL_POSITION, (*f.posicao, 1.0))          # w=1: luz POSICIONAL (pontual)
        glLightfv(luz, GL_AMBIENT, (*f.ambiente, 1.0))
        glLightfv(luz, GL_DIFFUSE, (*f.difusa, 1.0))            # resposta difusa (lei de Lambert: normal . luz)
        glLightfv(luz, GL_SPECULAR, (*f.especular, 1.0))        # brilho especular (depende do observador)
        glLightf(luz, GL_CONSTANT_ATTENUATION, f.atenuacao[0])  # atenuação com a distância
        glLightf(luz, GL_LINEAR_ATTENUATION, f.atenuacao[1])
        glLightf(luz, GL_QUADRATIC_ATTENUATION, f.atenuacao[2])


# ----------------------------------------------------------------------------- quadro 3D completo
def renderizar_cena(estado, sis, cenario, modo_menu=False):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    olho, alvo = posicao_camera_menu(estado.tempo) if modo_menu else posicao_camera(estado)
    aplicar_camera(olho, alvo)
    cenario.desenhar_estrelas(olho)
    aplicar_iluminacao(sis)

    cenario.desenhar_estatico()                   # piso, paredes, caixas, pilares, cabos (display list)
    cenario.desenhar_paineis(sis)
    cenario.desenhar_indicadores(sis)
    cenario.desenhar_lampada_e_luminarias(sis, estado)
    cenario.desenhar_pedestais(estado)
    cenario.desenhar_nucleos(estado)
    cenario.desenhar_portal(estado)
    cenario.desenhar_drone(estado)
    cenario.desenhar_translucidos(estado, sis)    # por último: precisam do fundo já desenhado
