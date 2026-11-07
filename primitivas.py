# -*- coding: utf-8 -*-
"""
primitivas.py — formas geométricas construídas "na mão" com glBegin/glEnd.

Onde cada PRIMITIVA da OpenGL aparece neste arquivo:
    GL_QUADS         -> caixa(), superficie_grade()   (quadriláteros: faces das caixas, piso, paredes)
    GL_TRIANGLES     -> octaedro()                     (triângulos: o cristal dos núcleos)
    GL_TRIANGLE_FAN  -> disco(), prisma() (tampas)     (leque de triângulos)
    GL_QUAD_STRIP    -> toro(), prisma() (lados)       (faixa de quadriláteros)
    GL_LINES / GL_LINE_LOOP -> linhas(), circulo()     (linhas: cabos, marcações, anéis)
    GL_POINTS        -> estrelas (em objetos.py)

Todos os objetos são definidos em COORDENADAS LOCAIS (centrados na origem, tamanho próprio).
Quem os posiciona no mundo é glTranslatef/glRotatef/glScalef, feitos por quem chama.

NORMAIS: cada face informa para onde "aponta" (glNormal3f). A iluminação (difusa e especular) usa
a normal para calcular o brilho: quanto mais a normal olha para a luz, mais iluminada a face.
"""
import math
from OpenGL.GL import *


def definir_material(cor, especular=0.0, brilho=0.0, emissao=0.0, alfa=1.0, cor_emissao=None):
    """
    Define a aparência da superfície para a iluminação:
      cor       -> cor ambiente+difusa (via GL_COLOR_MATERIAL, o glColor vira a cor do material)
      especular -> intensidade do brilho "espelhado" (0 = fosco)
      brilho    -> expoente especular (GL_SHININESS, 0..128): maior = reflexo menor e mais concentrado
      emissao   -> o objeto "emite" luz própria (lâmpadas, LEDs). NÃO ilumina outros objetos.
    Todos os 4 componentes são sempre redefinidos, para um objeto não "herdar" o material do anterior.
    """
    glColor4f(cor[0], cor[1], cor[2], alfa)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (especular, especular, especular, 1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, brilho)
    ce = cor_emissao if cor_emissao is not None else cor
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (ce[0] * emissao, ce[1] * emissao, ce[2] * emissao, 1.0))


# ----------------------------------------------------------------------------- caixa
# Para cada face: normal, eixo "u" (horizontal da textura) e eixo "v" (vertical).  u x v = normal.
_FACES = [
    ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    ((0, 1, 0), (1, 0, 0), (0, 0, -1)),
    ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
]


def caixa(lx, ly, lz, uv_por_metro=None, faces_laterais_apenas=False):
    """
    Caixa centrada na origem local, com dimensões lx*ly*lz (6 faces = 6 GL_QUADS, 24 vértices).
    uv_por_metro=None  -> a textura cobre cada face uma vez (0..1).
    uv_por_metro=k     -> a textura repete k vezes por metro: o tamanho do "ladrilho" fica o mesmo em
                          todas as faces, SEM esticar a imagem (evita deformação do mapeamento).
    """
    dims = (lx, ly, lz)
    glBegin(GL_QUADS)
    for n, u, v in _FACES:
        if faces_laterais_apenas and n[1] != 0:
            continue
        hn = sum(abs(n[i]) * dims[i] for i in range(3)) / 2.0
        hu = sum(abs(u[i]) * dims[i] for i in range(3)) / 2.0
        hv = sum(abs(v[i]) * dims[i] for i in range(3)) / 2.0
        ru = (2 * hu * uv_por_metro) if uv_por_metro else 1.0
        rv = (2 * hv * uv_por_metro) if uv_por_metro else 1.0
        glNormal3f(*n)
        for su, sv, tu, tv in ((-1, -1, 0, 0), (1, -1, ru, 0), (1, 1, ru, rv), (-1, 1, 0, rv)):
            glTexCoord2f(tu, tv)
            glVertex3f(*(n[i] * hn + u[i] * su * hu + v[i] * sv * hv for i in range(3)))
    glEnd()


def cubo_unitario():
    """Cubo 1x1x1 — as peças do drone usam glScalef sobre ele (a ESCALA define cada peça)."""
    caixa(1.0, 1.0, 1.0)


# ----------------------------------------------------------------------------- piso / paredes
def superficie_grade(comp_u, comp_v, normal, eixo_u, eixo_v, celula=1.0, uv_por_metro=(0.25, 0.25)):
    """
    Plano retangular centrado na origem, dividido em uma GRADE de quadradinhos (GL_QUADS).
    Por que dividir? A iluminação padrão é calculada nos VÉRTICES e interpolada. Um único quadrado
    gigante só teria 4 pontos de luz; com a grade, as "poças" de luz aparecem de verdade.
    """
    nu, nv = int(round(comp_u / celula)), int(round(comp_v / celula))
    ku, kv = uv_por_metro if isinstance(uv_por_metro, tuple) else (uv_por_metro, uv_por_metro)
    glNormal3f(*normal)
    # ordem dos vértices: anti-horária vista do lado da normal (necessário para o culling das paredes)
    cruz = (eixo_u[1] * eixo_v[2] - eixo_u[2] * eixo_v[1], eixo_u[2] * eixo_v[0] - eixo_u[0] * eixo_v[2],
            eixo_u[0] * eixo_v[1] - eixo_u[1] * eixo_v[0])
    ordem = ((0, 0), (1, 0), (1, 1), (0, 1))
    if sum(c * n for c, n in zip(cruz, normal)) < 0:
        ordem = ((0, 0), (0, 1), (1, 1), (1, 0))
    glBegin(GL_QUADS)
    for i in range(nu):
        for j in range(nv):
            for di, dj in ordem:
                a = (i + di) * celula - comp_u / 2.0
                b = (j + dj) * celula - comp_v / 2.0
                glTexCoord2f((i + di) * celula * ku, (j + dj) * celula * kv)
                glVertex3f(eixo_u[0] * a + eixo_v[0] * b, eixo_u[1] * a + eixo_v[1] * b, eixo_u[2] * a + eixo_v[2] * b)
    glEnd()


# ----------------------------------------------------------------------------- prisma / cilindro
def prisma(raio, altura, lados=8, tampas=True):
    """Prisma de N lados (cilindro "low poly") com base em y=0 e topo em y=altura."""
    glBegin(GL_QUAD_STRIP)
    for i in range(lados + 1):
        a = 2 * math.pi * i / lados
        am = 2 * math.pi * (i - 0.5) / lados          # normal "chata" no meio de cada face (estilo low poly)
        glNormal3f(math.cos(am), 0, math.sin(am))
        glTexCoord2f(i / lados * 2, 0)
        glVertex3f(raio * math.cos(a), 0, raio * math.sin(a))
        glTexCoord2f(i / lados * 2, altura * 0.25)
        glVertex3f(raio * math.cos(a), altura, raio * math.sin(a))
    glEnd()
    if tampas:
        for y, ny in ((altura, 1), (0, -1)):
            glBegin(GL_TRIANGLE_FAN)
            glNormal3f(0, ny, 0)
            glTexCoord2f(0.5, 0.5)
            glVertex3f(0, y, 0)
            for i in range(lados + 1):
                a = 2 * math.pi * i / lados * (1 if ny > 0 else -1)
                glTexCoord2f(0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))
                glVertex3f(raio * math.cos(a), y, raio * math.sin(a))
            glEnd()


# ----------------------------------------------------------------------------- esfera
def esfera(raio, fatias=20, pilhas=12):
    """
    Esfera com normais SUAVES (a normal de cada vértice aponta do centro para fora). É isso que permite
    ao brilho especular deslizar de forma contínua sobre o corpo do drone quando ele gira.
    """
    for i in range(pilhas):
        a0, a1 = math.pi * i / pilhas - math.pi / 2, math.pi * (i + 1) / pilhas - math.pi / 2
        glBegin(GL_QUAD_STRIP)
        for j in range(fatias + 1):
            b = 2 * math.pi * j / fatias
            for a in (a1, a0):
                nx, ny, nz = math.cos(a) * math.cos(b), math.sin(a), math.cos(a) * math.sin(b)
                glNormal3f(nx, ny, nz)
                glVertex3f(raio * nx, raio * ny, raio * nz)
        glEnd()


# ----------------------------------------------------------------------------- cristal
def octaedro():
    """Octaedro de raio 1 = 8 triângulos (GL_TRIANGLES). Alongado com glScalef vira um cristal."""
    topo, base = (0, 1, 0), (0, -1, 0)
    anel = [(1, 0, 0), (0, 0, 1), (-1, 0, 0), (0, 0, -1)]
    glBegin(GL_TRIANGLES)
    for pico in (topo, base):
        for i in range(4):
            p1, p2 = anel[i], anel[(i + 1) % 4]
            if pico is base:
                p1, p2 = p2, p1
            # normal da face = produto vetorial das duas arestas (aponta para fora do cristal)
            e1 = [p1[k] - pico[k] for k in range(3)]
            e2 = [p2[k] - pico[k] for k in range(3)]
            nx = e1[1] * e2[2] - e1[2] * e2[1]
            ny = e1[2] * e2[0] - e1[0] * e2[2]
            nz = e1[0] * e2[1] - e1[1] * e2[0]
            glNormal3f(nx, ny, nz)
            glVertex3f(*pico)
            glVertex3f(*p1)
            glVertex3f(*p2)
    glEnd()


# ----------------------------------------------------------------------------- disco / anel / toro
def disco(raio, seg=32, centro_alfa=1.0, borda_alfa=1.0, cor_centro=None, cor_borda=None):
    """Disco no plano XY (normal +Z) como leque de triângulos; cor/alfa podem variar do centro à borda."""
    glNormal3f(0, 0, 1)
    glBegin(GL_TRIANGLE_FAN)
    if cor_centro:
        glColor4f(*cor_centro, centro_alfa)
    glVertex3f(0, 0, 0)
    if cor_borda:
        glColor4f(*cor_borda, borda_alfa)
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        glVertex3f(raio * math.cos(a), raio * math.sin(a), 0)
    glEnd()


def toro(raio_maior, raio_menor, seg_maior=28, seg_menor=8):
    """Anel 3D (rosca) no plano XY, feito de faixas de quadriláteros. Usado no portal e nas hélices."""
    for i in range(seg_maior):
        glBegin(GL_QUAD_STRIP)
        for j in range(seg_menor + 1):
            for ii in (i, i + 1):
                a = 2 * math.pi * ii / seg_maior
                b = 2 * math.pi * j / seg_menor
                nx, ny, nz = math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)
                glNormal3f(nx, ny, nz)
                r = raio_maior + raio_menor * math.cos(b)
                glVertex3f(r * math.cos(a), r * math.sin(a), raio_menor * math.sin(b))
        glEnd()


def anel_plano(raio_ext, raio_int, seg=24):
    """Anel achatado no plano XZ (normal +Y): proteção das hélices. GL_QUAD_STRIP."""
    glNormal3f(0, 1, 0)
    glBegin(GL_QUAD_STRIP)
    for i in range(seg + 1):
        a = 2 * math.pi * i / seg
        glVertex3f(raio_ext * math.cos(a), 0, raio_ext * math.sin(a))
        glVertex3f(raio_int * math.cos(a), 0, raio_int * math.sin(a))
    glEnd()


# ----------------------------------------------------------------------------- linhas
def linhas(pares, cor, espessura=1.5):
    """Segmentos independentes (GL_LINES). Linhas não usam iluminação: desliga e religa."""
    glDisable(GL_LIGHTING)
    glLineWidth(espessura)
    glColor3f(*cor)
    glBegin(GL_LINES)
    for (a, b) in pares:
        glVertex3f(*a)
        glVertex3f(*b)
    glEnd()
    glEnable(GL_LIGHTING)


def circulo_linhas(raio, cor, seg=40, espessura=1.5):
    """Circunferência no plano XY feita de linhas (GL_LINE_LOOP)."""
    glDisable(GL_LIGHTING)
    glLineWidth(espessura)
    glColor3f(*cor)
    glBegin(GL_LINE_LOOP)
    for i in range(seg):
        a = 2 * math.pi * i / seg
        glVertex3f(raio * math.cos(a), raio * math.sin(a), 0)
    glEnd()
    glEnable(GL_LIGHTING)


def compilar_lista(funcao_de_desenho):
    """
    Grava os comandos de desenho numa DISPLAY LIST (glNewList/glEndList): a GPU guarda e reexecuta
    com 1 chamada (glCallList). Usada só no cenário ESTÁTICO (piso, paredes, caixas) por desempenho.
    A iluminação continua sendo calculada a cada quadro, então a luz muda normalmente.
    """
    lista = glGenLists(1)
    glNewList(lista, GL_COMPILE)
    funcao_de_desenho()
    glEndList()
    return lista
