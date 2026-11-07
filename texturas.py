# -*- coding: utf-8 -*-
"""
texturas.py — carrega as texturas para a GPU.

Caminho relativo ao PRÓPRIO arquivo (os.path.dirname(__file__)), então funciona em qualquer
computador e pasta. Se um PNG estiver faltando, ele é gerado por gerar_texturas.py na hora.
"""
import os
import pygame
from OpenGL.GL import *

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "texturas")


def _enviar_para_gpu(dados_rgba, largura, altura):
    """Cria uma textura OpenGL a partir de bytes RGBA e devolve seu identificador."""
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    # GL_REPEAT: coordenadas de textura > 1 repetem a imagem (usado no piso e nas paredes)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    # Mipmaps + filtro linear: evita "serrilhado/cintilação" no piso distante
    glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, largura, altura, 0, GL_RGBA, GL_UNSIGNED_BYTE, dados_rgba)
    return tex


def carregar_textura(nome):
    caminho = os.path.join(PASTA, nome)
    if not os.path.exists(caminho):                         # plano B: gera por código
        import gerar_texturas
        gerar_texturas.gerar_todas(PASTA)
    superficie = pygame.image.load(caminho)
    largura, altura = superficie.get_size()
    # flip=True: a OpenGL considera a 1ª linha como a de BAIXO da imagem
    dados = pygame.image.tostring(superficie, "RGBA", True)
    return _enviar_para_gpu(dados, largura, altura)


def carregar_todas():
    return {
        "piso": carregar_textura("piso_metalico.png"),
        "parede": carregar_textura("parede_painel.png"),
        "caixa": carregar_textura("caixa_manutencao.png"),
        "painel": carregar_textura("painel_energia.png"),
    }


def usar(tex_id):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)


def sem_textura():
    glDisable(GL_TEXTURE_2D)
