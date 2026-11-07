# -*- coding: utf-8 -*-
"""
estado.py — LÓGICA do jogo (posições, colisões, coleta, animações por tempo).

Este arquivo NÃO usa OpenGL. Isso separa "o que acontece" de "como é desenhado",
facilita testar e explicar. Tudo que se move usa `dt` (segundos desde o último quadro):
    nova_posição = posição + velocidade * dt
Assim o jogo roda na mesma velocidade a 30, 60 ou 144 FPS.
"""
import math
from dataclasses import dataclass, field
import config as cfg


@dataclass
class Entrada:
    """Teclas que estão pressionadas neste quadro (preenchida em main.py)."""
    frente: bool = False
    tras: bool = False
    esquerda: bool = False
    direita: bool = False
    cam_esq: bool = False
    cam_dir: bool = False
    cam_cima: bool = False
    cam_baixo: bool = False


@dataclass
class Obstaculo:
    tipo: str
    x: float
    z: float
    mx: float      # meia largura em X
    mz: float      # meia largura em Z
    altura: float


@dataclass
class Nucleo:
    x: float
    z: float
    fase: float                 # defasagem para cada núcleo flutuar em momento diferente
    estado: str = "ativo"       # "ativo" -> "coletando" -> "coletado"
    t_coleta: float = 0.0       # tempo desde que foi coletado (anima o encolhimento)
    angulo: float = 0.0         # rotação contínua (graus)
    y: float = cfg.NUCLEO_ALTURA_BASE
    escala: float = 1.0

    @property
    def visivel(self):
        return self.estado != "coletado"


@dataclass
class Drone:
    x: float = 0.0
    z: float = 0.0
    y: float = cfg.ALTURA_VOO
    vx: float = 0.0
    vz: float = 0.0
    yaw: float = 0.0            # orientação (graus em torno de Y)
    inclinacao: float = 0.0     # "nariz para baixo" ao acelerar (graus)
    angulo_helice: float = 0.0  # ângulo acumulado das hélices (graus)
    flash_colisao: float = 0.0  # 1 quando bate; decai com dt (reação a colisão)


class EstadoJogo:
    def __init__(self):
        self.obstaculos = [Obstaculo(*o) for o in cfg.OBSTACULOS]
        self.reiniciar()
        self.fase = "menu"      # "menu" | "jogando" | "vitoria"

    # ------------------------------------------------------------------ reinício
    def reiniciar(self):
        """Restaura TUDO para o começo da missão (tecla R) sem fechar o programa."""
        px, pz = cfg.POSICAO_INICIAL_DRONE
        self.drone = Drone(x=px, z=pz, yaw=0.0)
        self.nucleos = [Nucleo(x, z, fase=i * 1.3) for i, (x, z) in enumerate(cfg.POSICOES_NUCLEOS)]
        self.coletados = 0
        self.portal_ativo = False
        self.portal_abertura = 0.0      # 0 = fechado, 1 = totalmente aberto (animação por evento)
        self.portal_angulo = 0.0
        self.tempo = 0.0
        self.tempo_vitoria = 0.0
        self.aviso = ""                 # mensagem temporária no HUD
        self.aviso_tempo = 0.0
        self.cam_yaw = 0.0              # graus; 0 = câmera ao sul olhando para o norte
        self.cam_elev = cfg.CAMERA_ELEVACAO_INICIAL
        self.cam_foco = [px, cfg.ALTURA_VOO, pz]
        self.fase = "jogando"
        self.evento_coleta = False      # True por 1 quadro quando coleta (usado nos testes/efeitos)

    # ------------------------------------------------------------------ utilidades
    def obstaculos_ativos(self):
        """Obstáculos + a barreira do portal enquanto ele está desativado."""
        lista = list(self.obstaculos)
        if not self.portal_ativo:
            px, pz = cfg.POSICAO_PORTAL
            lista.append(Obstaculo("barreira", px, pz, cfg.PORTAL_RAIO_ANEL, 0.4, 5.0))
        return lista

    @staticmethod
    def colide_circulo_caixa(cx, cz, raio, o):
        """Círculo (drone) contra caixa delimitadora: ponto mais próximo da caixa ao centro."""
        px = max(o.x - o.mx, min(cx, o.x + o.mx))
        pz = max(o.z - o.mz, min(cz, o.z + o.mz))
        return (cx - px) ** 2 + (cz - pz) ** 2 < raio * raio

    def colide_algum(self, x, z):
        lim = cfg.METADE_ARENA - cfg.ESPESSURA_PAREDE - cfg.RAIO_DRONE
        if abs(x) > lim or abs(z) > lim:      # limites do cenário
            return True
        return any(self.colide_circulo_caixa(x, z, cfg.RAIO_DRONE, o) for o in self.obstaculos_ativos())

    def mostrar_aviso(self, texto, duracao=2.2):
        self.aviso, self.aviso_tempo = texto, duracao

    # ------------------------------------------------------------------ atualização
    def atualizar(self, dt, entrada):
        """Chamada UMA vez por quadro com o dt real."""
        self.tempo += dt
        self.evento_coleta = False
        self._atualizar_camera(dt, entrada)
        if self.fase == "jogando":
            self._mover_drone(dt, entrada)
            self._coletar()
            self._verificar_portal()
        else:
            self._mover_drone(dt, Entrada())       # no menu/vitória o drone só paira
        self._animar_drone(dt)
        self._animar_nucleos(dt)
        self._animar_portal(dt)
        if self.fase == "vitoria":
            self.tempo_vitoria += dt
        self.aviso_tempo = max(0.0, self.aviso_tempo - dt)
        d = self.drone
        # foco da câmera acompanha o drone com atraso suave (independente de FPS)
        k = 1.0 - math.exp(-cfg.CAMERA_SUAVIDADE * dt)
        self.cam_foco[0] += (d.x - self.cam_foco[0]) * k
        self.cam_foco[1] += (d.y - self.cam_foco[1]) * k
        self.cam_foco[2] += (d.z - self.cam_foco[2]) * k

    def _atualizar_camera(self, dt, e):
        if e.cam_esq:
            self.cam_yaw -= cfg.CAMERA_VEL_ROTACAO * dt
        if e.cam_dir:
            self.cam_yaw += cfg.CAMERA_VEL_ROTACAO * dt
        if e.cam_cima:
            self.cam_elev += 40.0 * dt
        if e.cam_baixo:
            self.cam_elev -= 40.0 * dt
        self.cam_elev = max(cfg.CAMERA_ELEVACAO_MIN, min(cfg.CAMERA_ELEVACAO_MAX, self.cam_elev))
        self.cam_yaw %= 360.0

    def _mover_drone(self, dt, e):
        d = self.drone
        # direção desejada RELATIVA à câmera: W = "para longe da câmera"
        a = math.radians(self.cam_yaw)
        frente = (-math.sin(a), -math.cos(a))
        direita = (math.cos(a), -math.sin(a))
        f = (1 if e.frente else 0) - (1 if e.tras else 0)
        r = (1 if e.direita else 0) - (1 if e.esquerda else 0)
        dx = frente[0] * f + direita[0] * r
        dz = frente[1] * f + direita[1] * r
        n = math.hypot(dx, dz)
        if n > 0:                       # normaliza: andar na diagonal não pode ser mais rápido
            dx, dz = dx / n, dz / n
        alvo_vx, alvo_vz = dx * cfg.VELOCIDADE_DRONE, dz * cfg.VELOCIDADE_DRONE
        k = 1.0 - math.exp(-cfg.SUAVIDADE_ACELERACAO * dt)   # aceleração suave, independente do FPS
        d.vx += (alvo_vx - d.vx) * k
        d.vz += (alvo_vz - d.vz) * k

        # movimento e colisão separados por eixo => o drone "desliza" nas paredes e caixas
        novo_x = d.x + d.vx * dt
        if self.colide_algum(novo_x, d.z):
            if abs(d.vx) > 2.0:
                d.flash_colisao = 1.0
            d.vx = 0.0
        else:
            d.x = novo_x
        novo_z = d.z + d.vz * dt
        if self.colide_algum(d.x, novo_z):
            if abs(d.vz) > 2.0:
                d.flash_colisao = 1.0
            d.vz = 0.0
        else:
            d.z = novo_z

    def _animar_drone(self, dt):
        d = self.drone
        vel = math.hypot(d.vx, d.vz)
        frac = min(1.0, vel / cfg.VELOCIDADE_DRONE)
        # orientação: vira suavemente para o sentido do movimento (ângulo mais curto)
        if vel > 0.4:
            alvo = math.degrees(math.atan2(-d.vx, -d.vz))
            dif = (alvo - d.yaw + 180.0) % 360.0 - 180.0
            d.yaw += dif * (1.0 - math.exp(-9.0 * dt))
        d.inclinacao += (14.0 * frac - d.inclinacao) * (1.0 - math.exp(-8.0 * dt))
        vh = cfg.VELOCIDADE_HELICE_PARADO + (cfg.VELOCIDADE_HELICE_MOVENDO - cfg.VELOCIDADE_HELICE_PARADO) * frac
        d.angulo_helice = (d.angulo_helice + vh * dt) % 360.0     # rotação contínua
        d.y = cfg.ALTURA_VOO + 0.12 * math.sin(self.tempo * 2.4)  # oscilação periódica
        d.flash_colisao = max(0.0, d.flash_colisao - 3.0 * dt)

    def _animar_nucleos(self, dt):
        for n in self.nucleos:
            if n.estado == "coletado":
                continue
            giro = cfg.NUCLEO_VEL_GIRO * (4.0 if n.estado == "coletando" else 1.0)
            n.angulo = (n.angulo + giro * dt) % 360.0                       # rotação contínua
            n.y = cfg.NUCLEO_ALTURA_BASE + cfg.NUCLEO_AMPLITUDE_FLUTUACAO * math.sin(
                self.tempo * cfg.NUCLEO_VEL_FLUTUACAO + n.fase)             # movimento periódico
            if n.estado == "coletando":                                      # animação por evento
                n.t_coleta += dt
                p = min(1.0, n.t_coleta / cfg.NUCLEO_DURACAO_COLETA)
                n.escala = (1.0 - p) ** 2
                n.y += 1.2 * p                                               # sobe enquanto encolhe
                if p >= 1.0:
                    n.estado = "coletado"

    def _coletar(self):
        d = self.drone
        for n in self.nucleos:
            if n.estado != "ativo":      # um núcleo só pode ser coletado uma vez
                continue
            if math.hypot(d.x - n.x, d.z - n.z) < cfg.NUCLEO_RAIO_COLETA and abs(d.y - n.y) < 1.6:
                n.estado = "coletando"
                self.coletados += 1
                self.evento_coleta = True
                if self.coletados >= len(self.nucleos):
                    self.portal_ativo = True
                    self.mostrar_aviso("ENERGIA PRINCIPAL RESTAURADA — PORTAL ATIVO", 4.0)
                else:
                    self.mostrar_aviso(f"NÚCLEO COLETADO  {self.coletados}/{len(self.nucleos)}")

    def _animar_portal(self, dt):
        self.portal_angulo = (self.portal_angulo + (40.0 + 140.0 * self.portal_abertura) * dt) % 360.0
        if self.portal_ativo and self.portal_abertura < 1.0:
            self.portal_abertura = min(1.0, self.portal_abertura + dt / cfg.PORTAL_DURACAO_ABERTURA)

    def _verificar_portal(self):
        if not self.portal_ativo or self.portal_abertura < 0.6:
            return
        px, pz = cfg.POSICAO_PORTAL
        if math.hypot(self.drone.x - px, self.drone.z - pz) < cfg.PORTAL_RAIO_ENTRADA:
            self.fase = "vitoria"
            self.tempo_vitoria = 0.0
