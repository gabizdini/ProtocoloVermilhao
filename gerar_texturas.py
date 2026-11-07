# -*- coding: utf-8 -*-
"""
gerar_texturas.py — cria as texturas do jogo POR CÓDIGO (NumPy + OpenCV).

Origem das imagens: todas são geradas proceduralmente por este script (autoria própria).
Nenhuma imagem externa/baixada é usada, então não há problema de direitos autorais.

Uso:   python gerar_texturas.py      -> grava os PNGs em assets/texturas/
(O jogo também chama estas funções automaticamente se algum PNG estiver faltando.)

Todas as texturas são 256x256 e "ladrilháveis" (as bordas se encaixam), para poderem repetir.
"""
import os
import numpy as np
import cv2

TAM = 256
PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "texturas")


def _ruido(rng, escala=1.0, suavizar=0):
    """Ruído gaussiano; 'suavizar' borra (com borda circular, para continuar ladrilhável)."""
    r = rng.normal(0, escala, (TAM, TAM)).astype(np.float32)
    if suavizar:
        k = suavizar * 2 + 1
        p = np.pad(r, suavizar * 2, mode="wrap")
        r = cv2.GaussianBlur(p, (k, k), 0)[suavizar * 2:-suavizar * 2, suavizar * 2:-suavizar * 2]
    return r


def _riscos_horizontais(rng):
    """Efeito de metal escovado: ruído borrado só na horizontal."""
    r = rng.normal(0, 1, (TAM, TAM)).astype(np.float32)
    p = np.pad(r, ((0, 0), (20, 20)), mode="wrap")
    p = cv2.blur(p, (41, 1))
    return p[:, 20:-20] * 4.0


def _para_uint8(img):
    return np.clip(img, 0, 255).astype(np.uint8)


def textura_piso():
    """Piso metálico: 2x2 placas com emendas, rebites e riscos de metal escovado."""
    rng = np.random.default_rng(1)
    base = np.zeros((TAM, TAM, 3), np.float32)
    base[:] = (104, 112, 130)                                  # RGB cinza-azulado metálico
    ruido = _riscos_horizontais(rng) * 3.0 + _ruido(rng, 3.0, 1)
    base += ruido[..., None]
    # placas ligeiramente diferentes de tom
    for (i, j), tom in {(0, 0): 0, (0, 1): -7, (1, 0): -4, (1, 1): 4}.items():
        base[i * 128:(i + 1) * 128, j * 128:(j + 1) * 128] += tom
    img = _para_uint8(base)
    for k in (0, 128):                                      # emendas escuras + brilho do chanfro
        cv2.line(img, (0, k), (TAM, k), (28, 32, 40), 4)
        cv2.line(img, (k, 0), (k, TAM), (28, 32, 40), 4)
        cv2.line(img, (0, k + 3), (TAM, k + 3), (112, 120, 136), 1)
        cv2.line(img, (k + 3, 0), (k + 3, TAM), (112, 120, 136), 1)
    for cx in (14, 114, 142, 242):                          # rebites
        for cy in (14, 114, 142, 242):
            cv2.circle(img, (cx, cy), 4, (38, 42, 52), -1)
            cv2.circle(img, (cx - 1, cy - 1), 2, (120, 128, 144), -1)
    cv2.rectangle(img, (190, 60), (214, 66), (139, 30, 45), -1)   # pequena marca vermelho-escura
    return img


def textura_parede():
    """Parede de painéis tecnológicos: placas, fendas de ventilação e faixa de alerta."""
    rng = np.random.default_rng(2)
    base = np.zeros((TAM, TAM, 3), np.float32)
    base[:] = (62, 68, 84)
    base += (_ruido(rng, 2.5, 1))[..., None]
    img = _para_uint8(base)
    for x in (0, 128):                                      # duas placas lado a lado
        cv2.rectangle(img, (x + 3, 3), (x + 124, 252), (86, 94, 112), 2)
        cv2.rectangle(img, (x + 8, 8), (x + 119, 247), (48, 54, 68), 1)
    for y in range(24, 80, 8):                              # fendas de ventilação
        cv2.line(img, (20, y), (108, y), (24, 28, 36), 3)
    cv2.rectangle(img, (150, 40), (232, 110), (34, 38, 50), -1)       # janelinha de painel
    cv2.rectangle(img, (150, 40), (232, 110), (110, 118, 136), 1)
    cv2.circle(img, (166, 56), 5, (230, 57, 70), -1)                 # LED vermelho
    cv2.line(img, (180, 56), (222, 56), (150, 158, 172), 1)
    cv2.line(img, (160, 80), (222, 80), (150, 158, 172), 1)
    # faixa de alerta diagonal (vermelho escuro / cinza) na parte de baixo
    faixa = np.zeros((40, TAM, 3), np.uint8)
    for i in range(-40, TAM + 40, 24):
        cv2.line(faixa, (i, 0), (i + 40, 40), (139, 30, 45), 11)
    faixa[faixa.sum(axis=2) == 0] = (40, 44, 56)
    img[200:240] = faixa
    return img


def textura_caixa():
    """Caixa de manutenção: moldura chanfrada, travessas em X, faixa vermelha e identificação."""
    rng = np.random.default_rng(3)
    base = np.zeros((TAM, TAM, 3), np.float32)
    base[:] = (84, 92, 108)
    base += (_ruido(rng, 3.0, 1) + _riscos_horizontais(rng) * 1.5)[..., None]
    img = _para_uint8(base)
    cv2.rectangle(img, (0, 0), (TAM - 1, TAM - 1), (30, 34, 44), 10)             # moldura
    cv2.rectangle(img, (10, 10), (TAM - 11, TAM - 11), (122, 130, 148), 2)
    cv2.line(img, (14, 14), (TAM - 15, TAM - 15), (56, 62, 78), 6)               # travessas em X
    cv2.line(img, (TAM - 15, 14), (14, TAM - 15), (56, 62, 78), 6)
    cv2.rectangle(img, (0, 104), (TAM, 150), (200, 45, 58), -1)                  # faixa vermelha
    cv2.rectangle(img, (0, 104), (TAM, 150), (139, 30, 45), 3)
    cv2.putText(img, "VRM-07", (62, 138), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (240, 244, 250), 2, cv2.LINE_AA)
    for cx in (26, 230):
        for cy in (26, 230):
            cv2.circle(img, (cx, cy), 5, (34, 38, 48), -1)
            cv2.circle(img, (cx - 1, cy - 1), 2, (150, 158, 174), -1)
    return img


def textura_painel_energia():
    """Painel de energia: circuitos, barras e LEDs. (Brilha mais conforme a estação é restaurada.)"""
    rng = np.random.default_rng(4)
    img = np.zeros((TAM, TAM, 3), np.uint8)
    img[:] = (26, 30, 42)
    img = _para_uint8(img.astype(np.float32) + _ruido(rng, 2.0, 1)[..., None])
    cv2.rectangle(img, (4, 4), (TAM - 5, TAM - 5), (120, 128, 146), 3)
    for y in range(28, 230, 24):                              # trilhas de circuito em ângulo reto
        x0 = int(rng.integers(16, 100))
        x1 = int(rng.integers(120, 236))
        cv2.line(img, (x0, y), (x1, y), (170, 178, 194), 2)
        cv2.line(img, (x1, y), (x1, y + 12), (170, 178, 194), 2)
        cv2.circle(img, (x0, y), 4, (216, 222, 233), -1)
    for i, h in enumerate((70, 110, 50, 130, 90)):            # gráfico de barras
        x = 24 + i * 22
        cv2.rectangle(img, (x, 236 - h), (x + 14, 236), (230, 57, 70), -1)
    for i in range(6):                                        # LEDs
        cor = (230, 57, 70) if i % 2 == 0 else (240, 244, 250)
        cv2.rectangle(img, (150 + (i % 3) * 28, 150 + (i // 3) * 28), (166 + (i % 3) * 28, 166 + (i // 3) * 28), cor, -1)
    return img


TEXTURAS = {
    "piso_metalico.png": textura_piso,
    "parede_painel.png": textura_parede,
    "caixa_manutencao.png": textura_caixa,
    "painel_energia.png": textura_painel_energia,
}


def gerar_todas(pasta=PASTA):
    os.makedirs(pasta, exist_ok=True)
    for nome, funcao in TEXTURAS.items():
        rgb = funcao()
        cv2.imwrite(os.path.join(pasta, nome), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))   # OpenCV grava em BGR
        print("gerada:", nome, rgb.shape)


if __name__ == "__main__":
    gerar_todas()
