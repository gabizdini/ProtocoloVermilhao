# -*- coding: utf-8 -*-
"""
Joga a missão com o piloto automático e salva capturas REAIS da janela OpenGL (glReadPixels).
Executar (precisa de pygame + PyOpenGL e de um display):   python testes/capturar_telas.py [pasta_saida]
"""
import os, sys
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cv2
import pygame
from OpenGL.GL import *
import config as cfg
import main as jogo
import texturas
from estado import EstadoJogo, Entrada
from iluminacao import SistemaIluminacao
from objetos import Cenario
from hud import Hud
import autopiloto as ap

SAIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "capturas")
os.makedirs(SAIDA, exist_ok=True)


def salvar(nome):
    dados = glReadPixels(0, 0, cfg.LARGURA, cfg.ALTURA, GL_RGBA, GL_UNSIGNED_BYTE)
    img = np.frombuffer(dados, np.uint8).reshape(cfg.ALTURA, cfg.LARGURA, 4)[::-1]
    cv2.imwrite(os.path.join(SAIDA, nome), cv2.cvtColor(img, cv2.COLOR_RGBA2BGR))
    print("capturado:", nome)


def quadro(estado, sis, cenario, hud):
    jogo.desenhar_quadro(estado, sis, cenario, hud)


def esperar(estado, sis, seg, dt=1 / 60, entrada=None):
    for _ in range(round(seg / dt)):
        estado.atualizar(dt, entrada or Entrada())
        sis.atualizar(dt, estado.coletados, estado.portal_abertura)


def main():
    jogo.iniciar_janela()
    cenario = Cenario(texturas.carregar_todas())
    hud = Hud()
    estado = EstadoJogo(); estado.fase = "menu"
    sis = SistemaIluminacao()
    esperar(estado, sis, 2.0)
    quadro(estado, sis, cenario, hud); salvar("01_menu.png")

    jogo.iniciar_missao(estado, sis)
    esperar(estado, sis, 2.5)
    quadro(estado, sis, cenario, hud); salvar("02_jogo_0de5_luz_ligada.png")
    sis.alternar_luz_principal(); esperar(estado, sis, 0.5)
    quadro(estado, sis, cenario, hud); salvar("03_jogo_0de5_luz_desligada.png")
    sis.alternar_luz_principal(); esperar(estado, sis, 0.5)

    # missão completa pelo piloto automático, capturando 2,5 s depois de cada coleta
    pendentes = []
    def cb(est, s, t):
        if est.evento_coleta:
            pendentes.append((t + 2.8, est.coletados))
        for item in list(pendentes):
            if t >= item[0]:
                pendentes.remove(item)
                quadro(est, s, cenario, hud); salvar(f"04_coleta_{item[1]}de5.png")
                if item[1] == 5:
                    s.alternar_luz_principal(); s.atualizar(0.5, est.coletados, est.portal_abertura)
                    quadro(est, s, cenario, hud); salvar("05_5de5_luz_desligada.png")
                    s.alternar_luz_principal(); s.atualizar(0.5, est.coletados, est.portal_abertura)
    ap.voar(estado, sis, ao_quadro=cb)
    esperar(estado, sis, 1.5)
    quadro(estado, sis, cenario, hud); salvar("06_vitoria.png")

    # --- oclusão: o drone passa ATRÁS da caixa e a caixa o esconde (teste de profundidade)
    jogo.iniciar_missao(estado, sis)
    estado.coletados = 3
    estado.drone.x, estado.drone.z = 9.0, 5.6        # logo atrás do container (9, 9), visto da câmera ao sul
    estado.cam_foco = [9.0, cfg.ALTURA_VOO, 5.6]
    estado.cam_elev = 24.0
    esperar(estado, sis, 4.0)
    quadro(estado, sis, cenario, hud); salvar("07_oclusao_drone_atras_da_caixa.png")

    # --- 5/5 no centro da estação: luz principal ligada x desligada (onde ela é a fonte dominante)
    jogo.iniciar_missao(estado, sis)
    estado.coletados = 5; estado.portal_ativo = True; estado.portal_abertura = 1.0
    for n in estado.nucleos:
        n.estado = "coletado"                       # estado coerente com 5/5
    estado.drone.x, estado.drone.z = 4.0, 7.0
    estado.cam_foco = [4.0, cfg.ALTURA_VOO, 7.0]
    esperar(estado, sis, 4.0)
    quadro(estado, sis, cenario, hud); salvar("09_5de5_centro_luz_ligada.png")
    sis.alternar_luz_principal(); esperar(estado, sis, 0.6)
    quadro(estado, sis, cenario, hud); salvar("09_5de5_centro_luz_desligada.png")

    # --- close-up do drone: brilho especular muda com a orientação
    cfg.CAMERA_DISTANCIA = 4.2
    jogo.iniciar_missao(estado, sis)
    estado.drone.x, estado.drone.z = 4.0, 7.0
    estado.cam_foco = [4.0, cfg.ALTURA_VOO, 7.0]
    estado.cam_elev = cfg.CAMERA_ELEVACAO_INICIAL
    for yaw in (0.0, 50.0):
        estado.cam_yaw = yaw
        esperar(estado, sis, 1.5)
        quadro(estado, sis, cenario, hud); salvar(f"08_drone_closeup_yaw{int(yaw)}.png")


if __name__ == "__main__":
    main()
