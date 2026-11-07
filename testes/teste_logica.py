# -*- coding: utf-8 -*-
"""
Testes automáticos da LÓGICA (não precisam de janela nem de OpenGL).
Executar:  python testes/teste_logica.py
"""
import os, sys, math, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import config as cfg
from estado import EstadoJogo, Entrada
from iluminacao import SistemaIluminacao
import autopiloto as ap


def novo():
    e = EstadoJogo(); e.reiniciar(); s = SistemaIluminacao()
    return e, s


class TesteCenario(unittest.TestCase):
    def test_requisitos_minimos(self):
        e, _ = novo()
        self.assertGreaterEqual(len(e.nucleos), 5)
        self.assertGreaterEqual(len(e.obstaculos), 3)

    def test_nucleos_nao_estao_dentro_de_obstaculos(self):
        e, _ = novo()
        for n in e.nucleos:
            for o in e.obstaculos:
                self.assertFalse(e.colide_circulo_caixa(n.x, n.z, cfg.RAIO_DRONE + 0.5, o), (n.x, n.z, o))

    def test_spawn_livre(self):
        e, _ = novo()
        self.assertFalse(e.colide_algum(e.drone.x, e.drone.z))


class TesteMovimento(unittest.TestCase):
    def test_limites_do_cenario(self):
        e, _ = novo()
        for _ in range(60 * 10):
            e.atualizar(1 / 60, Entrada(direita=True))
        lim = cfg.METADE_ARENA - cfg.ESPESSURA_PAREDE
        self.assertLessEqual(abs(e.drone.x), lim)
        for _ in range(60 * 10):
            e.atualizar(1 / 60, Entrada(frente=True))
        self.assertLessEqual(abs(e.drone.z), lim)

    def test_colisao_com_cada_obstaculo(self):
        """Empurra o drone contra cada obstáculo vindo de uma direção livre e confere que não entra."""
        for o in cfg.OBSTACULOS:
            e, _ = novo()
            tipo, ox, oz, mx, mz, alt = o
            # posiciona o drone ao sul do obstáculo, alinhado em x, e anda para o norte (W)
            e.drone.x, e.drone.z = ox, oz + mz + cfg.RAIO_DRONE + 3.0
            if e.colide_algum(e.drone.x, e.drone.z):
                continue            # ponto de partida ocupado por outro objeto: ignora este caso
            ant = e.drone.z
            for _ in range(60 * 3):
                e.atualizar(1 / 60, Entrada(frente=True))
                for ob in e.obstaculos_ativos():
                    self.assertFalse(e.colide_circulo_caixa(e.drone.x, e.drone.z, cfg.RAIO_DRONE - 0.01, ob),
                                     f"drone entrou em {ob}")

    def test_diagonal_nao_e_mais_rapida(self):
        a, _ = novo(); b, _ = novo()
        a.drone.x = b.drone.x = 0.0
        a.drone.z = b.drone.z = 12.5
        for _ in range(30):
            a.atualizar(1 / 60, Entrada(esquerda=True))
            b.atualizar(1 / 60, Entrada(esquerda=True, frente=True))
        va = math.hypot(a.drone.vx, a.drone.vz); vb = math.hypot(b.drone.vx, b.drone.vz)
        self.assertAlmostEqual(va, vb, delta=0.05)

    def test_independencia_de_fps(self):
        """Mesmo tempo simulado com dt diferentes => mesma posição (dentro de pequena tolerância)."""
        res = []
        for dt in (1 / 30, 1 / 60, 1 / 144):
            e, _ = novo()
            for _ in range(round(1.5 / dt)):
                e.atualizar(dt, Entrada(frente=True))
            res.append(e.drone.z)
        self.assertLess(max(res) - min(res), 0.35, res)


class TesteMissao(unittest.TestCase):
    def test_missao_completa_pelo_piloto_automatico(self):
        e, s = novo()
        marcos = []
        def cb(est, sis, t):
            if est.evento_coleta:
                marcos.append((est.coletados, round(t, 1)))
        t = ap.voar(e, s, ao_quadro=cb)
        self.assertEqual([m[0] for m in marcos], [1, 2, 3, 4, 5], marcos)
        self.assertEqual(e.fase, "vitoria")
        self.assertTrue(e.portal_ativo)
        print(f"\n   missão completa em {t:.1f}s simulados; coletas: {marcos}")

    def test_coleta_uma_unica_vez(self):
        e, _ = novo()
        n = e.nucleos[0]
        e.drone.x, e.drone.z = n.x, n.z
        for _ in range(120):
            e.atualizar(1 / 60, Entrada())
        self.assertEqual(e.coletados, 1)
        self.assertEqual(n.estado, "coletado")

    def test_animacao_de_coleta_encolhe(self):
        e, _ = novo()
        n = e.nucleos[0]
        e.drone.x, e.drone.z = n.x, n.z
        e.atualizar(1 / 60, Entrada())
        escalas = []
        for _ in range(40):
            e.atualizar(1 / 60, Entrada())
            escalas.append(n.escala)
        self.assertLess(escalas[10], 1.0)
        self.assertTrue(all(a >= b for a, b in zip(escalas, escalas[1:])))

    def test_portal_comeca_desativado_e_bloqueia(self):
        e, _ = novo()
        self.assertFalse(e.portal_ativo)
        px, pz = cfg.POSICAO_PORTAL
        e.drone.x, e.drone.z = 0.0, pz + 5
        for _ in range(60 * 4):
            e.atualizar(1 / 60, Entrada(frente=True))
        self.assertNotEqual(e.fase, "vitoria")
        self.assertGreater(e.drone.z, pz + 0.4)

    def test_nucleos_flutuam_e_giram(self):
        e, _ = novo()
        ys, angs = [], []
        for _ in range(120):
            e.atualizar(1 / 60, Entrada())
            ys.append(e.nucleos[1].y); angs.append(e.nucleos[1].angulo)
        self.assertGreater(max(ys) - min(ys), 0.3)
        self.assertGreater(len(set(round(a) for a in angs)), 50)

    def test_helices_giram(self):
        e, _ = novo()
        a0 = e.drone.angulo_helice
        e.atualizar(0.05, Entrada())
        self.assertNotEqual(a0, e.drone.angulo_helice)

    def test_reinicio_restaura_tudo(self):
        e, s = novo()
        ap.voar(e, s)
        self.assertEqual(e.fase, "vitoria")
        e.reiniciar(); s.reiniciar()
        self.assertEqual(e.fase, "jogando")
        self.assertEqual(e.coletados, 0)
        self.assertFalse(e.portal_ativo)
        self.assertEqual(e.portal_abertura, 0.0)
        self.assertTrue(all(n.estado == "ativo" and n.escala == 1.0 for n in e.nucleos))
        self.assertEqual((e.drone.x, e.drone.z), cfg.POSICAO_INICIAL_DRONE)
        self.assertEqual((s.nivel, s.coletados), (0.0, 0))


class TesteIluminacao(unittest.TestCase):
    def simula(self, s, seg, coletados, dt=1 / 60, portal=0.0):
        for _ in range(round(seg / dt)):
            s.atualizar(dt, coletados, portal)

    def test_progressao_monotonica_e_suave(self):
        s = SistemaIluminacao()
        niveis, prin, emer = [], [], []
        for c in range(6):
            self.simula(s, 4.0, c)
            niveis.append(s.nivel); prin.append(s.intensidade_principal); emer.append(s.intensidade_emergencia)
        self.assertEqual(niveis[0], 0.0)
        self.assertTrue(all(a < b for a, b in zip(niveis, niveis[1:])), niveis)
        self.assertTrue(all(a < b for a, b in zip(prin, prin[1:])), prin)
        self.assertAlmostEqual(niveis[5], 1.0, delta=0.02)
        print(f"\n   nível por coleta: {[round(n,2) for n in niveis]}\n   luz principal: {[round(p,2) for p in prin]}")

    def test_transicao_suave_sem_saltos(self):
        s = SistemaIluminacao()
        self.simula(s, 2, 0)
        antes = s.nivel
        maior = 0.0
        for _ in range(180):
            ant = s.nivel
            s.atualizar(1 / 60, 3, 0.0)
            maior = max(maior, abs(s.nivel - ant))
        self.assertLess(maior, 0.02)           # nunca "pula" de um quadro para outro

    def test_transicao_independe_do_fps(self):
        a, b = SistemaIluminacao(), SistemaIluminacao()
        self.simula(a, 1.0, 3, dt=1 / 30); self.simula(b, 1.0, 3, dt=1 / 120)
        self.assertAlmostEqual(a.nivel, b.nivel, delta=0.005)

    def test_L_independe_da_progressao(self):
        for c in range(6):
            s = SistemaIluminacao()
            self.simula(s, 5, c)
            self.assertGreater(s.fontes()[0].difusa[0], 0.2)
            s.alternar_luz_principal(); self.simula(s, 1, c)
            self.assertFalse(s.fontes()[0].ligada)       # desligada em qualquer progresso
            self.assertEqual(s.fontes()[0].difusa, (0.0, 0.0, 0.0))
            s.alternar_luz_principal(); self.simula(s, 1, c)
            self.assertTrue(s.fontes()[0].ligada)

    def test_paineis_acendem_por_etapas(self):
        s = SistemaIluminacao()
        self.simula(s, 5, 1); p1 = list(s.paineis)
        self.assertGreater(p1[0], 0.4); self.assertLess(p1[1], 0.05)
        self.simula(s, 5, 2); self.assertGreater(s.paineis[1], 0.4); self.assertLess(s.paineis[2], 0.05)
        self.simula(s, 5, 5); self.assertTrue(all(p > 0.95 for p in s.paineis))

    def test_estado_inicial_tem_emergencia_vermelha(self):
        s = SistemaIluminacao()
        self.simula(s, 1, 0)
        f = s.fontes()
        self.assertTrue(f[1].ligada and f[2].ligada)
        self.assertGreater(f[1].difusa[0], 4 * f[1].difusa[2])     # dominante vermelha
        self.assertFalse(any(x.ligada for x in f[4:]))              # painéis ainda apagados
        self.simula(s, 5, 5)
        self.assertLess(s.intensidade_emergencia, 0.4)

    def test_portal_ilumina_quando_abre(self):
        s = SistemaIluminacao()
        self.simula(s, 1, 5, portal=0.0); c = s.fontes()[3].difusa
        self.simula(s, 1, 5, portal=1.0); o = s.fontes()[3].difusa
        self.assertGreater(sum(o), 3 * sum(c))


if __name__ == "__main__":
    unittest.main(verbosity=2)
