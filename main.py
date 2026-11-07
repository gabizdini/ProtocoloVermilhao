# -*- coding: utf-8 -*-
"""
PROTOCOLO VERMILHÃO — OPERAÇÃO ÚLTIMA ENERGIA
Trabalho Prático 1 — Computação Gráfica (IFSULDEMINAS — Campus Machado)

Arquivo principal: inicializa Pygame + OpenGL e executa o LOOP PRINCIPAL.
Execução:   python main.py
"""
import sys
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN
from OpenGL.GL import *

import config as cfg
import cena
import texturas
from estado import EstadoJogo, Entrada
from iluminacao import SistemaIluminacao
from objetos import Cenario
from hud import Hud


def iniciar_janela():
    """Pygame cria a janela e o contexto OpenGL; a OpenGL só desenha."""
    pygame.init()
    try:   # tenta antisserrilhado (MSAA); se a placa não suportar, abre sem ele
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.set_mode((cfg.LARGURA, cfg.ALTURA), DOUBLEBUF | OPENGL)
    except pygame.error:
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
        pygame.display.set_mode((cfg.LARGURA, cfg.ALTURA), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(cfg.TITULO)
    cena.configurar_opengl()


def ler_teclado():
    """Teclas SEGURADAS (movimento contínuo) -> get_pressed(), como no exercício de teclado das aulas."""
    t = pygame.key.get_pressed()
    return Entrada(
        frente=t[pygame.K_w], tras=t[pygame.K_s], esquerda=t[pygame.K_a], direita=t[pygame.K_d],
        cam_esq=t[pygame.K_LEFT], cam_dir=t[pygame.K_RIGHT], cam_cima=t[pygame.K_UP], cam_baixo=t[pygame.K_DOWN],
    )


def iniciar_missao(estado, sis):
    """Reinício completo SEM fechar o programa: estado do jogo + iluminação voltam ao zero."""
    estado.reiniciar()
    sis.reiniciar()


def desenhar_quadro(estado, sis, cenario, hud):
    """Um quadro completo: cena 3D + interface 2D por cima."""
    cena.renderizar_cena(estado, sis, cenario, modo_menu=(estado.fase == "menu"))
    if estado.fase == "menu":
        hud.desenhar_menu(estado)
    else:
        hud.desenhar_hud(estado, sis)
        if estado.fase == "vitoria":
            hud.desenhar_vitoria(estado)


def tratar_eventos(estado, sis):
    """Eventos de UM toque (KEYDOWN): sair, iniciar, reiniciar, ligar/desligar a luz. Retorna False para encerrar."""
    for ev in pygame.event.get():
        if ev.type == QUIT:
            return False
        if ev.type == KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                return False
            if ev.key == pygame.K_l:
                sis.alternar_luz_principal()           # independe da progressão da missão
            if ev.key == pygame.K_r and estado.fase != "menu":
                iniciar_missao(estado, sis)
            if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER) and estado.fase == "menu":
                iniciar_missao(estado, sis)
    return True


def main():
    iniciar_janela()
    tex = texturas.carregar_todas()
    cenario = Cenario(tex)
    hud = Hud()
    estado = EstadoJogo()
    estado.fase = "menu"
    sis = SistemaIluminacao()
    relogio = pygame.time.Clock()
    acumulado = 0.0
    rodando = True
    while rodando:
        # dt = tempo (em segundos) que passou desde o quadro anterior
        dt = min(relogio.tick(cfg.FPS_ALVO) / 1000.0, cfg.DT_MAXIMO)
        rodando = tratar_eventos(estado, sis)
        estado.atualizar(dt, ler_teclado())
        sis.atualizar(dt, estado.coletados, estado.portal_abertura)
        desenhar_quadro(estado, sis, cenario, hud)
        pygame.display.flip()                            # troca os buffers (buffer duplo)
        acumulado += dt
        if acumulado > 0.5 and estado.fase != "menu":    # contador também no título da janela
            acumulado = 0.0
            pygame.display.set_caption(f"PROTOCOLO VERMILHÃO — Energia {estado.coletados}/{len(estado.nucleos)}"
                                       f" — {relogio.get_fps():.0f} FPS")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
