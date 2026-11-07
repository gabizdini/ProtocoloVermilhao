# -*- coding: utf-8 -*-
"""
Teste de INTEGRAÇÃO (precisa de pygame + PyOpenGL + display): abre a janela de verdade e confere
eventos de teclado, ausência de erros da OpenGL, hélices girando e luz L alterando a imagem.
Executar:   python testes/teste_integracao.py
"""
import os, sys, time, unittest
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, RAIZ)
import numpy as np
import pygame
from OpenGL.GL import *
import config as cfg
import main as jogo
import texturas
from estado import EstadoJogo, Entrada
from iluminacao import SistemaIluminacao
from objetos import Cenario
from hud import Hud


def tecla(k):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k))


def ler():
    d = glReadPixels(0, 0, cfg.LARGURA, cfg.ALTURA, GL_RGBA, GL_UNSIGNED_BYTE)
    return np.frombuffer(d, np.uint8).reshape(cfg.ALTURA, cfg.LARGURA, 4).astype(np.int32)


class TesteJanela(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jogo.iniciar_janela()
        cls.cenario = Cenario(texturas.carregar_todas())
        cls.hud = Hud()

    def setUp(self):
        self.e = EstadoJogo(); self.e.fase = "menu"; self.s = SistemaIluminacao()

    def passo(self, seg=0.5, entrada=None):
        for _ in range(round(seg * 60)):
            self.e.atualizar(1 / 60, entrada or Entrada())
            self.s.atualizar(1 / 60, self.e.coletados, self.e.portal_abertura)

    def quadro(self):
        jogo.desenhar_quadro(self.e, self.s, self.cenario, self.hud)

    def test_sem_erros_opengl_em_todas_as_telas(self):
        self.quadro(); self.assertEqual(glGetError(), 0, "menu")
        jogo.iniciar_missao(self.e, self.s); self.passo(); self.quadro(); self.assertEqual(glGetError(), 0, "jogo")
        self.e.coletados = 5; self.e.portal_ativo = True; self.passo(3); self.quadro(); self.assertEqual(glGetError(), 0, "portal")
        self.e.fase = "vitoria"; self.passo(1); self.quadro(); self.assertEqual(glGetError(), 0, "vitoria")

    def test_teclas_enter_L_R_esc(self):
        tecla(pygame.K_RETURN); self.assertTrue(jogo.tratar_eventos(self.e, self.s)); self.assertEqual(self.e.fase, "jogando")
        tecla(pygame.K_l); jogo.tratar_eventos(self.e, self.s); self.assertFalse(self.s.luz_principal_ligada)
        tecla(pygame.K_l); jogo.tratar_eventos(self.e, self.s); self.assertTrue(self.s.luz_principal_ligada)
        self.e.coletados = 2; self.e.drone.x = 5.0
        tecla(pygame.K_r); jogo.tratar_eventos(self.e, self.s)
        self.assertEqual((self.e.coletados, self.e.drone.x), (0, cfg.POSICAO_INICIAL_DRONE[0]))
        tecla(pygame.K_ESCAPE); self.assertFalse(jogo.tratar_eventos(self.e, self.s))

    def test_luz_L_muda_a_imagem(self):
        jogo.iniciar_missao(self.e, self.s); self.passo(2)
        self.quadro(); a = ler()
        self.s.alternar_luz_principal(); self.passo(0.6); self.quadro(); b = ler()
        regiao = (slice(250, 600), slice(300, 1000))       # área da cena (fora do HUD)
        dif = np.abs(a[regiao][..., :3] - b[regiao][..., :3]).mean()
        print(f"\n   diferença média de pixel (L ligada x desligada, 0/5): {dif:.1f}/255")
        self.assertGreater(dif, 5.0)

    def test_helices_giram_na_imagem(self):
        jogo.iniciar_missao(self.e, self.s); self.passo(1)
        self.quadro(); a = ler(); self.passo(0.02); self.quadro(); b = ler()
        regiao = (slice(250, 450), slice(500, 800))
        self.assertGreater(np.abs(a[regiao] - b[regiao]).sum(), 1000)

    def test_ordem_de_grandeza_do_tempo_de_quadro(self):
        jogo.iniciar_missao(self.e, self.s); self.passo(1)
        t0 = time.perf_counter()
        for _ in range(20):
            self.passo(1 / 60); self.quadro(); pygame.display.flip()
        ms = (time.perf_counter() - t0) / 20 * 1000
        print(f"\n   tempo médio por quadro neste ambiente: {ms:.1f} ms")


if __name__ == "__main__":
    unittest.main(verbosity=2)
