# Roteiro de apresentação — 5 minutos
**PROTOCOLO VERMILHÃO — OPERAÇÃO ÚLTIMA ENERGIA**

> Dica: ensaie uma vez com o cronômetro. A missão completa leva ~30 s se você já souber o caminho (rota abaixo).
> Deixe o jogo aberto na tela inicial e o VS Code/editor com os arquivos abertos nas abas indicadas.

## Rota rápida para pegar os 5 núcleos
1. Núcleo do **oeste, perto do início** (à esquerda, atrás das caixas).
2. Vá ao **centro-norte**: o núcleo está dentro do "U" de caixas (entre pela abertura, pela frente).
3. Núcleo do **nordeste** (canto direito, ao fundo), passando entre a caixa e o pilar.
4. Núcleo do **leste** (lado direito, no meio).
5. Núcleo do **noroeste**, atrás do pórtico de manutenção (dois pilares com uma viga).
6. Portal no fundo, entre os dois pilares.

---

## 0:00 – 0:30 · Abertura (tela inicial)
**Mostrar:** o menu com a estação girando ao fundo.
**Falar:** "Nosso jogo se chama Protocolo Vermilhão. A estação perdeu a energia e o jogador pilota um drone de manutenção para recuperar cinco núcleos e reativar o portal. A ideia que a gente quis explorar foi usar a **iluminação como história**: a estação começa no escuro, com luz de emergência vermelha, e vai acendendo a cada núcleo."
**Ação:** pressionar ENTER.

## 0:30 – 1:30 · Cena, câmera e colisão
**Mostrar:** voar um pouco (W A S D), girar a câmera com as setas, bater de leve numa caixa e passar atrás de uma caixa (oclusão).
**Falar:** "É 3D de verdade: tem perspectiva, profundidade e a câmera acompanha o drone. Quando o drone passa atrás da caixa, ela esconde ele — isso é o **teste de profundidade**, o `GL_DEPTH_TEST`. Os objetos são desenhados em coordenadas locais, a gente posiciona no mundo com translação, rotação e escala, a câmera é o `gluLookAt` e a projeção em perspectiva é o `gluPerspective`. A colisão é simples: o drone é um círculo e os obstáculos são caixas; se for entrar, ele desliza na lateral."
**Se perguntarem:** `cena.py` → `aplicar_camera`; `estado.py` → `colide_circulo_caixa` e `_mover_drone`.

## 1:30 – 2:45 · ILUMINAÇÃO (o ponto principal)
**Mostrar (ainda no 0/5):**
1. Apertar **L** (desliga) e apertar **L** de novo (liga). Mostrar a diferença.
2. Coletar o 1º núcleo e mostrar a barra "ESTAÇÃO" subindo e os painéis acendendo; coletar mais um ou dois.
3. Apertar **L** de novo já com a estação mais restaurada, para provar que funciona em qualquer etapa.

**Falar:** "A iluminação é a da própria OpenGL, não é pintar de outra cor. Cada superfície tem **normal** — a direção para onde ela aponta — e a luz calcula o brilho pela relação entre a normal, a posição da luz e o material. Tem a parte **ambiente**, que deixa as áreas escuras ainda visíveis; a **difusa**, que ilumina mais as faces viradas para a luz; e a **especular**, que é aquele brilho do corpo do drone e que muda quando ele gira. A tecla L liga e desliga só a luz principal da torre, e por isso, mesmo apagada, a gente ainda vê a emergência vermelha. Além dela, tem duas luzes de emergência, uma luz no portal e quatro luzes de painéis que vão acendendo a cada núcleo: a OpenGL clássica permite 8 luzes, e a gente usou as 8. A transição é suave porque usa o `dt`."
**Se perguntarem:** `iluminacao.py` → `SistemaIluminacao.atualizar` e `fontes()`; `cena.py` → `aplicar_iluminacao`. Mudar a posição da luz: `POSICAO_LUZ_PRINCIPAL` em `config.py`.

## 2:45 – 3:30 · Transformações e transformação hierárquica
**Mostrar:** aproximar a câmera do drone (seta para baixo) e acompanhar as hélices girando enquanto ele anda e vira; núcleos girando e flutuando.
**Falar:** "A translação posiciona tudo; a rotação gira as hélices e os núcleos; a escala monta as peças — o drone é um cubo unitário esticado para virar braço, base, sensor — e faz o núcleo encolher quando é coletado. A **hierárquica** é a hélice: ela é filha do braço, que é filho do drone. Com `glPushMatrix` e `glPopMatrix` aninhados, a hélice gira no próprio centro, mas continua indo para onde o drone vai e girando junto com ele."
**Mostrar no código se pedirem:** `objetos.py` → `desenhar_drone` (o laço `for k in range(4)`).

## 3:30 – 4:10 · Texturas e primitivas
**Mostrar:** o piso de longe.
**Falar:** "São quatro texturas feitas por código com NumPy e OpenCV, então não dependem de imagem baixada. O piso é uma textura pequena que **repete** dez vezes em cada direção — é o `GL_REPEAT` com coordenadas de textura maiores que 1. Nas caixas, a repetição é proporcional ao tamanho para a imagem não esticar. Usamos quadriláteros, triângulos, leques e faixas, linhas e pontos."
**Código:** `gerar_texturas.py`; `texturas.py`; `primitivas.py` → `superficie_grade` e `caixa`.

## 4:10 – 4:40 · `dt` e animações
**Falar:** "Tudo que se move é multiplicado pelo `dt`, o tempo desde o último quadro: velocidade vezes `dt`. Assim o jogo anda igual a 30 ou a 144 quadros por segundo. Testamos isso simulando o mesmo tempo com `dt` diferentes. As animações são: rotação contínua, flutuação periódica e as por evento: o núcleo que encolhe, o portal que abre e o LED que pisca na colisão."
**Código:** `main.py` (`dt = relogio.tick(...)`), `estado.py` → `_animar_nucleos`.

## 4:40 – 5:00 · Final
**Mostrar:** entrar no portal ativado → "MISSÃO CONCLUÍDA" → apertar **R** para reiniciar.
**Falar:** "Quando chega em 5 de 5 o portal muda de aparência e abre; ao entrar, aparece a missão concluída. E o R reinicia tudo sem fechar o programa. Obrigada!"

---

## Perguntas possíveis (respostas curtas)
| Pergunta | Resposta para memorizar |
|---|---|
| O que é `glPushMatrix`/`glPopMatrix`? | Salva e restaura a matriz atual, para as transformações de um objeto não afetarem o próximo. |
| Por que a ordem translate → rotate importa? | A última transformação escrita é aplicada primeiro ao vértice. Translada depois de rotacionar → gira no próprio centro; o contrário → orbita a origem. |
| O que é normal? | Vetor perpendicular à superfície; a luz usa ele para saber o quanto a face está virada para ela. |
| Diferença entre difusa e especular? | Difusa depende só da luz e da superfície; especular também depende de onde o observador está (por isso o brilho do drone se move). |
| Por que o piso é uma grade de quadradinhos? | A luz clássica é calculada nos vértices. Um quadrado só teria 4 pontos; com a grade as poças de luz aparecem. |
| Por que `GL_NORMALIZE`? | Quando uso `glScalef`, as normais mudam de tamanho; o `GL_NORMALIZE` corrige para a luz não ficar errada. |
| Como a hélice gira no próprio centro e segue o drone? | Ela está dentro do `glPushMatrix` do drone. A matriz do drone vem primeiro e o giro da hélice é a última, mais interna. |
| Como funciona o teste de profundidade? | Para cada pixel a GPU guarda o ponto mais próximo da câmera (buffer de profundidade); o que está atrás é descartado. |
| Como funciona a colisão? | Círculo (drone) contra caixa (AABB) no plano XZ. Testo X e Z separados, então ele desliza na lateral. |
| Por que usar `dt`? | Para a velocidade não depender do FPS: posição += velocidade × `dt`. |
| `KEYDOWN` ou `get_pressed()`? | `KEYDOWN` dispara uma vez (L, R, ESC, ENTER); `get_pressed()` é lido a todo quadro (W A S D, setas). |
| Por que display list? | O cenário fixo é gravado uma vez e redesenhado com 1 chamada. A iluminação continua sendo calculada a cada quadro. |
| A luz do painel é luz de verdade? | Sim, são `GL_LIGHT4` a `7`. Os painéis também têm emissão só como acabamento. |
| Como ficou suave a transição da luz? | O nível se aproxima do alvo com `k = 1 - e^(-taxa·dt)`; dá o mesmo resultado em qualquer FPS. |
| Qual a limitação? | Luz por vértice (sem sombras), máximo de 8 luzes, colisão 2D e altura constante do drone. |

## Pequenas mudanças que o professor pode pedir (tudo em `config.py`)
| Pedido | O que mudar |
|---|---|
| Mudar a posição da luz | `POSICAO_LUZ_PRINCIPAL` |
| Drone mais rápido | `VELOCIDADE_DRONE` |
| Hélices mais rápidas | `VELOCIDADE_HELICE_MOVENDO` |
| Núcleos mais altos / flutuando mais | `NUCLEO_ALTURA_BASE`, `NUCLEO_AMPLITUDE_FLUTUACAO` |
| Portal abrindo mais devagar | `PORTAL_DURACAO_ABERTURA` |
| Transição de luz mais lenta | `VELOCIDADE_TRANSICAO_LUZ` |
| Câmera mais perto | `CAMERA_DISTANCIA` |
| Mais/menos núcleos | lista `POSICOES_NUCLEOS` (o HUD e o portal se ajustam; as tabelas de luz foram feitas para 5) |
