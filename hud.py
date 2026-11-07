# -*- coding: utf-8 -*-
"""
hud.py — interface 2D (menu, HUD durante o jogo, tela de vitória).

Como o texto aparece na OpenGL? O pygame desenha o texto numa imagem (Surface); a imagem vira uma
TEXTURA e é aplicada em um retângulo (GL_QUADS) numa projeção ORTOGONAL 2D (glOrtho), sem iluminação
e sem teste de profundidade. As texturas de texto ficam em cache para não recriar a cada quadro.
"""
import math
import pygame
from OpenGL.GL import *
import config as cfg


class Hud:
    def __init__(self):
        pygame.font.init()
        nomes = "bahnschrift,segoeui,arial,dejavusans,verdana"
        self.fontes = {}
        for tam in (16, 20, 24, 30, 40, 64, 84):
            try:
                self.fontes[tam] = pygame.font.SysFont(nomes, tam, bold=True)
            except Exception:
                self.fontes[tam] = pygame.font.Font(None, tam + 6)     # fonte padrão do pygame
        self.cache = {}

    # ------------------------------------------------------------------ modo 2D
    def _entrar_2d(self):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, cfg.LARGURA, cfg.ALTURA, 0, -1, 1)          # origem no canto superior esquerdo, unidades = pixels
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def _sair_2d(self):
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    # ------------------------------------------------------------------ elementos básicos
    def _textura_texto(self, texto, tam):
        chave = (texto, tam)
        if chave not in self.cache:
            sup = self.fontes[tam].render(texto, True, (255, 255, 255))
            larg, alt = sup.get_size()
            dados = pygame.image.tostring(sup, "RGBA", True)
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, larg, alt, 0, GL_RGBA, GL_UNSIGNED_BYTE, dados)
            self.cache[chave] = (tex, larg, alt)
        return self.cache[chave]

    def texto(self, texto, x, y, tam=20, cor=cfg.CINZA_CLARO, alfa=1.0, alinhar="esq"):
        tex, larg, alt = self._textura_texto(texto, tam)
        if alinhar == "centro":
            x -= larg / 2
        elif alinhar == "dir":
            x -= larg
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex)
        glColor4f(cor[0], cor[1], cor[2], alfa)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x, y)
        glTexCoord2f(1, 1); glVertex2f(x + larg, y)
        glTexCoord2f(1, 0); glVertex2f(x + larg, y + alt)
        glTexCoord2f(0, 0); glVertex2f(x, y + alt)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        return larg, alt

    def retangulo(self, x, y, w, h, cor, alfa=1.0):
        glColor4f(cor[0], cor[1], cor[2], alfa)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def moldura(self, x, y, w, h, cor, alfa=1.0, espessura=2.0):
        glLineWidth(espessura)
        glColor4f(cor[0], cor[1], cor[2], alfa)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def painel(self, x, y, w, h):
        """Painel escuro translúcido com filete vermelho à esquerda (identidade visual)."""
        self.retangulo(x, y, w, h, cfg.PRETO_AZULADO, 0.78)
        self.retangulo(x, y, 4, h, cfg.VERMELHO, 1.0)
        self.moldura(x, y, w, h, cfg.CINZA_METAL, 0.8, 1.5)

    # ------------------------------------------------------------------ telas
    def desenhar_hud(self, estado, sis):
        self._entrar_2d()
        total = len(estado.nucleos)
        # --- painel esquerdo: missão, energia, portal, estação
        self.painel(20, 20, 380, 176)
        self.texto("PROTOCOLO VERMILHÃO", 38, 28, 20, cfg.VERMELHO)
        self.texto("MISSÃO: RESTAURAR A ENERGIA", 38, 52, 16, cfg.CINZA_CLARO)
        self.texto("ENERGIA", 38, 80, 24, cfg.CINZA_CLARO)
        self.texto(f"{estado.coletados}/{total}", 150, 74, 40, cfg.BRANCO)
        for i in range(total):                                   # 5 células indicadoras
            x = 236 + i * 32
            if i < estado.coletados:
                self.retangulo(x, 84, 24, 24, cfg.VERMELHO)
            else:
                self.moldura(x, 84, 24, 24, cfg.CINZA_METAL, 1.0, 2.0)
        ativo = estado.portal_ativo
        pisca = 0.65 + 0.35 * math.sin(estado.tempo * 6.0) if ativo else 1.0
        self.retangulo(38, 128, 14, 14, cfg.VERMELHO if ativo else cfg.CINZA_METAL, pisca)
        self.texto("PORTAL: " + ("ATIVO" if ativo else "INATIVO"), 62, 123, 20, cfg.BRANCO if ativo else cfg.CINZA_CLARO)
        self.texto("ESTAÇÃO", 38, 160, 16, cfg.CINZA_CLARO)
        self.retangulo(112, 163, 270, 12, cfg.CINZA_METAL, 0.45)
        self.retangulo(112, 163, 270 * sis.nivel, 12, cfg.VERMELHO)
        self.moldura(112, 163, 270, 12, cfg.CINZA_CLARO, 0.6, 1.0)

        # --- painel direito: luz principal
        self.painel(cfg.LARGURA - 340, 20, 320, 60)
        lig = sis.luz_principal_ligada
        self.texto("LUZ PRINCIPAL [L]", cfg.LARGURA - 322, 28, 16, cfg.CINZA_CLARO)
        self.retangulo(cfg.LARGURA - 322, 52, 14, 14, cfg.BRANCO if lig else cfg.CINZA_METAL)
        self.texto("LIGADA" if lig else "DESLIGADA", cfg.LARGURA - 298, 46, 24, cfg.BRANCO if lig else cfg.VERMELHO)

        # --- aviso temporário (some com o tempo, usando dt)
        if estado.aviso_tempo > 0:
            alfa = min(1.0, estado.aviso_tempo / 0.5)
            self.retangulo(cfg.LARGURA / 2 - 300, 110, 600, 46, cfg.PRETO_AZULADO, 0.8 * alfa)
            self.retangulo(cfg.LARGURA / 2 - 300, 110, 600, 3, cfg.VERMELHO, alfa)
            self.texto(estado.aviso, cfg.LARGURA / 2, 120, 24, cfg.BRANCO, alfa, "centro")

        # --- instruções
        self.retangulo(0, cfg.ALTURA - 38, cfg.LARGURA, 38, cfg.PRETO_AZULADO, 0.7)
        dica = "W A S D  mover     SETAS  câmera     L  luz principal     R  reiniciar     ESC  sair"
        if estado.portal_ativo:
            dica = "PORTAL ATIVO — vá até o portal vermelho!     " + "R  reiniciar     ESC  sair"
        self.texto(dica, cfg.LARGURA / 2, cfg.ALTURA - 31, 20, cfg.CINZA_CLARO, 1.0, "centro")
        self._sair_2d()

    def desenhar_menu(self, estado):
        self._entrar_2d()
        self.retangulo(0, 0, cfg.LARGURA, cfg.ALTURA, cfg.PRETO_AZULADO, 0.62)
        cx = cfg.LARGURA / 2
        self.retangulo(cx - 420, 70, 840, 4, cfg.VERMELHO)
        self.texto("PROTOCOLO VERMILHÃO", cx, 92, 84, cfg.BRANCO, 1.0, "centro")
        self.texto("OPERAÇÃO ÚLTIMA ENERGIA", cx, 186, 40, cfg.VERMELHO, 1.0, "centro")
        self.retangulo(cx - 420, 246, 840, 2, cfg.CINZA_METAL)
        linhas = ["A estação espacial perdeu sua fonte principal de energia.",
                  "Pilote o drone de manutenção, recupere os 5 núcleos vermelhos,",
                  "desvie dos obstáculos e reative o portal de saída."]
        for i, l in enumerate(linhas):
            self.texto(l, cx, 266 + i * 30, 24, cfg.CINZA_CLARO, 1.0, "centro")
        self.painel(cx - 330, 380, 660, 150)
        ctrl = [("W A S D", "mover o drone"), ("SETAS", "girar / inclinar a câmera"),
                ("L", "ligar / desligar a luz principal"), ("R", "reiniciar a missão"), ("ESC", "sair")]
        for i, (t, d) in enumerate(ctrl):
            self.texto(t, cx - 300, 392 + i * 27, 20, cfg.VERMELHO)
            self.texto(d, cx - 160, 392 + i * 27, 20, cfg.CINZA_CLARO)
        pisca = 0.55 + 0.45 * math.sin(estado.tempo * 4.0)
        self.texto("PRESSIONE ENTER PARA INICIAR", cx, 580, 30, cfg.BRANCO, pisca, "centro")
        self._sair_2d()

    def desenhar_vitoria(self, estado):
        self._entrar_2d()
        a = min(1.0, estado.tempo_vitoria / 1.0)
        self.retangulo(0, 0, cfg.LARGURA, cfg.ALTURA, cfg.PRETO_AZULADO, 0.6 * a)
        cx, cy = cfg.LARGURA / 2, cfg.ALTURA / 2
        self.retangulo(cx - 440, cy - 150, 880, 300, cfg.PRETO_AZULADO, 0.88 * a)
        self.retangulo(cx - 440, cy - 150, 880, 5, cfg.VERMELHO, a)
        self.moldura(cx - 440, cy - 150, 880, 300, cfg.CINZA_METAL, a, 2.0)
        self.texto("MISSÃO CONCLUÍDA", cx, cy - 120, 84, cfg.VERMELHO, a, "centro")
        self.texto("A energia principal foi restaurada e o drone escapou pelo portal.", cx, cy - 10, 24, cfg.BRANCO, a, "centro")
        self.texto("A estação voltou à vida. Bom trabalho, piloto.", cx, cy + 26, 24, cfg.CINZA_CLARO, a, "centro")
        pisca = 0.6 + 0.4 * math.sin(estado.tempo * 4.0)
        self.texto("R  jogar novamente        ESC  sair", cx, cy + 90, 30, cfg.BRANCO, pisca * a, "centro")
        self._sair_2d()
