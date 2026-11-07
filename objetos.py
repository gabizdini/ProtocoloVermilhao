# -*- coding: utf-8 -*-
"""
objetos.py — desenho de cada objeto da cena (drone, cenário, núcleos, portal...).

Dois grupos:
  * ESTÁTICO (piso, paredes, caixas, pilares, cabos): nunca muda -> gravado uma vez numa display list.
  * DINÂMICO (drone, núcleos, portal, painéis, lâmpadas): desenhado de novo a cada quadro, com
    posições/ângulos vindos do `estado` (que já foram atualizados usando dt).

TRANSFORMAÇÕES: o padrão em todo o arquivo é
        glPushMatrix()    # salva a matriz atual
        glTranslatef(...) # TRANSLAÇÃO: coloca o objeto no mundo
        glRotatef(...)    # ROTAÇÃO:    orienta o objeto
        glScalef(...)     # ESCALA:     define o tamanho
        ...desenha em coordenadas locais...
        glPopMatrix()     # restaura: o próximo objeto não é afetado
As operações são aplicadas ao vértice na ORDEM INVERSA da escrita (a última escrita é a 1ª aplicada).
"""
import math
import random
from OpenGL.GL import *
import config as cfg
import primitivas as P
import texturas as T
from primitivas import definir_material as material

META = cfg.METADE_ARENA - cfg.ESPESSURA_PAREDE      # face interna das paredes (= 19)
H = cfg.ALTURA_PAREDE


def suave(t):
    """smoothstep: 0..1 com começo e fim suaves (usado nas animações do portal)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# =============================================================================== CENÁRIO ESTÁTICO
class Cenario:
    def __init__(self, tex):
        self.tex = tex
        self.lista = P.compilar_lista(self._desenhar_estatico)
        rng = random.Random(11)                           # semente fixa: mesmo céu sempre
        self.estrelas = []
        for _ in range(420):
            az = rng.uniform(0, 2 * math.pi)
            el = rng.uniform(-0.15, 1.35)
            r = 150.0
            self.estrelas.append((r * math.cos(el) * math.cos(az), r * math.sin(el), r * math.cos(el) * math.sin(az),
                                  rng.uniform(0.45, 1.0)))

    # ---------------------------------------------------------------- partes estáticas
    def _desenhar_estatico(self):
        self._piso()
        self._paredes()
        self._marcacoes_piso()
        self._dutos_e_cabos()
        for o in cfg.OBSTACULOS:
            self._obstaculo(o)
        self._portico()

    def _piso(self):
        # PISO: malha 40x40 de quadradinhos; a textura REPETE a cada METROS_POR_TEXTURA (10x10 vezes)
        T.usar(self.tex["piso"])
        material((0.95, 0.95, 1.0), especular=0.28, brilho=28)
        P.superficie_grade(2 * cfg.METADE_ARENA, 2 * cfg.METADE_ARENA, (0, 1, 0), (1, 0, 0), (0, 0, 1),
                           cfg.CELULA_PISO, 1.0 / cfg.METROS_POR_TEXTURA)
        T.sem_textura()

    def _paredes(self):
        T.usar(self.tex["parede"])
        material((0.92, 0.92, 0.96), especular=0.12, brilho=16)
        glEnable(GL_CULL_FACE)      # faces voltadas para trás não são desenhadas (as paredes só existem POR DENTRO)
        comp = 2 * META
        uv = (1 / 3.0, 1 / 3.0)
        defs = [   # centro, normal (para dentro da sala), eixo u
            ((0, H / 2, -META), (0, 0, 1), (1, 0, 0)),
            ((0, H / 2, META), (0, 0, -1), (1, 0, 0)),
            ((-META, H / 2, 0), (1, 0, 0), (0, 0, 1)),
            ((META, H / 2, 0), (-1, 0, 0), (0, 0, 1)),
        ]
        for centro, normal, eu in defs:
            glPushMatrix()
            glTranslatef(*centro)
            P.superficie_grade(comp, H, normal, eu, (0, 1, 0), 1.0, uv)
            glPopMatrix()
        glDisable(GL_CULL_FACE)
        T.sem_textura()
        # tampa (topo) das paredes: caixas finas de metal escuro
        material(cfg.CINZA_METAL, especular=0.3, brilho=30)
        for centro, dims in [((0, H + 0.1, -META - 0.5), (2 * cfg.METADE_ARENA, 0.2, 1.0)),
                             ((0, H + 0.1, META + 0.5), (2 * cfg.METADE_ARENA, 0.2, 1.0)),
                             ((-META - 0.5, H + 0.1, 0), (1.0, 0.2, 2 * cfg.METADE_ARENA)),
                             ((META + 0.5, H + 0.1, 0), (1.0, 0.2, 2 * cfg.METADE_ARENA))]:
            glPushMatrix()
            glTranslatef(*centro)
            P.caixa(*dims)
            glPopMatrix()

    def _marcacoes_piso(self):
        y = 0.025   # um pouquinho acima do piso para não "brigar" com ele (z-fighting)
        # faixas de alerta na frente do portal (quadriláteros alternando vermelho-escuro / cinza)
        px, pz = cfg.POSICAO_PORTAL
        for i in range(12):
            x0 = -3.6 + i * 0.6
            cor = cfg.VERMELHO_ESCURO if i % 2 == 0 else cfg.CINZA_METAL
            material(cor, especular=0.1, brilho=10)
            glBegin(GL_QUADS)
            glNormal3f(0, 1, 0)
            glVertex3f(x0, y, pz + 2.1)
            glVertex3f(x0 + 0.6, y, pz + 2.1)
            glVertex3f(x0 + 0.6, y, pz + 2.7)
            glVertex3f(x0, y, pz + 2.7)
            glEnd()
        # plataforma de partida do drone: quadrado + diagonais feitos de LINHAS
        sx, sz = cfg.POSICAO_INICIAL_DRONE
        pares = []
        cantos = [(sx - 2, sz - 2), (sx + 2, sz - 2), (sx + 2, sz + 2), (sx - 2, sz + 2)]
        for i in range(4):
            a, b = cantos[i], cantos[(i + 1) % 4]
            pares.append(((a[0], y, a[1]), (b[0], y, b[1])))
        pares += [((sx - 2, y, sz - 2), (sx + 2, y, sz + 2)), ((sx + 2, y, sz - 2), (sx - 2, y, sz + 2))]
        P.linhas(pares, cfg.VERMELHO_ESCURO, 3.0)
        # linhas-guia ao longo do piso
        guias = [((x, y, -15), (x, y, 14)) for x in (-9.5, 9.5)]
        P.linhas(guias, (0.26, 0.29, 0.36), 2.0)

    def _dutos_e_cabos(self):
        material(cfg.CINZA_METAL, especular=0.5, brilho=40)
        for altura in (0.55, 1.1):                                   # dutos horizontais ao longo das paredes
            for (x, z, rot) in [(0, -META + 0.35, 90), (0, META - 0.35, 90), (-META + 0.35, 0, 0), (META - 0.35, 0, 0)]:
                glPushMatrix()
                glTranslatef(x, altura, z)
                if rot == 90:
                    glRotatef(90, 0, 0, 1)                           # deita o cilindro ao longo de X
                    glTranslatef(0, -META, 0)
                else:
                    glRotatef(90, 1, 0, 0)                           # deita ao longo de Z
                    glTranslatef(0, -META, 0)
                P.prisma(0.17, 2 * META, 8, tampas=False)
                glPopMatrix()
        # cabos pendurados (LINHAS): pilares -> paredes, com "barriga" (catenária simples)
        pares = []
        for (x0, y0, z0, x1, y1, z1) in [(-6, 6.4, 3.5, -19, 5.2, 3.5), (6, 6.4, 3.5, 19, 5.2, 3.5),
                                         (-11, 5.9, -13, -11, 5.5, -19), (10, 6.4, -9, 19, 5.0, -9),
                                         (-4.5, 5.4, -17.6, -4.5, 5.2, -19), (4.5, 5.4, -17.6, 4.5, 5.2, -19)]:
            ant = (x0, y0, z0)
            for s in range(1, 13):
                t = s / 12.0
                p = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - 0.9 * math.sin(math.pi * t), z0 + (z1 - z0) * t)
                pares.append((ant, p))
                ant = p
        P.linhas(pares, (0.20, 0.22, 0.28), 2.0)

    def _obstaculo(self, o):
        tipo, x, z, mx, mz, alt = o
        glPushMatrix()
        glTranslatef(x, 0, z)                                         # TRANSLAÇÃO: posiciona no mundo
        if tipo in ("caixa", "container"):
            T.usar(self.tex["caixa"])
            material((0.95, 0.95, 1.0), especular=0.25, brilho=24)
            glPushMatrix()
            glTranslatef(0, alt / 2, 0)
            P.caixa(2 * mx, alt, 2 * mz, uv_por_metro=0.5)            # coordenadas de textura proporcionais ao tamanho
            glPopMatrix()
            T.sem_textura()
            material(cfg.CINZA_METAL, especular=0.4, brilho=30)       # tampa metálica levemente maior
            glPushMatrix()
            glTranslatef(0, alt + 0.06, 0)
            P.caixa(2 * mx + 0.12, 0.12, 2 * mz + 0.12)
            glPopMatrix()
        else:
            raio = mx
            material(cfg.CINZA_METAL, especular=0.5, brilho=40)
            glPushMatrix()
            glRotatef(22.5, 0, 1, 0)                                  # gira o octógono para a face ficar paralela aos eixos
            P.prisma(raio * (0.84 if tipo == "torre" else 1.0), alt, 8)
            glPopMatrix()
            material(cfg.CINZA_METAL, especular=0.3, brilho=20, cor_emissao=(0, 0, 0))
            glColor3f(0.2, 0.22, 0.28)
            glPushMatrix()
            glRotatef(22.5, 0, 1, 0)
            P.prisma(raio * 1.25, 0.35, 8)                            # base mais larga
            glPopMatrix()
        glPopMatrix()

    def _portico(self):
        """Viga do pórtico de manutenção entre os dois pilares do oeste (caixa ESCALADA)."""
        material(cfg.CINZA_METAL, especular=0.4, brilho=30)
        glPushMatrix()
        glTranslatef(-11.0, 5.55, -9.0)
        glScalef(0.5, 0.5, 8.0)                                       # ESCALA: cubo unitário vira viga
        P.cubo_unitario()
        glPopMatrix()

    # ---------------------------------------------------------------- chamado todo quadro
    def desenhar_estatico(self):
        glCallList(self.lista)

    def desenhar_estrelas(self, cam):
        glDisable(GL_LIGHTING)
        glDepthMask(GL_FALSE)
        glPushMatrix()
        glTranslatef(*cam)                                            # as estrelas acompanham a câmera (infinitamente longe)
        glPointSize(2.2)
        glBegin(GL_POINTS)                                            # PONTOS
        for x, y, z, b in self.estrelas:
            glColor3f(b * 0.85, b * 0.88, b)
            glVertex3f(x, y, z)
        glEnd()
        glPopMatrix()
        glDepthMask(GL_TRUE)
        glEnable(GL_LIGHTING)

    # ---------------------------------------------------------------- dinâmicos: painéis, lâmpadas, LEDs
    def desenhar_paineis(self, sis):
        T.usar(self.tex["painel"])
        for i, zona in enumerate(cfg.ZONAS_PAINEIS):
            brilho = 0.05 + 0.95 * sis.paineis[i]                     # emissão do painel
            for k in (-3.2, 0.0, 3.2):
                glPushMatrix()
                c = zona["centro"] + k
                w = zona["parede"]
                if w == "oeste":
                    glTranslatef(-META + 0.07, 3.0, c)
                elif w == "leste":
                    glTranslatef(META - 0.07, 3.0, c)
                    glRotatef(180, 0, 1, 0)
                elif w == "norte":
                    glTranslatef(c, 3.0, -META + 0.07)
                    glRotatef(-90, 0, 1, 0)
                else:
                    glTranslatef(c, 3.0, META - 0.07)
                    glRotatef(90, 0, 1, 0)
                # o painel é desenhado "de frente para +X" e a ROTAÇÃO acima o vira para dentro da sala
                material((0.95, 0.95, 1.0), especular=0.35, brilho=40, emissao=brilho, cor_emissao=(1, 1, 1))
                P.caixa(0.14, 1.8, 2.8)
                glPopMatrix()
        T.sem_textura()

    def desenhar_indicadores(self, sis):
        """LEDs vermelhos sobre as caixas e pilares: começam a acender já no 1/5."""
        e = 0.12 + 0.88 * sis.brilho_indicadores
        for (tipo, x, z, mx, mz, alt) in cfg.OBSTACULOS:
            material(cfg.VERMELHO, especular=0.3, brilho=30, emissao=e)
            glPushMatrix()
            glTranslatef(x, alt + (0.2 if tipo != "pilar" and tipo != "torre" else 0.05), z)
            if tipo in ("pilar", "torre"):
                glPushMatrix()
                glTranslatef(0, -0.35 if tipo == "pilar" else -1.0, 0)
                P.prisma(mx * 1.06, 0.18, 8, tampas=False)            # anel de LED em volta do pilar
                glPopMatrix()
            else:
                P.caixa(0.35, 0.16, 0.35)
            glPopMatrix()

    def desenhar_lampada_e_luminarias(self, sis, estado):
        # lâmpada da torre (acende/apaga com a tecla L, e fica mais forte com a restauração)
        lx, ly, lz = cfg.POSICAO_LUZ_PRINCIPAL
        b = sis.brilho_lampada
        glPushMatrix()
        glTranslatef(lx, ly - 0.55, lz)
        material((0.30, 0.33, 0.40), especular=0.5, brilho=40)
        P.prisma(1.55, 0.35, 8)                                       # cúpula da lâmpada
        glTranslatef(0, 0.55, 0)
        material((0.85, 0.92, 1.0), emissao=b, especular=0.0)
        glPushMatrix()
        glScalef(0.45, 0.45, 0.45)
        P.octaedro()                                                  # "bulbo" da lâmpada
        glPopMatrix()
        glPopMatrix()
        # luminárias de emergência (vermelhas) com refletor giratório
        e = sis.intensidade_emergencia
        for pos in cfg.POSICOES_LUZ_EMERGENCIA:
            glPushMatrix()
            glTranslatef(*pos)
            material((0.18, 0.2, 0.26), especular=0.4, brilho=30)
            P.caixa(0.5, 0.6, 0.5)
            glTranslatef(0, 0.45, 0)
            glRotatef(estado.tempo * 220.0, 0, 1, 0)                  # ROTAÇÃO contínua do giroflex
            material(cfg.VERMELHO, especular=0.6, brilho=60, emissao=0.35 + 0.65 * e)
            glPushMatrix()
            glScalef(0.34, 0.26, 0.34)
            P.octaedro()
            glPopMatrix()
            glPopMatrix()

    def desenhar_pedestais(self, estado):
        for n in estado.nucleos:
            glPushMatrix()
            glTranslatef(n.x, 0, n.z)
            material((0.28, 0.30, 0.38), especular=0.5, brilho=40)
            glPushMatrix()
            glRotatef(30, 0, 1, 0)
            P.prisma(0.75, 0.3, 6)
            glPopMatrix()
            ativo = n.estado == "ativo"
            material(cfg.VERMELHO, emissao=0.9 if ativo else 0.05)
            glTranslatef(0, 0.31, 0)
            glPushMatrix()
            glRotatef(30, 0, 1, 0)
            P.prisma(0.55, 0.05, 6)
            glPopMatrix()
            glPopMatrix()

    # ---------------------------------------------------------------- DRONE (objeto composto/hierárquico)
    def desenhar_drone(self, estado):
        d = estado.drone
        t = estado.tempo
        glPushMatrix()
        glTranslatef(d.x, d.y, d.z)               # 1) TRANSLAÇÃO: posição no mundo
        glRotatef(d.yaw, 0, 1, 0)                 # 2) ROTAÇÃO:    orientação (para onde o sensor aponta)
        glRotatef(-d.inclinacao, 1, 0, 0)         #    inclina o "nariz" ao acelerar
        glScalef(0.72, 0.72, 0.72)                # 3) ESCALA:     tamanho geral do drone
        # A partir daqui tudo é filho do drone: acompanha posição, giro e inclinação.

        # corpo central: esfera achatada (escala não uniforme), cinza escuro, MUITO especular
        material((0.52, 0.56, 0.66), especular=1.0, brilho=90)
        glPushMatrix()
        glScalef(0.85, 0.36, 0.85)
        P.esfera(1.0, 22, 14)
        glPopMatrix()
        # base inferior (caixa escalada) e faixa vermelha
        material((0.30, 0.32, 0.40), especular=0.4, brilho=30)
        glPushMatrix()
        glTranslatef(0, -0.26, 0)
        glScalef(0.9, 0.16, 0.9)
        P.cubo_unitario()
        glPopMatrix()
        brilho_led = 0.75 + 0.25 * math.sin(t * 6.0) + 1.0 * d.flash_colisao
        material(cfg.VERMELHO, emissao=min(1.6, brilho_led))
        glPushMatrix()
        glTranslatef(0, -0.36, 0)
        glScalef(0.7, 0.05, 0.7)
        P.cubo_unitario()
        glPopMatrix()
        # placa vermelho-escura no topo + antena
        material(cfg.VERMELHO_ESCURO, especular=0.6, brilho=50)
        glPushMatrix()
        glTranslatef(0, 0.3, 0.1)
        glScalef(0.7, 0.08, 0.55)
        P.cubo_unitario()
        glPopMatrix()
        material((0.2, 0.22, 0.28), especular=0.5, brilho=40)
        glPushMatrix()
        glTranslatef(0.35, 0.3, 0.45)
        P.prisma(0.035, 0.45, 6)
        glTranslatef(0, 0.45, 0)
        material(cfg.VERMELHO, emissao=0.7 + 0.3 * math.sin(t * 5.0))
        glScalef(0.08, 0.08, 0.08)
        P.octaedro()
        glPopMatrix()
        # sensor frontal (aponta para -Z local): caixa escura + lente vermelha luminosa
        material((0.10, 0.11, 0.14), especular=0.8, brilho=60)
        glPushMatrix()
        glTranslatef(0, 0.0, -0.82)
        glScalef(0.45, 0.2, 0.18)
        P.cubo_unitario()
        glPopMatrix()
        material(cfg.VERMELHO, especular=1.0, brilho=100, emissao=min(1.8, 0.9 + d.flash_colisao))
        glPushMatrix()
        glTranslatef(0, 0.0, -0.93)
        P.esfera(0.085, 10, 8)
        glPopMatrix()

        # 4 braços + motores + anéis + HÉLICES
        for k in range(4):
            glPushMatrix()
            glRotatef(45.0 + 90.0 * k, 0, 1, 0)   # referencial do braço k (aponta para fora)
            material((0.42, 0.45, 0.54), especular=0.5, brilho=40)
            glPushMatrix()
            glTranslatef(0.85, 0, 0)
            glScalef(1.2, 0.1, 0.17)              # ESCALA: braço fino e comprido
            P.cubo_unitario()
            glPopMatrix()
            glTranslatef(1.5, 0, 0)               # vai até a ponta do braço (hierarquia continua)
            # motor
            material((0.14, 0.15, 0.2), especular=0.8, brilho=60)
            glPushMatrix()
            glTranslatef(0, -0.02, 0)
            P.prisma(0.16, 0.22, 8)
            glPopMatrix()
            # anel protetor (toro deitado)
            material(cfg.CINZA_METAL, especular=0.7, brilho=60)
            glPushMatrix()
            glTranslatef(0, 0.1, 0)
            glRotatef(90, 1, 0, 0)
            P.toro(0.52, 0.03, 24, 6)
            glPopMatrix()
            # HÉLICE: gira em torno do PRÓPRIO centro (glRotatef do ângulo acumulado),
            # mas como está dentro do glPushMatrix do drone, continua seguindo posição e orientação dele.
            glPushMatrix()
            glTranslatef(0, 0.24, 0)
            sentido = 1 if k % 2 == 0 else -1
            glRotatef(sentido * d.angulo_helice, 0, 1, 0)
            for lamina in range(2):
                glPushMatrix()
                glRotatef(90 * lamina, 0, 1, 0)
                material((0.82, 0.85, 0.9), especular=0.6, brilho=50)
                glScalef(0.98, 0.022, 0.1)
                P.cubo_unitario()
                glPopMatrix()
            material(cfg.VERMELHO, emissao=0.9)                          # pontas vermelhas
            for sx in (-1, 1):
                glPushMatrix()
                glTranslatef(sx * 0.45, 0.012, 0)
                glScalef(0.1, 0.03, 0.11)
                P.cubo_unitario()
                glPopMatrix()
            glPopMatrix()
            glPopMatrix()
        glPopMatrix()

    # ---------------------------------------------------------------- NÚCLEOS DE ENERGIA
    def desenhar_nucleos(self, estado):
        for n in estado.nucleos:
            if not n.visivel:
                continue
            glPushMatrix()
            glTranslatef(n.x, n.y, n.z)            # TRANSLAÇÃO (n.y já inclui a flutuação senoidal)
            glRotatef(n.angulo, 0, 1, 0)           # ROTAÇÃO contínua
            glScalef(n.escala, n.escala, n.escala) # ESCALA animada: encolhe ao ser coletado
            # cristal externo: octaedro (8 triângulos) esticado em Y
            material(cfg.VERMELHO, especular=1.0, brilho=90, emissao=0.55)
            glPushMatrix()
            glScalef(0.4, 0.72, 0.4)
            P.octaedro()
            glPopMatrix()
            # miolo branco brilhante
            material(cfg.BRANCO, emissao=1.0)
            glPushMatrix()
            glRotatef(45, 0, 1, 0)
            glScalef(0.17, 0.32, 0.17)
            P.octaedro()
            glPopMatrix()
            # anéis orbitais feitos de LINHAS (GL_LINE_LOOP), girando em sentido contrário
            for inc, vel in ((70.0, -2.0), (-20.0, 1.4)):
                glPushMatrix()
                glRotatef(n.angulo * vel, 0, 1, 0)
                glRotatef(inc, 1, 0, 0)
                P.circulo_linhas(0.82, (1.0, 0.45, 0.5), 36, 2.0)
                glPopMatrix()
            glPopMatrix()

    # ---------------------------------------------------------------- PORTAL
    def desenhar_portal(self, estado):
        px, pz = cfg.POSICAO_PORTAL
        R = cfg.PORTAL_RAIO_ANEL
        ab = suave(estado.portal_abertura)
        pulso = 0.85 + 0.15 * math.sin(estado.tempo * 3.0)
        glPushMatrix()
        glTranslatef(px, cfg.PORTAL_ALTURA_CENTRO, pz)
        # anel externo: apagado (vermelho-escuro) -> aceso (vermelho vivo, quase branco)
        cor = tuple(a + (b - a) * ab for a, b in zip(cfg.VERMELHO_ESCURO, (1.0, 0.45, 0.5)))
        material(cor, especular=0.8, brilho=70, emissao=0.10 + 0.9 * ab * pulso)
        P.toro(R, 0.26, 40, 10)
        # aro interno com "dentes": gira em torno do centro do portal (rotação hierárquica)
        glRotatef(estado.portal_angulo, 0, 0, 1)
        material(cfg.CINZA_METAL, especular=0.7, brilho=60, emissao=0.0)
        for i in range(12):
            glPushMatrix()
            glRotatef(30 * i, 0, 0, 1)
            glTranslatef(R - 0.55, 0, 0)
            glScalef(0.4, 0.14, 0.18)
            P.cubo_unitario()
            glPopMatrix()
        glPopMatrix()
        # colunas laterais do portal (luminosas quando ativo)
        for sx in (-1, 1):
            glPushMatrix()
            glTranslatef(px + sx * (R + 0.55), 0, pz)
            material(cfg.CINZA_METAL, especular=0.5, brilho=40)
            P.prisma(0.28, 4.4, 6)
            material(cfg.VERMELHO, emissao=0.1 + 0.9 * ab)
            glTranslatef(0, 4.4, 0)
            glScalef(0.32, 0.32, 0.32)
            P.octaedro()
            glPopMatrix()

    # ---------------------------------------------------------------- TRANSLÚCIDOS (depois dos opacos)
    def desenhar_translucidos(self, estado, sis):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)                  # mistura ADITIVA: soma luz (efeito de brilho)
        glDepthMask(GL_FALSE)                              # translúcidos não escrevem profundidade
        # feixes e manchas de luz sob os núcleos ainda ativos
        for n in estado.nucleos:
            if n.estado != "ativo":
                continue
            glPushMatrix()
            glTranslatef(n.x, 0.04, n.z)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            P.disco(2.1, 28, 0.55, 0.0, cfg.VERMELHO, cfg.VERMELHO)       # mancha de luz no chão
            glPopMatrix()
            glBegin(GL_QUADS)                                              # coluna de luz (2 planos cruzados)
            for ang in (0, 90):
                c, s = math.cos(math.radians(ang)) * 0.42, math.sin(math.radians(ang)) * 0.42
                glColor4f(*cfg.VERMELHO, 0.42)
                glVertex3f(-c, 0.3, -s)
                glVertex3f(c, 0.3, s)
                glColor4f(*cfg.VERMELHO, 0.0)
                glVertex3f(c, 7.0, s)
                glVertex3f(-c, 7.0, -s)
            glEnd()
            glPopMatrix()
        # varredura dos giroflex de emergência (vermelho)
        e = sis.intensidade_emergencia
        for pos in cfg.POSICOES_LUZ_EMERGENCIA:
            for off in (0, 180):
                glPushMatrix()
                glTranslatef(pos[0], pos[1] + 0.45, pos[2])
                glRotatef(estado.tempo * 220.0 + off, 0, 1, 0)
                glBegin(GL_TRIANGLES)
                glColor4f(*cfg.VERMELHO, 0.30 * e)
                glVertex3f(0, 0, 0)
                glColor4f(*cfg.VERMELHO, 0.0)
                glVertex3f(7.0, -0.2, -1.6)
                glVertex3f(7.0, -0.2, 1.6)
                glEnd()
                glPopMatrix()
        # superfície do portal: barreira de linhas (fechado) -> disco luminoso (aberto)
        px, pz = cfg.POSICAO_PORTAL
        R = cfg.PORTAL_RAIO_ANEL
        ab = suave(estado.portal_abertura)
        glPushMatrix()
        glTranslatef(px, cfg.PORTAL_ALTURA_CENTRO, pz)
        if ab < 1.0:
            glLineWidth(3.0)
            glBegin(GL_LINES)                                              # grade de feixes que se recolhe
            y = -R + 0.4
            while y < R - 0.3:
                w = math.sqrt(max(0.0, (R - 0.3) ** 2 - y * y)) * (1.0 - ab)
                glColor4f(*cfg.VERMELHO, 0.85 * (1.0 - ab))
                glVertex3f(-w, y, 0)
                glVertex3f(w, y, 0)
                y += 0.38
            glEnd()
            glPushMatrix()
            P.disco(R - 0.28, 36, 0.20 * (1 - ab), 0.08 * (1 - ab), cfg.VERMELHO_ESCURO, cfg.VERMELHO_ESCURO)
            glPopMatrix()
        if ab > 0.0:
            raio = (R - 0.28) * ab                                         # "íris" que abre do centro para fora
            P.disco(raio, 40, 0.95, 0.5, (1.0, 0.85, 0.85), cfg.VERMELHO)
            glRotatef(estado.portal_angulo * 1.5, 0, 0, 1)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            for i in range(10):
                a = math.radians(36 * i)
                glColor4f(1, 1, 1, 0.8)
                glVertex3f(0, 0, 0.02)
                glColor4f(*cfg.VERMELHO, 0.0)
                glVertex3f(raio * math.cos(a), raio * math.sin(a), 0.02)
            glEnd()
        glPopMatrix()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
