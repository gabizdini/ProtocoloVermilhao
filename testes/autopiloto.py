# -*- coding: utf-8 -*-
"""
Piloto automático usado nos testes: gera teclas W/A/S/D sintéticas (com a câmera em yaw 0) para seguir
uma rota de pontos, chamando EstadoJogo.atualizar() exatamente como o loop principal faz.
Com yaw 0:  W = -Z (norte)   S = +Z (sul)   A = -X (oeste)   D = +X (leste).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from estado import Entrada

# rota que passa por todos os núcleos contornando os obstáculos (ordem: N1, N5, N4, N2, N3, portal)
ROTA = [
    (0.0, 14.5), (-13.5, 14.5), (-13.5, 11.5),                       # núcleo 1
    (-13.5, 6.0), (3.0, 6.0), (3.0, -5.5), (0.0, -5.5), (0.0, -8.0),   # núcleo 5 (dentro do "U" de caixas)
    (0.0, -5.5), (7.6, -5.5), (7.6, -11.5), (8.5, -11.5), (8.5, -13.5), (13.0, -13.5),   # núcleo 4
    (17.0, -13.5), (17.0, 3.0), (14.5, 3.0),                           # núcleo 2
    (14.5, 6.0), (-13.0, 6.0), (-13.0, -9.5), (-14.5, -9.5),           # núcleo 3
    (-14.5, -15.0), (0.0, -15.0), (0.0, -17.0),                        # portal
]


def entrada_para(drone, alvo, tol=0.15):
    """Move no eixo de maior erro e corrige o desvio lateral (por causa da inércia do drone)."""
    dx, dz = alvo[0] - drone.x, alvo[1] - drone.z
    e = Entrada()
    if abs(dx) >= abs(dz):
        e.direita, e.esquerda = dx > tol, dx < -tol
        e.tras, e.frente = dz > 0.12, dz < -0.12
    else:
        e.tras, e.frente = dz > tol, dz < -tol
        e.direita, e.esquerda = dx > 0.12, dx < -0.12
    return e


def voar(estado, sis, dt=1 / 60, max_seg=200, ao_quadro=None, rota=ROTA):
    """Segue a rota até vencer ou estourar o tempo. Retorna o tempo simulado."""
    i, t = 0, 0.0
    while estado.fase == "jogando" and t < max_seg and i < len(rota):
        d = estado.drone
        alvo = rota[i]
        if abs(d.x - alvo[0]) < 0.3 and abs(d.z - alvo[1]) < 0.3:
            i += 1
            continue
        estado.atualizar(dt, entrada_para(d, alvo))
        sis.atualizar(dt, estado.coletados, estado.portal_abertura)
        t += dt
        if ao_quadro:
            ao_quadro(estado, sis, t)
    return t
