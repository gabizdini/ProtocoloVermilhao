# -*- coding: utf-8 -*-
"""
iluminacao.py — SISTEMA DE ILUMINAÇÃO PROGRESSIVA da estação (lógica, sem OpenGL).

A história é contada pela luz:
    0/5  estação escura, só a iluminação de EMERGÊNCIA vermelha (e a luz principal fraquinha)
    1-2  painéis e indicadores começam a acender (luzes de painel reais)
    3-4  a iluminação geral aumenta gradualmente
    5/5  energia restaurada: luz intensa, todos os painéis ligados, portal iluminado

Esta classe calcula, a cada quadro, os PARÂMETROS de cada fonte de luz (posição, cor, intensidade,
atenuação). Quem realmente envia isso para a OpenGL (glLightfv) é a função aplicar_iluminacao() em cena.py.
Assim a iluminação é real (feita pela OpenGL, com normais e materiais) e não "pintura" de cores.

Fontes de luz (a OpenGL clássica garante 8):
    GL_LIGHT0      luz principal da torre        -> controlada pela tecla L
    GL_LIGHT1,2    luzes de emergência vermelhas  -> sempre ligadas, enfraquecem com a restauração
    GL_LIGHT3      luz do portal
    GL_LIGHT4..7   luzes dos 4 grupos de painéis  -> acendem conforme os núcleos são coletados
"""
import math
from dataclasses import dataclass
import config as cfg


@dataclass
class FonteLuz:
    indice: int                 # 0..7  (GL_LIGHT0 + indice)
    posicao: tuple              # (x, y, z) no mundo
    difusa: tuple               # cor da luz difusa (já multiplicada pela intensidade)
    especular: tuple
    ambiente: tuple
    atenuacao: tuple            # (constante, linear, quadrática)
    ligada: bool = True


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_cor(c1, c2, t):
    return tuple(_lerp(a, b, t) for a, b in zip(c1, c2))


def _esc(cor, k):
    return tuple(c * k for c in cor)


class SistemaIluminacao:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.luz_principal_ligada = True     # tecla L (independe da missão)
        self.fator_principal = 1.0           # 0..1, suaviza o liga/desliga (~0,2 s)
        self.nivel = 0.0                     # 0..1  restauração geral (suave)
        self.paineis = [0.0, 0.0, 0.0, 0.0]  # 0..1 de cada zona de painéis
        self.tempo = 0.0
        self.portal = 0.0                    # 0..1 (copiado de portal_abertura)
        self.coletados = 0

    def alternar_luz_principal(self):
        self.luz_principal_ligada = not self.luz_principal_ligada

    # ------------------------------------------------------------------ atualização por dt
    def atualizar(self, dt, coletados, portal_abertura):
        self.tempo += dt
        self.coletados = coletados
        self.portal = portal_abertura

        # nível geral: aproxima-se do alvo de forma exponencial (suave e independente do FPS)
        alvo = cfg.NIVEL_POR_COLETA[max(0, min(5, coletados))]
        self.nivel += (alvo - self.nivel) * (1.0 - math.exp(-cfg.VELOCIDADE_TRANSICAO_LUZ * dt))

        # cada zona de painéis acende quando coletados >= i+1; fica plena só com 5/5
        for i in range(4):
            if coletados >= 5:
                alvo_p = 1.0
            elif coletados >= i + 1:
                alvo_p = 0.55
            else:
                alvo_p = 0.0
            self.paineis[i] += (alvo_p - self.paineis[i]) * (1.0 - math.exp(-3.0 * dt))

        # liga/desliga da luz principal (L): transição rápida, ~0,2 s
        alvo_l = 1.0 if self.luz_principal_ligada else 0.0
        passo = 6.0 * dt
        if self.fator_principal < alvo_l:
            self.fator_principal = min(alvo_l, self.fator_principal + passo)
        else:
            self.fator_principal = max(alvo_l, self.fator_principal - passo)

    # ------------------------------------------------------------------ valores derivados
    @property
    def intensidade_principal(self):
        """Luz principal: fraca no início (0.62) e forte no fim (1.25) — e zero se L estiver desligada."""
        return _lerp(0.62, 1.25, self.nivel) * self.fator_principal

    @property
    def intensidade_emergencia(self):
        """Vermelha: 100% no início, cai para 30% quando a energia é restaurada; pulsa como alarme."""
        pulso = 0.88 + 0.12 * math.sin(self.tempo * 3.2)
        return _lerp(1.0, 0.30, self.nivel) * pulso

    @property
    def ambiente_global(self):
        """Luz ambiente da cena: vermelho-escura no início, azul-acinzentada no fim."""
        return _lerp_cor((0.17, 0.095, 0.11), (0.17, 0.185, 0.23), self.nivel)

    @property
    def brilho_lampada(self):
        """Quanto a lâmpada da torre 'acende' visualmente (emissão); coerente com a luz real."""
        return self.fator_principal * _lerp(0.55, 1.0, self.nivel)

    @property
    def brilho_indicadores(self):
        """LEDs/indicadores: começam a acender já no 1/5."""
        return min(1.0, self.nivel * 2.2)

    # ------------------------------------------------------------------ lista de fontes
    def fontes(self):
        lista = []
        # 0 — luz principal (L): branca-azulada, com brilho especular
        c = (0.88, 0.93, 1.0)
        k = self.intensidade_principal
        lista.append(FonteLuz(0, cfg.POSICAO_LUZ_PRINCIPAL, _esc(c, k), _esc(c, k), (0.0, 0.0, 0.0),
                              (1.0, 0.010, 0.0007), ligada=k > 0.003))
        # 1 e 2 — emergência vermelha
        e = self.intensidade_emergencia
        verm = (1.0, 0.13, 0.16)
        for i, pos in enumerate(cfg.POSICOES_LUZ_EMERGENCIA):
            lista.append(FonteLuz(1 + i, pos, _esc(verm, 1.9 * e), _esc(verm, 0.8 * e), (0, 0, 0),
                                  (1.0, 0.05, 0.010)))
        # 3 — portal: vermelho fraco enquanto fechado; branco-avermelhado intenso quando aberto
        cor_portal = _lerp_cor((1.0, 0.15, 0.18), (1.0, 0.72, 0.68), self.portal)
        kp = 0.30 * (0.85 + 0.15 * math.sin(self.tempo * 2.0)) + 1.2 * self.portal
        lista.append(FonteLuz(3, cfg.POSICAO_LUZ_PORTAL, _esc(cor_portal, kp), _esc(cor_portal, kp * 0.6),
                              (0, 0, 0), (1.0, 0.07, 0.015)))
        # 4..7 — luzes dos painéis (cinza-claro da paleta)
        cp = (0.85, 0.88, 0.96)
        for i, z in enumerate(cfg.ZONAS_PAINEIS):
            kz = self.paineis[i] * 1.1
            lista.append(FonteLuz(4 + i, z["luz"], _esc(cp, kz), _esc(cp, kz * 0.5), (0, 0, 0),
                                  (1.0, 0.09, 0.020), ligada=kz > 0.003))
        return lista
