# -*- coding: utf-8 -*-
"""Monta as figuras comparativas do relatório a partir das capturas reais em capturas/."""
import os, cv2, numpy as np
C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "capturas")

def r(n):
    return cv2.resize(cv2.imread(os.path.join(C, n)), (640, 360))

def rot(im, txt):
    im = im.copy(); cv2.rectangle(im, (0, 326), (640, 360), (29, 20, 16), -1)
    cv2.putText(im, txt, (10, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (233, 222, 216), 1, cv2.LINE_AA)
    return im

prog = [("02_jogo_0de5_luz_ligada.png", "0/5  emergencia vermelha"), ("04_coleta_1de5.png", "1/5  paineis comecam a acender"),
        ("04_coleta_2de5.png", "2/5"), ("04_coleta_3de5.png", "3/5  iluminacao sobe"),
        ("04_coleta_4de5.png", "4/5"), ("04_coleta_5de5.png", "5/5  energia restaurada")]
ims = [rot(r(n), t) for n, t in prog]
cv2.imwrite(os.path.join(C, "progressao_iluminacao.png"), np.vstack([np.hstack(ims[:3]), np.hstack(ims[3:])]))
pares = [rot(r("02_jogo_0de5_luz_ligada.png"), "0/5  L ligada"), rot(r("03_jogo_0de5_luz_desligada.png"), "0/5  L desligada"),
         rot(r("09_5de5_centro_luz_ligada.png"), "5/5  L ligada"), rot(r("09_5de5_centro_luz_desligada.png"), "5/5  L desligada")]
cv2.imwrite(os.path.join(C, "comparacao_luz_L.png"), np.vstack([np.hstack(pares[:2]), np.hstack(pares[2:])]))
dr = [rot(r("08_drone_closeup_yaw0.png"), "drone: camera yaw 0"), rot(r("08_drone_closeup_yaw50.png"), "drone: camera yaw 50 (brilho especular se move)")]
cv2.imwrite(os.path.join(C, "drone_especular.png"), np.hstack(dr))
print("figuras montadas")
extra = [rot(r("01_menu.png"), "tela inicial"), rot(r("07_oclusao_drone_atras_da_caixa.png"), "oclusao: caixa esconde o drone"), rot(r("06_vitoria.png"), "missao concluida")]
cv2.imwrite(os.path.join(C, "telas_extras.png"), np.hstack(extra))
